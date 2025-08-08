"""
下载器测试模块
"""

import pytest
from endolysin_ncbi.databases.sequence_databases import SequenceDatabaseDownloader
from endolysin_ncbi.databases.literature_databases import LiteratureDatabaseDownloader
from endolysin_ncbi.databases.gene_databases import GeneDatabaseDownloader


class TestSequenceDatabaseDownloader:
    """序列数据库下载器测试类"""
    
    def setup_method(self):
        """测试前的设置"""
        self.downloader = SequenceDatabaseDownloader("/tmp/test_output")
    
    def test_get_supported_databases(self):
        """测试获取支持的数据库列表"""
        databases = self.downloader.get_supported_databases()
        expected = ['protein', 'nucleotide', 'nuccore', 'nucest', 'nucgss', 'genome', 'popset']
        assert databases == expected
    
    def test_get_database_category(self):
        """测试获取数据库类别"""
        category = self.downloader.get_database_category()
        assert category == "序列数据库"
    
    def test_is_supported(self):
        """测试数据库支持检查"""
        assert self.downloader.is_supported('protein') == True
        assert self.downloader.is_supported('PROTEIN') == True  # 大小写不敏感
        assert self.downloader.is_supported('pubmed') == False
    
    def test_get_database_descriptions(self):
        """测试获取数据库描述"""
        descriptions = self.downloader.get_database_descriptions()
        assert 'protein' in descriptions
        assert '蛋白质序列数据库' in descriptions['protein']
    
    def test_get_priority_databases(self):
        """测试获取优先数据库列表"""
        priority = self.downloader.get_priority_databases()
        assert priority[0] == 'protein'  # 蛋白质数据库应该是最优先的


class TestLiteratureDatabaseDownloader:
    """文献数据库下载器测试类"""
    
    def setup_method(self):
        """测试前的设置"""
        self.downloader = LiteratureDatabaseDownloader("/tmp/test_output")
    
    def test_get_supported_databases(self):
        """测试获取支持的数据库列表"""
        databases = self.downloader.get_supported_databases()
        expected = ['pubmed', 'pmc', 'books']
        assert databases == expected
    
    def test_get_database_category(self):
        """测试获取数据库类别"""
        category = self.downloader.get_database_category()
        assert category == "文献数据库"
    
    def test_is_supported(self):
        """测试数据库支持检查"""
        assert self.downloader.is_supported('pubmed') == True
        assert self.downloader.is_supported('protein') == False


class TestGeneDatabaseDownloader:
    """基因数据库下载器测试类"""
    
    def setup_method(self):
        """测试前的设置"""
        self.downloader = GeneDatabaseDownloader("/tmp/test_output")
    
    def test_get_supported_databases(self):
        """测试获取支持的数据库列表"""
        databases = self.downloader.get_supported_databases()
        expected = ['gene', 'homologene', 'cdd', 'proteinclusters', 'gds', 'geo', 'unigene', 'probe']
        assert databases == expected
    
    def test_get_database_category(self):
        """测试获取数据库类别"""
        category = self.downloader.get_database_category()
        assert category == "基因功能数据库"
    
    def test_is_supported(self):
        """测试数据库支持检查"""
        assert self.downloader.is_supported('gene') == True
        assert self.downloader.is_supported('cdd') == True
        assert self.downloader.is_supported('pubmed') == False
