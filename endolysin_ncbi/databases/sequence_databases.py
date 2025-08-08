"""
序列数据库下载器
专门处理蛋白质和核酸序列相关的数据库
"""

from typing import List
from endolysin_ncbi.databases.base_downloader import BaseDownloader


class SequenceDatabaseDownloader(BaseDownloader):
    """序列数据库下载器"""
    
    def get_supported_databases(self) -> List[str]:
        """获取支持的序列数据库列表"""
        return [
            'protein',      # 蛋白质序列数据库
            'nucleotide',   # 核酸序列数据库
            'nuccore',      # 核心核酸数据库
            'nucest',       # EST序列数据库
            'nucgss',       # GSS序列数据库
            'genome',       # 基因组序列数据库
            'popset',       # 群体序列数据库
        ]
    
    def get_database_category(self) -> str:
        """获取数据库类别名称"""
        return "序列数据库"
    
    def get_database_descriptions(self) -> dict:
        """获取数据库详细描述"""
        return {
            'protein': '蛋白质序列数据库 - 包含蛋白质序列和注释信息',
            'nucleotide': '核酸序列数据库 - 包含DNA和RNA序列',
            'nuccore': '核心核酸数据库 - 核酸序列的核心集合',
            'nucest': 'EST序列数据库 - 表达序列标签',
            'nucgss': 'GSS序列数据库 - 基因组调查序列',
            'genome': '基因组序列数据库 - 完整基因组序列',
            'popset': '群体序列数据库 - 群体遗传学序列集合',
        }
    
    def get_priority_databases(self) -> List[str]:
        """获取优先处理的数据库列表（按重要性排序）"""
        return [
            'protein',      # 最重要：蛋白质序列
            'nucleotide',   # 次重要：核酸序列
            'nuccore',      # 核心核酸数据
            'genome',       # 基因组数据
            'popset',       # 群体序列
            'nucest',       # EST序列
            'nucgss',       # GSS序列
        ]
