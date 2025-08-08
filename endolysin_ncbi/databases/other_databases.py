"""
其他数据库下载器
处理项目、样本、变异、化学、结构和分类等其他类型的数据库
"""

from typing import List
from endolysin_ncbi.databases.base_downloader import BaseDownloader


class ProjectSampleDatabaseDownloader(BaseDownloader):
    """生物项目和样本数据库下载器"""
    
    def get_supported_databases(self) -> List[str]:
        """获取支持的项目和样本数据库列表"""
        return [
            'bioproject',   # 生物项目数据库
            'biosample',    # 生物样本数据库
            'sra',          # SRA测序数据库
            'assembly',     # 基因组组装数据库
        ]
    
    def get_database_category(self) -> str:
        """获取数据库类别名称"""
        return "项目样本数据库"
    
    def get_database_descriptions(self) -> dict:
        """获取数据库详细描述"""
        return {
            'bioproject': '生物项目数据库 - 研究项目信息',
            'biosample': '生物样本数据库 - 生物样本元数据',
            'sra': 'SRA测序数据库 - 序列读取档案',
            'assembly': '基因组组装数据库 - 基因组组装信息',
        }


class VariationDatabaseDownloader(BaseDownloader):
    """变异和临床数据库下载器"""
    
    def get_supported_databases(self) -> List[str]:
        """获取支持的变异数据库列表"""
        return [
            'snp',      # SNP变异数据库
            'dbvar',    # 结构变异数据库
            'clinvar',  # 临床变异数据库
            'gap',      # 基因型-表型数据库
        ]
    
    def get_database_category(self) -> str:
        """获取数据库类别名称"""
        return "变异数据库"
    
    def get_database_descriptions(self) -> dict:
        """获取数据库详细描述"""
        return {
            'snp': 'SNP变异数据库 - 单核苷酸多态性',
            'dbvar': '结构变异数据库 - 大型结构变异',
            'clinvar': '临床变异数据库 - 临床相关变异',
            'gap': '基因型-表型数据库 - 基因型与表型关联',
        }


class ChemicalDatabaseDownloader(BaseDownloader):
    """化学和药物数据库下载器"""
    
    def get_supported_databases(self) -> List[str]:
        """获取支持的化学数据库列表"""
        return [
            'pcassay',      # 生物测定数据库
            'pccompound',   # 化合物数据库
            'pcsubstance',  # 物质数据库
        ]
    
    def get_database_category(self) -> str:
        """获取数据库类别名称"""
        return "化学数据库"
    
    def get_database_descriptions(self) -> dict:
        """获取数据库详细描述"""
        return {
            'pcassay': '生物测定数据库 - 生物活性测定',
            'pccompound': '化合物数据库 - 化学化合物信息',
            'pcsubstance': '物质数据库 - 化学物质信息',
        }


class StructureTaxonomyDatabaseDownloader(BaseDownloader):
    """结构和分类数据库下载器"""
    
    def get_supported_databases(self) -> List[str]:
        """获取支持的结构和分类数据库列表"""
        return [
            'structure',    # 蛋白质结构数据库
            'taxonomy',     # 分类学数据库
            'mesh',         # MeSH术语数据库
            'omim',         # OMIM数据库
        ]
    
    def get_database_category(self) -> str:
        """获取数据库类别名称"""
        return "结构分类数据库"
    
    def get_database_descriptions(self) -> dict:
        """获取数据库详细描述"""
        return {
            'structure': '蛋白质结构数据库 - 3D结构信息',
            'taxonomy': '分类学数据库 - 生物分类信息',
            'mesh': 'MeSH术语数据库 - 医学主题词表',
            'omim': 'OMIM数据库 - 人类基因和遗传疾病',
        }
