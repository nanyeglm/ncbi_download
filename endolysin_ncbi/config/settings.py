"""
Endolysin NCBI数据库下载器配置文件
包含所有可配置的参数和设置
"""

from pathlib import Path
import os

# 项目根目录（工作区根目录）
PROJECT_ROOT: Path = Path(__file__).resolve().parents[2]

# NCBI API配置
NCBI_EMAIL = os.getenv("ENDOLYSIN_NCBI_EMAIL", "nanyecpu@163.com")
NCBI_TOOL = os.getenv("ENDOLYSIN_NCBI_TOOL", "endolysin_search_script")
NCBI_API_KEY = os.getenv("ENDOLYSIN_NCBI_API_KEY", "")

# 下载配置（可通过环境变量覆盖）
MAX_RECORDS_PER_DATABASE = int(os.getenv("ENDOLYSIN_MAX_RECORDS_PER_DATABASE", "500000"))
BATCH_SIZE = int(os.getenv("ENDOLYSIN_BATCH_SIZE", "50"))
DOWNLOAD_DELAY = float(os.getenv("ENDOLYSIN_DOWNLOAD_DELAY", "1.0"))
SAMPLE_SIZE = int(os.getenv("ENDOLYSIN_SAMPLE_SIZE", "10"))

# 搜索配置
SEARCH_TERM = os.getenv("ENDOLYSIN_SEARCH_TERM", "endolysin")

# 输出配置（基于工作区根目录）
OUTPUT_DIR: Path = PROJECT_ROOT / os.getenv("ENDOLYSIN_OUTPUT_DIR", "endolysin_data")

# 重试与退避策略（用于请求失败的自恢复）
MAX_RETRIES = int(os.getenv("ENDOLYSIN_MAX_RETRIES", "5"))
RETRY_BACKOFF_BASE = float(os.getenv("ENDOLYSIN_RETRY_BACKOFF_BASE", "2.0"))
RETRY_JITTER_MAX = float(os.getenv("ENDOLYSIN_RETRY_JITTER_MAX", "0.5"))

# 数据库格式映射配置
DATABASE_FORMATS = {
    # 序列数据库 - 使用GenBank格式获取完整信息
    'sequence_databases': {
        'protein': ('gb', 'text'),
        'nucleotide': ('gb', 'text'),
        'nuccore': ('gb', 'text'),
        'nucest': ('gb', 'text'),
        'nucgss': ('gb', 'text'),
        'genome': ('gb', 'text'),
        'popset': ('gb', 'text'),
    },
    
    # 文献数据库 - 使用XML格式获取完整bibliographic信息
    'literature_databases': {
        'pubmed': ('xml', 'xml'),
        'pmc': ('xml', 'xml'),
        'books': ('xml', 'xml'),
    },
    
    # 基因和功能数据库 - 使用XML获取详细信息
    'gene_function_databases': {
        'gene': ('xml', 'xml'),
        'homologene': ('xml', 'xml'),
        'cdd': ('xml', 'xml'),
        'proteinclusters': ('xml', 'xml'),
    },
    
    # 生物项目和样本数据库
    'project_sample_databases': {
        'bioproject': ('xml', 'xml'),
        'biosample': ('xml', 'xml'),
        'sra': ('xml', 'xml'),
        'assembly': ('xml', 'xml'),
    },
    
    # 变异和临床数据库
    'variation_databases': {
        'snp': ('xml', 'xml'),
        'dbvar': ('xml', 'xml'),
        'clinvar': ('xml', 'xml'),
        'gap': ('xml', 'xml'),
    },
    
    # 化学和药物数据库
    'chemical_databases': {
        'pcassay': ('xml', 'xml'),
        'pccompound': ('xml', 'xml'),
        'pcsubstance': ('xml', 'xml'),
    },
    
    # 表达和功能数据库
    'expression_databases': {
        'gds': ('xml', 'xml'),
        'geo': ('xml', 'xml'),
        'unigene': ('xml', 'xml'),
        'probe': ('xml', 'xml'),
    },
    
    # 结构和分类数据库
    'structure_taxonomy_databases': {
        'structure': ('xml', 'xml'),
        'taxonomy': ('xml', 'xml'),
        'mesh': ('xml', 'xml'),
        'omim': ('xml', 'xml'),
    }
}

# 默认下载格式
DEFAULT_FORMAT = ('xml', 'xml')

def get_all_database_formats():
    """获取所有数据库格式的合并字典"""
    all_formats = {}
    for category in DATABASE_FORMATS.values():
        all_formats.update(category)
    return all_formats

def get_download_format(database):
    """根据数据库名称获取下载格式"""
    all_formats = get_all_database_formats()
    return all_formats.get(database.lower(), DEFAULT_FORMAT)

# 文件扩展名映射
FILE_EXTENSIONS = {
    'gb': 'gbk',
    'xml': 'xml',
    'csv': 'csv',
    'text': 'txt'
}

def get_file_extension(rettype, retmode):
    """根据返回类型和模式获取文件扩展名"""
    if rettype == 'gb':
        return 'gbk'
    elif retmode == 'xml':
        return 'xml'
    elif retmode == 'csv':
        return 'csv'
    else:
        return 'txt'
