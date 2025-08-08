#!/usr/bin/env python3
"""
Endolysin NCBI数据库下载器主程序
模块化的endolysin相关数据下载工具

使用方法:
    python main.py [选项]

选项:
    --preview-only      只获取预览信息，不下载完整数据
    --category CATEGORY 只处理指定类别的数据库 (sequence, literature, gene, project, variation, chemical, structure)
    --database DATABASE 只处理指定的数据库
    --output-dir DIR    指定输出目录 (默认: endolysin_data)
    --help             显示帮助信息
"""

import argparse
import sys
import time
from datetime import datetime
from typing import List, Dict, Any

from pathlib import Path
from endolysin_ncbi.config.settings import OUTPUT_DIR
from endolysin_ncbi.core.database_manager import DatabaseManager
from endolysin_ncbi.utils.file_utils import (
    create_output_directory,
    save_download_list_preview,
    save_search_summary,
)
from endolysin_ncbi.databases.sequence_databases import SequenceDatabaseDownloader
from endolysin_ncbi.databases.literature_databases import LiteratureDatabaseDownloader
from endolysin_ncbi.databases.gene_databases import GeneDatabaseDownloader
from endolysin_ncbi.databases.other_databases import (
    ProjectSampleDatabaseDownloader, VariationDatabaseDownloader,
    ChemicalDatabaseDownloader, StructureTaxonomyDatabaseDownloader
)


