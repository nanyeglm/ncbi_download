"""
数据库管理核心模块
负责NCBI数据库的连接、搜索和基本操作
"""

from Bio import Entrez
import time
import random
from typing import List, Tuple, Dict, Any, Callable
from endolysin_ncbi.config.settings import (
    NCBI_EMAIL,
    NCBI_TOOL,
    NCBI_API_KEY,
    SEARCH_TERM,
    MAX_RETRIES,
    RETRY_BACKOFF_BASE,
    RETRY_JITTER_MAX,
)


class DatabaseManager:
    """NCBI数据库管理器"""
    
    def __init__(self):
        """初始化数据库管理器"""
        Entrez.email = NCBI_EMAIL
        Entrez.tool = NCBI_TOOL
        if NCBI_API_KEY:
            Entrez.api_key = NCBI_API_KEY

    def _with_retries(self, func: Callable, *args, **kwargs):
        """带重试与指数退避的调用包装。对 429/5xx 等错误重试，加入抖动。"""
        attempt = 0
        while True:
            try:
                return func(*args, **kwargs)
            except Exception as exc:  # 网络/限流/服务端错误
                attempt += 1
                if attempt > MAX_RETRIES:
                    raise
                sleep_seconds = (RETRY_BACKOFF_BASE ** (attempt - 1))
                # 抖动，避免雪崩与同步重试
                sleep_seconds += random.uniform(0, RETRY_JITTER_MAX)
                time.sleep(sleep_seconds)
    
    def get_available_databases(self) -> List[str]:
        """获取 NCBI 所有可用数据库列表"""
        try:
            info_handle = self._with_retries(Entrez.einfo)
            info_results = Entrez.read(info_handle)
            info_handle.close()
            return info_results["DbList"]
        except Exception as e:
            print(f"获取数据库列表时出错: {e}")
            return []
    
    def search_database(self, database: str, search_term: str = SEARCH_TERM) -> Tuple[int, str, str]:
        """在指定数据库中搜索关键词"""
        try:
            search_handle = self._with_retries(
                Entrez.esearch,
                db=database,
                term=search_term,
                usehistory="y",
                retmax=0
            )
            search_results = Entrez.read(search_handle)
            search_handle.close()
            
            count = int(search_results["Count"])
            webenv = search_results.get("WebEnv", "")
            query_key = search_results.get("QueryKey", "")
            
            return count, webenv, query_key
        except Exception as e:
            print(f"在数据库 {database} 中搜索时出错: {e}")
            return 0, "", ""
    
    def get_record_ids(self, database: str, search_term: str = SEARCH_TERM, 
                      max_records: int = 10000) -> List[str]:
        """获取记录ID列表"""
        try:
            search_handle = self._with_retries(
                Entrez.esearch,
                db=database,
                term=search_term,
                usehistory="y",
                retmax=min(max_records, 10000)  # NCBI限制
            )
            search_results = Entrez.read(search_handle)
            search_handle.close()
            
            return search_results.get("IdList", [])
        except Exception as e:
            print(f"获取 {database} 数据库记录ID时出错: {e}")
            return []
    
    def get_record_summaries(self, database: str, id_list: List[str]) -> List[Dict[str, Any]]:
        """获取记录摘要信息"""
        if not id_list:
            return []
        
        try:
            summary_handle = self._with_retries(
                Entrez.esummary,
                db=database,
                id=','.join(id_list)
            )
            summaries = Entrez.read(summary_handle)
            summary_handle.close()
            
            # 处理摘要信息
            sample_records = []
            for i, summary in enumerate(summaries):
                if isinstance(summary, dict):
                    record_info = {
                        'id': summary.get('Id', id_list[i] if i < len(id_list) else 'unknown'),
                        'title': summary.get('Title', summary.get('Caption', 'No title')),
                        'authors': summary.get('AuthorList', summary.get('Authors', 'No authors')),
                        'date': summary.get('PubDate', summary.get('CreateDate', 'No date')),
                        'database': database
                    }
                    sample_records.append(record_info)
            
            return sample_records
            
        except Exception as e:
            print(f"获取 {database} 数据库摘要信息时出错: {e}")
            # 如果获取摘要失败，至少返回ID信息
            return [{
                'id': record_id,
                'title': 'Title not available',
                'authors': 'Authors not available',
                'date': 'Date not available',
                'database': database
            } for record_id in id_list]
    
    def fetch_records(self, database: str, rettype: str, retmode: str,
                     start: int, batch_size: int, webenv: str, query_key: str) -> str:
        """从NCBI获取记录数据"""
        try:
            fetch_handle = self._with_retries(
                Entrez.efetch,
                db=database,
                rettype=rettype,
                retmode=retmode,
                retstart=start,
                retmax=batch_size,
                webenv=webenv,
                query_key=query_key
            )
            
            data = fetch_handle.read()
            if isinstance(data, bytes):
                data = data.decode('utf-8', errors='ignore')
            
            fetch_handle.close()
            return data
            
        except Exception as e:
            raise Exception(f"获取记录 {start+1}-{start+batch_size} 时出错: {e}")
    
    def get_download_list_info(self, database: str, count: int, webenv: str, 
                              query_key: str, sample_size: int = 10) -> Dict[str, Any]:
        """获取指定数据库的下载列表信息，只获取基本信息而不下载完整内容"""
        from ..config.settings import get_download_format, MAX_RECORDS_PER_DATABASE
        
        if count == 0:
            return {
                'database': database,
                'total_count': 0,
                'available_ids': 0,
                'sample_records': [],
                'format_info': get_download_format(database)
            }
        
        print(f"正在获取 {database} 数据库的记录列表信息...")
        print(f"  总记录数: {count}")
        print(f"  获取样本数: {min(sample_size, count)}")
        
        try:
            # 获取记录ID列表
            id_list = self.get_record_ids(database, max_records=min(count, MAX_RECORDS_PER_DATABASE))
            print(f"  获取到 {len(id_list)} 个记录ID")
            
            # 获取样本记录的摘要信息
            sample_ids = id_list[:sample_size] if id_list else []
            sample_records = self.get_record_summaries(database, sample_ids)
            
            return {
                'database': database,
                'total_count': count,
                'available_ids': len(id_list),
                'sample_records': sample_records,
                'format_info': get_download_format(database)
            }
            
        except Exception as e:
            print(f"  获取 {database} 数据库列表时出错: {e}")
            return {
                'database': database,
                'total_count': count,
                'available_ids': 0,
                'sample_records': [],
                'format_info': get_download_format(database),
                'error': str(e)
            }
