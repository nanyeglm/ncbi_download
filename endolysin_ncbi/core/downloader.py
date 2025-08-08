"""
下载核心模块
负责数据的下载、保存和统计
"""

from pathlib import Path
import time
from datetime import datetime
from typing import List, Dict, Any
from endolysin_ncbi.core.database_manager import DatabaseManager
from endolysin_ncbi.config.settings import (
    BATCH_SIZE,
    DOWNLOAD_DELAY,
    MAX_RECORDS_PER_DATABASE,
    get_download_format,
    get_file_extension,
)
from endolysin_ncbi.utils.file_utils import (
    create_database_directory,
    save_record_file,
    save_error_file,
    generate_safe_filename,
)
from endolysin_ncbi.utils.format_utils import (
    parse_genbank_records,
    parse_xml_records,
    parse_text_records,
    extract_record_id,
    format_file_size,
)


class DataDownloader:
    """数据下载器"""
    
    def __init__(self, output_dir: Path):
        """初始化下载器"""
        self.output_dir: Path = Path(output_dir)
        self.db_manager = DatabaseManager()
    
    def download_database_data(self, database: str, count: int, webenv: str, 
                              query_key: str, batch_size: int = None) -> int:
        """下载指定数据库的完整元数据，每条记录保存为单独文件"""
        if count == 0:
            return 0
        
        # 使用全局配置或默认值
        if batch_size is None:
            batch_size = BATCH_SIZE
        
        rettype, retmode = get_download_format(database)
        file_extension = get_file_extension(rettype, retmode)
        
        # 创建数据库子文件夹
        database_dir = create_database_directory(self.output_dir, database)
        
        print(f"正在下载 {database} 数据库的 {count} 条完整元数据记录...")
        print(f"  格式: {rettype} ({retmode})")
        print(f"  保存目录: {database_dir}")
        
        # 分批下载，使用全局配置的下载限制
        actual_download_count = min(count, MAX_RECORDS_PER_DATABASE)
        print(f"  计划下载: {actual_download_count} 条记录 (总共 {count} 条可用)")
        
        downloaded_records: List[Dict[str, Any]] = []  # 用于统计
        total_file_size = 0
        record_counter = 0
        
        for start in range(0, actual_download_count, batch_size):
            end = min(start + batch_size, actual_download_count)
            print(f"  下载第 {start + 1} - {end} 条记录 (完整元数据)")
            
            try:
                # 获取数据
                current_batch_size = end - start
                data = self.db_manager.fetch_records(
                    database, rettype, retmode, start, current_batch_size, webenv, query_key
                )
                
                # 解析数据为单个记录
                records = self._parse_records(data, database, rettype, retmode)
                
                # 保存每个记录为单独文件
                for record in records:
                    if record.strip():  # 确保记录不为空
                        record_counter += 1
                        record_id = extract_record_id(record, database, rettype, record_counter)
                        
                        filename = f"{record_id}.{file_extension}"
                        safe_filename = generate_safe_filename(filename)
                        safe_filepath = Path(database_dir) / safe_filename
                        
                        # 保存文件
                        file_size = save_record_file(
                            safe_filepath, record, database, record_id, rettype, retmode
                        )
                        
                        # 统计信息
                        total_file_size += file_size
                        downloaded_records.append({
                            'filename': safe_filename,
                            'record_id': record_id,
                            'file_size': file_size,
                            'batch': start//batch_size + 1
                        })
                
                time.sleep(DOWNLOAD_DELAY)  # 使用全局配置的延迟时间
                
            except Exception as e:
                error_msg = str(e)
                print(f"  {error_msg}")
                
                # 记录错误信息
                save_error_file(
                    database_dir,
                    start // batch_size + 1,
                    error_msg,
                    database,
                    start,
                    end,
                )
                continue
        
        # 生成数据库统计信息文件
        self._generate_database_statistics(
            database, database_dir, downloaded_records, total_file_size,
            count, actual_download_count, rettype, retmode
        )
        
        print(f"  {database} 数据库下载完成:")
        print(f"    - 总共下载: {len(downloaded_records)} 个文件")
        print(f"    - 总大小: {format_file_size(total_file_size)}")
        print(f"    - 保存目录: {database_dir}")
        
        # 返回实际下载的记录数
        return len(downloaded_records)
    
    def _parse_records(self, data: str, database: str, rettype: str, retmode: str) -> List[str]:
        """根据格式解析记录"""
        if rettype == 'gb':
            return parse_genbank_records(data)
        elif retmode == 'xml':
            return parse_xml_records(data, database)
        else:
            return parse_text_records(data, database)
    
    def _generate_database_statistics(self, database: str, database_dir: str,
                                    downloaded_records: List[Dict[str, Any]],
                                    total_file_size: int, total_count: int,
                                    downloaded_count: int, rettype: str, retmode: str) -> None:
        """为每个数据库生成详细的统计信息文件"""
        stats_file = Path(database_dir) / f"{database}_statistics.txt"
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            f.write(f"# {database.upper()} 数据库统计信息\n")
            f.write("=" * 60 + "\n\n")
            
            # 基本信息
            f.write("## 基本信息\n")
            f.write(f"数据库名称: {database}\n")
            f.write(f"搜索关键词: endolysin\n")
            f.write(f"下载时间: {datetime.now()}\n")
            f.write(f"数据格式: {rettype} ({retmode})\n")
            f.write(f"保存目录: {database_dir}\n\n")
            
            # 数量统计
            f.write("## 数量统计\n")
            f.write(f"总找到记录数: {total_count:,}\n")
            f.write(f"实际下载记录数: {downloaded_count:,}\n")
            f.write(f"成功保存文件数: {len(downloaded_records):,}\n")
            f.write(f"下载完成率: {(len(downloaded_records)/downloaded_count*100):.1f}%\n")
            f.write(f"总覆盖率: {(len(downloaded_records)/total_count*100):.1f}%\n\n")
            
            # 文件大小统计
            f.write("## 文件大小统计\n")
            f.write(f"总文件大小: {format_file_size(total_file_size)}\n")
            
            if downloaded_records:
                file_sizes = [record['file_size'] for record in downloaded_records]
                avg_size = total_file_size / len(downloaded_records)
                max_size = max(file_sizes)
                min_size = min(file_sizes)
                
                f.write(f"平均文件大小: {format_file_size(avg_size)}\n")
                f.write(f"最大文件大小: {format_file_size(max_size)}\n")
                f.write(f"最小文件大小: {format_file_size(min_size)}\n\n")
            
            # 批次统计
            if downloaded_records:
                batch_stats = {}
                for record in downloaded_records:
                    batch = record['batch']
                    if batch not in batch_stats:
                        batch_stats[batch] = []
                    batch_stats[batch].append(record)
                
                f.write("## 批次下载统计\n")
                f.write(f"总批次数: {len(batch_stats)}\n")
                for batch_num in sorted(batch_stats.keys()):
                    batch_records = batch_stats[batch_num]
                    batch_size = sum(record['file_size'] for record in batch_records)
                    f.write(f"批次 {batch_num}: {len(batch_records)} 个文件, {format_file_size(batch_size)}\n")
                f.write("\n")
            
            # 文件列表
            f.write("## 下载文件列表\n")
            f.write(f"{'序号':<6} {'文件名':<50} {'记录ID':<20} {'大小':<10} {'批次':<6}\n")
            f.write("-" * 92 + "\n")
            
            for i, record in enumerate(downloaded_records, 1):
                filename = record['filename'][:47] + "..." if len(record['filename']) > 50 else record['filename']
                record_id = record['record_id'][:17] + "..." if len(record['record_id']) > 20 else record['record_id']
                f.write(f"{i:<6} {filename:<50} {record_id:<20} {format_file_size(record['file_size']):<10} {record['batch']:<6}\n")
            
            f.write("\n# 统计信息生成完成\n")
        
        print(f"    - 统计信息已保存: {stats_file}")
