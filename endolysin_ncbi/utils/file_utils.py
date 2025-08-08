"""
文件操作工具模块
包含文件创建、保存、统计等功能
"""

from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Union

PathLike = Union[str, Path]


def create_output_directory(output_dir: PathLike) -> Path:
    """创建输出目录并返回路径"""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path


def create_database_directory(output_dir: PathLike, database: str) -> str:
    """为特定数据库创建子目录并返回字符串路径（向后兼容）"""
    database_dir = Path(output_dir) / database
    database_dir.mkdir(parents=True, exist_ok=True)
    return str(database_dir)


def save_record_file(
    filepath: PathLike,
    record_content: str,
    database: str,
    record_id: str,
    rettype: str,
    retmode: str,
) -> int:
    """保存单个记录到文件并返回文件大小（字节）"""
    file_path = Path(filepath)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(f"# 数据库: {database}\n")
        f.write(f"# 记录ID: {record_id}\n")
        f.write(f"# 下载时间: {datetime.now()}\n")
        f.write(f"# 格式: {rettype} ({retmode})\n")
        f.write("# " + "=" * 50 + "\n\n")
        f.write(record_content)
        if not record_content.endswith('\n'):
            f.write('\n')
    return file_path.stat().st_size


def save_error_file(
    database_dir: PathLike,
    batch_num: int,
    error_msg: str,
    database: str,
    start: int,
    end: int,
) -> None:
    """保存错误信息到文件"""
    error_file = Path(database_dir) / f"error_batch_{batch_num}.txt"
    with open(error_file, 'w', encoding='utf-8') as f:
        f.write(f"# 错误信息\n")
        f.write(f"# 数据库: {database}\n")
        f.write(f"# 批次: {batch_num}\n")
        f.write(f"# 记录范围: {start+1}-{end}\n")
        f.write(f"# 时间: {datetime.now()}\n")
        f.write("# " + "=" * 50 + "\n\n")
        f.write(error_msg)


def generate_safe_filename(filename: str) -> str:
    """生成安全的文件名，移除非法字符"""
    return "".join(c for c in filename if c.isalnum() or c in '._-')


def save_download_list_preview(
    output_dir: PathLike, download_lists: List[Dict[str, Any]]
) -> Path:
    """保存下载列表预览文件并返回路径"""
    list_file = Path(output_dir) / "download_lists_preview.txt"

    with open(list_file, 'w', encoding='utf-8') as f:
        f.write("Endolysin 数据库下载列表预览\n")
        f.write(f"生成时间: {datetime.now()}\n")
        f.write("=" * 80 + "\n\n")

        total_records = 0
        total_available = 0

        for download_info in download_lists:
            database = download_info['database']
            total_count = download_info['total_count']
            available_ids = download_info['available_ids']
            sample_records = download_info['sample_records']
            format_info = download_info['format_info']

            total_records += total_count
            total_available += available_ids

            f.write(f"数据库: {database.upper()}\n")
            f.write(f"总记录数: {total_count:,}\n")
            f.write(f"可获取ID数: {available_ids:,}\n")
            f.write(f"下载格式: {format_info[0]} ({format_info[1]})\n")
            f.write(f"样本记录数: {len(sample_records)}\n")

            if 'error' in download_info:
                f.write(f"错误: {download_info['error']}\n")

            # 保存样本记录
            if sample_records:
                f.write("样本记录:\n")
                for j, record in enumerate(sample_records[:3], 1):
                    f.write(f"  {j}. ID: {record['id']}\n")
                    f.write(f"     标题: {record['title']}\n")
                    f.write(f"     作者: {record['authors']}\n")
                    f.write(f"     日期: {record['date']}\n")

            f.write("-" * 60 + "\n\n")

        f.write(f"总计:\n")
        f.write(f"有数据的数据库: {len(download_lists)} 个\n")
        f.write(f"总记录数: {total_records:,}\n")
        f.write(f"总可获取数: {total_available:,}\n")

    return list_file


def save_search_summary(
    output_dir: PathLike, search_summary: List[tuple], max_records: int
) -> Path:
    """保存搜索摘要文件并返回路径"""
    summary_file = Path(output_dir) / "search_summary.txt"

    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"Endolysin 搜索结果摘要\n")
        f.write(f"搜索时间: {datetime.now()}\n")
        f.write(f"配置: 每个数据库最多下载 {max_records} 条记录\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"{'数据库':20s} {'找到记录数':>12s} {'下载记录数':>12s} {'下载比例':>10s}\n")
        f.write("-" * 60 + "\n")

        total_found = 0
        total_downloaded = 0

        for database, found_count, downloaded_count in search_summary:
            percentage = (downloaded_count / found_count * 100) if found_count > 0 else 0
            f.write(
                f"{database:20s}: {found_count:>10,} / {downloaded_count:>10,} ({percentage:>6.1f}%)\n"
            )
            total_found += found_count
            total_downloaded += downloaded_count

        f.write("-" * 60 + "\n")
        f.write(
            f"{'总计':20s}: {total_found:>10,} / {total_downloaded:>10,} ({(total_downloaded/total_found*100):>6.1f}%)\n"
        )
        f.write(f"\n有数据的数据库数量: {len(search_summary)} 个\n")

    return summary_file
