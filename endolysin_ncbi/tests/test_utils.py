"""
工具模块测试
"""

import pytest
import tempfile
import os

from endolysin_ncbi.utils.format_utils import (
    format_file_size, parse_genbank_records, parse_xml_records,
    parse_text_records, extract_record_id
)
from endolysin_ncbi.utils.file_utils import (
    create_output_directory, create_database_directory,
    generate_safe_filename
)


class TestFormatUtils:
    """格式化工具测试类"""
    
    def test_format_file_size(self):
        """测试文件大小格式化"""
        assert format_file_size(500) == "500 B"
        assert format_file_size(1536) == "1.50 KB"
        assert format_file_size(1048576) == "1.00 MB"
        assert format_file_size(1073741824) == "1.00 GB"
    
    def test_parse_genbank_records(self):
        """测试GenBank记录解析"""
        data = """LOCUS       TEST1
DEFINITION  Test sequence 1
//
LOCUS       TEST2
DEFINITION  Test sequence 2
//"""
        
        records = parse_genbank_records(data)
        assert len(records) == 2
        assert "TEST1" in records[0]
        assert "TEST2" in records[1]
    
    def test_parse_xml_records_pubmed(self):
        """测试PubMed XML记录解析"""
        data = """<PubmedArticle>
    <PMID>12345</PMID>
    <Article>Test Article 1</Article>
</PubmedArticle>
<PubmedArticle>
    <PMID>67890</PMID>
    <Article>Test Article 2</Article>
</PubmedArticle>"""
        
        records = parse_xml_records(data, 'pubmed')
        assert len(records) >= 1  # 至少应该找到一些记录
    
    def test_parse_text_records_sra(self):
        """测试SRA文本记录解析"""
        data = """Run\tBioProject\tBioSample
SRR123456\tPRJNA123\tSAMN123
SRR789012\tPRJNA456\tSAMN456"""
        
        records = parse_text_records(data, 'sra')
        assert len(records) == 2
        assert "SRR123456" in records[0]
        assert "SRR789012" in records[1]
    
    def test_extract_record_id_genbank(self):
        """测试从GenBank记录提取ID"""
        record = """LOCUS       NP_123456
DEFINITION  Test protein
ACCESSION   NP_123456
//"""
        
        record_id = extract_record_id(record, 'protein', 'gb', 1)
        assert record_id == "NP_123456"
    
    def test_extract_record_id_pubmed(self):
        """测试从PubMed记录提取ID"""
        record = """<PubmedArticle>
    <PMID Version="1">12345678</PMID>
    <Article>Test Article</Article>
</PubmedArticle>"""
        
        record_id = extract_record_id(record, 'pubmed', 'xml', 1)
        assert record_id == "PMID_12345678"
    
    def test_extract_record_id_default(self):
        """测试默认记录ID提取"""
        record = "Some unknown format record"
        
        record_id = extract_record_id(record, 'unknown', 'text', 5)
        assert record_id == "unknown_record_000005"


class TestFileUtils:
    """文件工具测试类"""
    
    def test_create_output_directory(self):
        """测试创建输出目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_dir = os.path.join(temp_dir, "test_output")
            create_output_directory(test_dir)
            assert os.path.exists(test_dir)
            assert os.path.isdir(test_dir)
    
    def test_create_database_directory(self):
        """测试创建数据库子目录"""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_dir = create_database_directory(temp_dir, "pubmed")
            expected_path = os.path.join(temp_dir, "pubmed")
            assert db_dir == expected_path
            assert os.path.exists(db_dir)
            assert os.path.isdir(db_dir)
    
    def test_generate_safe_filename(self):
        """测试生成安全文件名"""
        unsafe_name = "test/file<name>with|illegal*chars?.txt"
        safe_name = generate_safe_filename(unsafe_name)
        assert "/" not in safe_name
        assert "<" not in safe_name
        assert ">" not in safe_name
        assert "|" not in safe_name
        assert "*" not in safe_name
        assert "?" not in safe_name
        assert "test" in safe_name
        assert ".txt" in safe_name
