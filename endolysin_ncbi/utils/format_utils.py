"""
格式化工具模块
包含文件大小格式化、记录解析等功能
"""

import re
from typing import List


def format_file_size(size_bytes: int) -> str:
    """格式化文件大小显示"""
    if size_bytes >= 1024*1024*1024:
        return f"{size_bytes/(1024*1024*1024):.2f} GB"
    elif size_bytes >= 1024*1024:
        return f"{size_bytes/(1024*1024):.2f} MB"
    elif size_bytes >= 1024:
        return f"{size_bytes/1024:.2f} KB"
    else:
        return f"{size_bytes} B"


def parse_genbank_records(data: str) -> List[str]:
    """解析GenBank格式数据，返回单个记录列表"""
    records = []
    current_record = []
    
    for line in data.split('\n'):
        current_record.append(line)
        if line.strip() == '//':
            if len(current_record) > 1:  # 确保不是空记录
                records.append('\n'.join(current_record))
            current_record = []
    
    # 处理最后一个记录（如果没有以//结尾）
    if current_record and any(line.strip() for line in current_record):
        records.append('\n'.join(current_record))
    
    return records


def parse_xml_records(data: str, database: str) -> List[str]:
    """解析XML格式数据，返回单个记录列表"""
    records = []
    
    # 不同数据库的XML结构不同，需要分别处理
    if database in ['pubmed', 'pmc']:
        # PubMed记录通常在<PubmedArticle>标签内
        pattern = r'<PubmedArticle.*?</PubmedArticle>'
        matches = re.findall(pattern, data, re.DOTALL)
        records.extend(matches)
        
        # 也检查<Article>标签
        pattern = r'<Article.*?</Article>'
        matches = re.findall(pattern, data, re.DOTALL)
        records.extend(matches)
        
    elif database in ['gene', 'biosample', 'bioproject']:
        # 基因、样本、项目记录
        pattern = r'<DocumentSummary.*?</DocumentSummary>'
        matches = re.findall(pattern, data, re.DOTALL)
        records.extend(matches)
        
    else:
        # 通用XML记录解析
        # 尝试找到重复的顶级元素
        common_patterns = [
            r'<DocumentSummary.*?</DocumentSummary>',
            r'<record.*?</record>',
            r'<entry.*?</entry>',
            r'<item.*?</item>'
        ]
        
        for pattern in common_patterns:
            matches = re.findall(pattern, data, re.DOTALL | re.IGNORECASE)
            if matches:
                records.extend(matches)
                break
    
    # 如果没有找到明确的记录分隔，将整个内容作为一个记录
    if not records and data.strip():
        records.append(data)
    
    return records


def parse_text_records(data: str, database: str) -> List[str]:
    """解析文本格式数据，返回单个记录列表"""
    records = []
    
    if database == 'sra':
        # SRA运行信息通常按行分隔
        lines = data.strip().split('\n')
        if len(lines) > 1:  # 跳过标题行
            for i, line in enumerate(lines[1:], 1):
                if line.strip():
                    records.append(f"# SRA Record {i}\n{lines[0]}\n{line}")
    else:
        # 其他文本格式，尝试按段落分隔
        paragraphs = data.split('\n\n')
        for i, paragraph in enumerate(paragraphs, 1):
            if paragraph.strip():
                records.append(paragraph)
    
    return records


def extract_record_id(record_content: str, database: str, rettype: str, record_index: int) -> str:
    """从记录内容中提取ID，用于文件命名"""
    if rettype == 'gb':
        # GenBank格式，查找ACCESSION行
        match = re.search(r'ACCESSION\s+(\S+)', record_content)
        if match:
            return match.group(1)
        # 查找LOCUS行
        match = re.search(r'LOCUS\s+(\S+)', record_content)
        if match:
            return match.group(1)
    
    elif database == 'pubmed':
        # PubMed ID
        match = re.search(r'<PMID.*?>(\d+)</PMID>', record_content)
        if match:
            return f"PMID_{match.group(1)}"
    
    elif database in ['gene', 'biosample', 'bioproject']:
        # DocumentSummary ID
        match = re.search(r'<DocumentSummary.*?uid="(\d+)"', record_content)
        if match:
            return f"{database}_{match.group(1)}"
    
    # 默认使用索引
    return f"{database}_record_{record_index:06d}"
