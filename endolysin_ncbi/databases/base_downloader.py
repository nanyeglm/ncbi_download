"""
基础下载器类
定义所有数据库下载器的通用接口和基础功能
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple
from endolysin_ncbi.core.database_manager import DatabaseManager
from endolysin_ncbi.core.downloader import DataDownloader
from endolysin_ncbi.config.settings import SAMPLE_SIZE


class BaseDownloader(ABC):
    """基础下载器抽象类"""
    
    def __init__(self, output_dir: str):
        """初始化基础下载器"""
        self.output_dir = output_dir
        self.db_manager = DatabaseManager()
        self.data_downloader = DataDownloader(output_dir)
    
    @abstractmethod
    def get_supported_databases(self) -> List[str]:
        """获取支持的数据库列表"""
        pass
    
    @abstractmethod
    def get_database_category(self) -> str:
        """获取数据库类别名称"""
        pass
    
    def is_supported(self, database: str) -> bool:
        """检查是否支持指定数据库"""
        return database.lower() in [db.lower() for db in self.get_supported_databases()]
    
    def search_database(self, database: str) -> Tuple[int, str, str]:
        """搜索数据库中的endolysin相关记录"""
        if not self.is_supported(database):
            raise ValueError(f"数据库 {database} 不被此下载器支持")
        
        return self.db_manager.search_database(database)
    
    def get_download_preview(self, database: str, count: int, webenv: str, 
                           query_key: str, sample_size: int = SAMPLE_SIZE) -> Dict[str, Any]:
        """获取下载预览信息"""
        if not self.is_supported(database):
            raise ValueError(f"数据库 {database} 不被此下载器支持")
        
        return self.db_manager.get_download_list_info(
            database, count, webenv, query_key, sample_size
        )
    
    def download_data(self, database: str, count: int, webenv: str, 
                     query_key: str, batch_size: int = None) -> int:
        """下载数据库数据"""
        if not self.is_supported(database):
            raise ValueError(f"数据库 {database} 不被此下载器支持")
        
        return self.data_downloader.download_database_data(
            database, count, webenv, query_key, batch_size
        )
    
    def process_database(self, database: str, download_full_data: bool = False) -> Dict[str, Any]:
        """处理单个数据库的完整流程"""
        if not self.is_supported(database):
            return {
                'database': database,
                'supported': False,
                'error': f"数据库 {database} 不被 {self.get_database_category()} 下载器支持"
            }
        
        try:
            # 搜索数据库
            count, webenv, query_key = self.search_database(database)
            
            if count == 0:
                return {
                    'database': database,
                    'supported': True,
                    'found_records': 0,
                    'downloaded_records': 0,
                    'message': '未找到相关记录'
                }
            
            print(f"[{self.get_database_category()}] {database}: 找到 {count} 条记录")
            
            # 获取预览信息
            preview_info = self.get_download_preview(database, count, webenv, query_key)
            
            downloaded_count = 0
            if download_full_data and webenv and query_key:
                # 下载完整数据
                downloaded_count = self.download_data(database, count, webenv, query_key)
            
            return {
                'database': database,
                'supported': True,
                'found_records': count,
                'downloaded_records': downloaded_count,
                'preview_info': preview_info,
                'category': self.get_database_category()
            }
            
        except Exception as e:
            return {
                'database': database,
                'supported': True,
                'error': str(e),
                'category': self.get_database_category()
            }
    
    def process_all_supported_databases(self, available_databases: List[str], 
                                      download_full_data: bool = False) -> List[Dict[str, Any]]:
        """处理所有支持的数据库"""
        results = []
        supported_dbs = [db for db in available_databases if self.is_supported(db)]
        
        if not supported_dbs:
            print(f"[{self.get_database_category()}] 没有找到支持的数据库")
            return results
        
        print(f"[{self.get_database_category()}] 开始处理 {len(supported_dbs)} 个数据库:")
        print(f"  支持的数据库: {', '.join(supported_dbs)}")
        
        for database in supported_dbs:
            print(f"\n[{self.get_database_category()}] 正在处理数据库: {database}")
            result = self.process_database(database, download_full_data)
            results.append(result)
            
            # 简单的进度显示
            if result.get('found_records', 0) > 0:
                print(f"  ✓ 找到 {result['found_records']} 条记录")
                if download_full_data:
                    print(f"  ✓ 下载 {result.get('downloaded_records', 0)} 条记录")
            else:
                print(f"  - 未找到记录")
        
        return results
    
    def get_summary(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """获取处理结果摘要"""
        total_found = sum(r.get('found_records', 0) for r in results)
        total_downloaded = sum(r.get('downloaded_records', 0) for r in results)
        successful_dbs = len([r for r in results if r.get('found_records', 0) > 0])
        
        return {
            'category': self.get_database_category(),
            'processed_databases': len(results),
            'successful_databases': successful_dbs,
            'total_found_records': total_found,
            'total_downloaded_records': total_downloaded,
            'results': results
        }
