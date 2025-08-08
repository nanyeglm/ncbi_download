"""
基因和功能数据库下载器
专门处理基因、蛋白质功能和表达相关的数据库
"""

from typing import List
from endolysin_ncbi.databases.base_downloader import BaseDownloader


class GeneDatabaseDownloader(BaseDownloader):
    """基因和功能数据库下载器"""
    
    def get_supported_databases(self) -> List[str]:
        """获取支持的基因和功能数据库列表"""
        return [
            'gene',             # 基因数据库
            'homologene',       # 同源基因数据库
            'cdd',              # 保守结构域数据库
            'proteinclusters',  # 蛋白质簇数据库
            'gds',              # 基因表达数据库
            'geo',              # GEO表达数据库
            'unigene',          # UniGene数据库
            'probe',            # 探针数据库
        ]
    
    def get_database_category(self) -> str:
        """获取数据库类别名称"""
        return "基因功能数据库"
    
    def get_database_descriptions(self) -> dict:
        """获取数据库详细描述"""
        return {
            'gene': '基因数据库 - 基因信息和注释',
            'homologene': '同源基因数据库 - 跨物种同源基因',
            'cdd': '保守结构域数据库 - 蛋白质保守结构域',
            'proteinclusters': '蛋白质簇数据库 - 相关蛋白质聚类',
            'gds': '基因表达数据库 - 基因表达数据集',
            'geo': 'GEO表达数据库 - 基因表达综合数据库',
            'unigene': 'UniGene数据库 - 基因表达和序列聚类',
            'probe': '探针数据库 - 微阵列探针信息',
        }
    
    def get_priority_databases(self) -> List[str]:
        """获取优先处理的数据库列表（按重要性排序）"""
        return [
            'gene',             # 最重要：基因信息
            'cdd',              # 次重要：保守结构域
            'proteinclusters',  # 蛋白质簇
            'homologene',       # 同源基因
            'gds',              # 基因表达
            'geo',              # GEO数据
            'unigene',          # UniGene
            'probe',            # 探针信息
        ]