class EndolysinDownloadManager:
    """Endolysin数据下载管理器"""
    
    def __init__(self, output_dir: str = str(OUTPUT_DIR)):
        """初始化下载管理器"""
        self.output_dir = str(output_dir)
        self.db_manager = DatabaseManager()
        
        # 初始化各类下载器
        self.downloaders = {
            'sequence': SequenceDatabaseDownloader(output_dir),
            'literature': LiteratureDatabaseDownloader(output_dir),
            'gene': GeneDatabaseDownloader(output_dir),
            'project': ProjectSampleDatabaseDownloader(output_dir),
            'variation': VariationDatabaseDownloader(output_dir),
            'chemical': ChemicalDatabaseDownloader(output_dir),
            'structure': StructureTaxonomyDatabaseDownloader(output_dir),
        }
        
        # 创建输出目录
        create_output_directory(self.output_dir)
    
    def get_available_databases(self) -> List[str]:
        """获取所有可用的NCBI数据库"""
        return self.db_manager.get_available_databases()
    
    def process_single_database(self, database: str, download_full_data: bool = False) -> Dict[str, Any]:
        """处理单个数据库"""
        # 找到支持该数据库的下载器
        for category, downloader in self.downloaders.items():
            if downloader.is_supported(database):
                print(f"使用 {downloader.get_database_category()} 下载器处理 {database}")
                return downloader.process_database(database, download_full_data)
        
        # 如果没有找到支持的下载器
        return {
            'database': database,
            'supported': False,
            'error': f"没有找到支持数据库 {database} 的下载器"
        }
    
    def process_category(self, category: str, download_full_data: bool = False) -> Dict[str, Any]:
        """处理指定类别的所有数据库"""
        if category not in self.downloaders:
            raise ValueError(f"不支持的数据库类别: {category}")
        
        available_databases = self.get_available_databases()
        if not available_databases:
            return {'error': '无法获取NCBI数据库列表'}
        
        downloader = self.downloaders[category]
        results = downloader.process_all_supported_databases(available_databases, download_full_data)
        return downloader.get_summary(results)
    
    def process_all_databases(self, download_full_data: bool = False) -> Dict[str, Any]:
        """处理所有数据库"""
        print("开始获取NCBI数据库列表...")
        available_databases = self.get_available_databases()
        
        if not available_databases:
            print("无法获取数据库列表")
            return {'error': '无法获取NCBI数据库列表'}
        
        print(f"找到 {len(available_databases)} 个 NCBI 数据库")
        print(f"数据库列表: {', '.join(available_databases)}")
        print("=" * 60)
        
        # 存储所有结果
        all_results = {}
        all_download_lists = []
        all_search_summary = []
        
        # 按类别处理数据库
        for category, downloader in self.downloaders.items():
            print(f"\n{'='*20} {downloader.get_database_category()} {'='*20}")
            
            results = downloader.process_all_supported_databases(available_databases, download_full_data)
            summary = downloader.get_summary(results)
            all_results[category] = summary
            
            # 收集下载列表信息
            for result in results:
                if 'preview_info' in result:
                    all_download_lists.append(result['preview_info'])
                
                # 收集搜索摘要
                if result.get('found_records', 0) > 0:
                    all_search_summary.append((
                        result['database'],
                        result['found_records'],
                        result.get('downloaded_records', 0)
                    ))
            
            time.sleep(0.5)  # 避免请求过于频繁
        
        # 保存汇总信息
        self._save_summary_files(all_download_lists, all_search_summary)
        
        # 显示总体统计
        self._display_final_summary(all_results)
        
        return all_results
    
    def _save_summary_files(self, download_lists: List[Dict[str, Any]], 
                           search_summary: List[tuple]) -> None:
        """保存汇总文件"""
        if download_lists:
            list_file = save_download_list_preview(self.output_dir, download_lists)
            print(f"\n详细下载列表已保存到: {list_file}")
        
        if search_summary:
            from config.settings import MAX_RECORDS_PER_DATABASE
            summary_file = save_search_summary(self.output_dir, search_summary, MAX_RECORDS_PER_DATABASE)
            print(f"搜索摘要已保存到: {summary_file}")
    
    def _display_final_summary(self, all_results: Dict[str, Any]) -> None:
        """显示最终汇总统计"""
        print("\n" + "="*60)
        print("最终汇总统计:")
        print("="*60)
        
        total_found = 0
        total_downloaded = 0
        total_databases = 0
        
        for category, summary in all_results.items():
            if 'error' not in summary:
                found = summary.get('total_found_records', 0)
                downloaded = summary.get('total_downloaded_records', 0)
                db_count = summary.get('successful_databases', 0)
                
                total_found += found
                total_downloaded += downloaded
                total_databases += db_count
                
                print(f"{summary.get('category', category):20s}: {found:>8,} / {downloaded:>8,} 条记录 ({db_count} 个数据库)")
        
        print("-" * 60)
        print(f"{'总计':20s}: {total_found:>8,} / {total_downloaded:>8,} 条记录 ({total_databases} 个数据库)")
        
        if total_found > 0:
            print(f"\n总下载率: {(total_downloaded/total_found*100):.1f}%")
        
        print(f"\n所有数据已保存到目录: {self.output_dir}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Endolysin NCBI数据库下载器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    
    parser.add_argument('--preview-only', action='store_true',
                       help='只获取预览信息，不下载完整数据')
    parser.add_argument('--category', choices=['sequence', 'literature', 'gene', 'project', 'variation', 'chemical', 'structure'],
                       help='只处理指定类别的数据库')
    parser.add_argument('--database', help='只处理指定的数据库')
    parser.add_argument('--output-dir', default=str(OUTPUT_DIR),
                       help=f'指定输出目录 (默认: {OUTPUT_DIR})')
    parser.add_argument('--retry-batches', nargs='*', type=int,
                       help='仅重试指定批次号（例如: --retry-batches 789 790 861）')
    
    args = parser.parse_args()
    
    # 初始化下载管理器
    manager = EndolysinDownloadManager(args.output_dir)
    
    print(f"Endolysin NCBI数据库下载器")
    print(f"开始时间: {datetime.now()}")
    print(f"输出目录: {args.output_dir}")
    print(f"模式: {'仅预览' if args.preview_only else '完整下载'}")
    print("=" * 60)
    
    try:
        if args.retry_batches is not None:
            # 仅重试指定批次（需要指定数据库）
            if not args.database:
                raise ValueError('使用 --retry-batches 时，必须同时指定 --database')
            dm = DatabaseManager()
            count, webenv, query_key = dm.search_database(args.database)
            if count > 0 and webenv and query_key:
                # 通过对应类别下载器来调用 retry
                # 选择器：从各 downloader 中找支持该数据库的实例
                for downloader in manager.downloaders.values():
                    if downloader.is_supported(args.database):
                        repaired = downloader.data_downloader.retry_failed_batches(
                            args.database, webenv, query_key, args.retry_batches
                        )
                        print(f"已补回 {repaired} 个记录文件。")
                        break
            else:
                print('无法获取有效的会话信息（webenv/query_key），重试终止。')

        elif args.database:
            # 处理单个数据库
            print(f"处理单个数据库: {args.database}")
            result = manager.process_single_database(args.database, not args.preview_only)
            print(f"处理结果: {result}")
            
        elif args.category:
            # 处理指定类别
            print(f"处理数据库类别: {args.category}")
            result = manager.process_category(args.category, not args.preview_only)
            print(f"类别处理完成: {result.get('category', args.category)}")
            
        else:
            # 处理所有数据库
            if not args.preview_only:
                # 询问用户是否继续下载
                print("即将开始完整数据下载。")
                print("输入 'y' 或 'yes' 继续，其他任意键仅获取预览信息")
                user_input = input("请选择: ").strip().lower()
                download_full = user_input in ['y', 'yes']
            else:
                download_full = False
            
            result = manager.process_all_databases(download_full)
            
    except KeyboardInterrupt:
        print("\n\n用户中断程序执行")
        sys.exit(1)
    except Exception as e:
        print(f"\n程序执行出错: {e}")
        sys.exit(1)
    
    print(f"\n程序执行完成: {datetime.now()}")


if __name__ == "__main__":
    main()
