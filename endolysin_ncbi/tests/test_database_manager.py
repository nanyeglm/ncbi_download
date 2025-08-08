"""
数据库管理器测试模块
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from endolysin_ncbi.core.database_manager import DatabaseManager


class TestDatabaseManager:
    """数据库管理器测试类"""
    
    def setup_method(self):
        """测试前的设置"""
        self.db_manager = DatabaseManager()
    
    @patch('endolysin_ncbi.core.database_manager.Entrez.einfo')
    def test_get_available_databases_success(self, mock_einfo):
        """测试成功获取数据库列表"""
        # 模拟返回数据
        mock_handle = Mock()
        mock_einfo.return_value = mock_handle
        
        mock_result = {'DbList': ['pubmed', 'protein', 'nucleotide']}
        
        with patch('endolysin_ncbi.core.database_manager.Entrez.read', return_value=mock_result):
            databases = self.db_manager.get_available_databases()
            
        assert databases == ['pubmed', 'protein', 'nucleotide']
        mock_handle.close.assert_called_once()
    
    @patch('endolysin_ncbi.core.database_manager.Entrez.einfo')
    def test_get_available_databases_error(self, mock_einfo):
        """测试获取数据库列表时出错"""
        mock_einfo.side_effect = Exception("Network error")
        
        databases = self.db_manager.get_available_databases()
        
        assert databases == []
    
    @patch('endolysin_ncbi.core.database_manager.Entrez.esearch')
    def test_search_database_success(self, mock_esearch):
        """测试成功搜索数据库"""
        # 模拟返回数据
        mock_handle = Mock()
        mock_esearch.return_value = mock_handle
        
        mock_result = {
            'Count': '100',
            'WebEnv': 'test_webenv',
            'QueryKey': 'test_querykey'
        }
        
        with patch('endolysin_ncbi.core.database_manager.Entrez.read', return_value=mock_result):
            count, webenv, query_key = self.db_manager.search_database('pubmed')
            
        assert count == 100
        assert webenv == 'test_webenv'
        assert query_key == 'test_querykey'
        mock_handle.close.assert_called_once()
    
    @patch('endolysin_ncbi.core.database_manager.Entrez.esearch')
    def test_search_database_error(self, mock_esearch):
        """测试搜索数据库时出错"""
        mock_esearch.side_effect = Exception("Search error")
        
        count, webenv, query_key = self.db_manager.search_database('pubmed')
        
        assert count == 0
        assert webenv == ""
        assert query_key == ""
    
    @patch('endolysin_ncbi.core.database_manager.Entrez.esearch')
    def test_get_record_ids_success(self, mock_esearch):
        """测试成功获取记录ID"""
        mock_handle = Mock()
        mock_esearch.return_value = mock_handle
        
        mock_result = {'IdList': ['12345', '67890', '11111']}
        
        with patch('endolysin_ncbi.core.database_manager.Entrez.read', return_value=mock_result):
            ids = self.db_manager.get_record_ids('pubmed')
            
        assert ids == ['12345', '67890', '11111']
        mock_handle.close.assert_called_once()
    
    @patch('endolysin_ncbi.core.database_manager.Entrez.esummary')
    def test_get_record_summaries_success(self, mock_esummary):
        """测试成功获取记录摘要"""
        mock_handle = Mock()
        mock_esummary.return_value = mock_handle
        
        mock_summaries = [
            {
                'Id': '12345',
                'Title': 'Test Article 1',
                'AuthorList': 'Author A, Author B',
                'PubDate': '2023'
            },
            {
                'Id': '67890',
                'Title': 'Test Article 2',
                'Authors': 'Author C',
                'CreateDate': '2023-01-01'
            }
        ]
        
        with patch('endolysin_ncbi.core.database_manager.Entrez.read', return_value=mock_summaries):
            summaries = self.db_manager.get_record_summaries('pubmed', ['12345', '67890'])
            
        assert len(summaries) == 2
        assert summaries[0]['id'] == '12345'
        assert summaries[0]['title'] == 'Test Article 1'
        assert summaries[1]['id'] == '67890'
        assert summaries[1]['title'] == 'Test Article 2'
        mock_handle.close.assert_called_once()
    
    def test_get_record_summaries_empty_list(self):
        """测试空ID列表"""
        summaries = self.db_manager.get_record_summaries('pubmed', [])
        assert summaries == []
    
    @patch('endolysin_ncbi.core.database_manager.Entrez.efetch')
    def test_fetch_records_success(self, mock_efetch):
        """测试成功获取记录数据"""
        mock_handle = Mock()
        mock_efetch.return_value = mock_handle
        mock_handle.read.return_value = b"Test record data"
        
        data = self.db_manager.fetch_records(
            'pubmed', 'xml', 'xml', 0, 10, 'test_webenv', 'test_querykey'
        )
        
        assert data == "Test record data"
        mock_handle.close.assert_called_once()
    
    @patch('endolysin_ncbi.core.database_manager.Entrez.efetch')
    def test_fetch_records_error(self, mock_efetch):
        """测试获取记录数据时出错"""
        mock_efetch.side_effect = Exception("Fetch error")
        
        with pytest.raises(Exception, match="获取记录 1-10 时出错"):
            self.db_manager.fetch_records(
                'pubmed', 'xml', 'xml', 0, 10, 'test_webenv', 'test_querykey'
            )
