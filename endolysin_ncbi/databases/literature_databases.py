"""
文献数据库下载器
专门处理文献和出版物相关的数据库
"""

from typing import List
from endolysin_ncbi.databases.base_downloader import BaseDownloader


class LiteratureDatabaseDownloader(BaseDownloader):
    """文献数据库下载器"""
    
    def get_supported_databases(self) -> List[str]:
        """获取支持的文献数据库列表"""
        return [
            'pubmed',       # PubMed文献数据库
            'pmc',          # PMC全文数据库
            'books',        # 图书数据库
        ]
    
    def get_database_category(self) -> str:
        """获取数据库类别名称"""
        return "文献数据库"
    
    def get_database_descriptions(self) -> dict:
        """获取数据库详细描述"""
        return {
            'pubmed': 'PubMed文献数据库 - 生物医学文献摘要和引用',
            'pmc': 'PMC全文数据库 - PubMed Central全文文章',
            'books': '图书数据库 - NCBI图书和章节',
        }
    
    def get_priority_databases(self) -> List[str]:
        """获取优先处理的数据库列表（按重要性排序）"""
        return [
            'pubmed',       # 最重要：文献摘要
            'pmc',          # 次重要：全文文章
            'books',        # 图书资源
        ]
