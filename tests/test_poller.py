#!/usr/bin/env python3
"""
Tests for Transaction Poller
"""

import unittest
import os
import sys
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.transaction_poller import TransactionPoller, CSVPersistor
from utils.transaction_parser import EthereumTransactionParser

load_dotenv()

class TestCSVPersistor(unittest.TestCase):
    """Test CSVPersistor functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.persistor = CSVPersistor(output_dir=self.temp_dir)
        self.test_transactions = [
            {
                'transaction_hash': '0x123',
                'date_time': '2024-01-01 12:00:00',
                'from_address': '0xa39b189482f984388a34460636fea9eb181ad1a6',
                'to_address': '0x456',
                'transaction_type': 'ETH Transfer',
                'asset_contract_address': '',
                'asset_symbol_name': 'ETH',
                'token_id': '',
                'value_amount': '1.0',
                'gas_fee_eth': '0.001'
            }
        ]
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_persist_transactions(self):
        """Test persisting transactions to CSV."""
        filename = self.persistor.persist_transactions(self.test_transactions, 'test.csv')
        
        self.assertTrue(os.path.exists(filename))
        self.assertIn('test.csv', filename)
    
    def test_append_transactions(self):
        """Test appending transactions to existing CSV."""
        # First, create a file
        filename = self.persistor.persist_transactions(self.test_transactions, 'test.csv')
        
        # Then append more transactions
        new_transactions = [
            {
                'transaction_hash': '0x789',
                'date_time': '2024-01-01 13:00:00',
                'from_address': '0xa39b189482f984388a34460636fea9eb181ad1a6',
                'to_address': '0xabc',
                'transaction_type': 'ERC-20 Transfer',
                'asset_contract_address': '0xdef',
                'asset_symbol_name': 'USDC',
                'token_id': '',
                'value_amount': '100.0',
                'gas_fee_eth': '0.002'
            }
        ]
        
        result = self.persistor.append_transactions(new_transactions, filename)
        self.assertTrue(result)

class TestTransactionPoller(unittest.TestCase):
    """Test TransactionPoller functionality."""
    
    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.parser = EthereumTransactionParser()
        self.persistor = CSVPersistor(output_dir=self.temp_dir)
        self.poller = TransactionPoller(
            connector_type='etherscan',
            parser=self.parser,
            persistor=self.persistor,
            chunk_duration_minutes=15
        )
        self.test_address = "0xa39b189482f984388a34460636fea9eb181ad1a6"
    
    def tearDown(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)
    
    def test_get_chunk_boundaries(self):
        """Test chunk boundary calculation."""
        # Test 1 hour range with 15-minute chunks
        start_epoch = 1735689600  # 2025-01-01 05:30:00
        end_epoch = 1735693200    # 2025-01-01 06:30:00
        
        chunks = self.poller._get_chunk_boundaries(start_epoch, end_epoch)
        
        # Should have 4 chunks (1 hour / 15 minutes = 4 chunks)
        self.assertEqual(len(chunks), 4)
        
        # Check first chunk
        first_chunk_start, first_chunk_end = chunks[0]
        self.assertEqual(first_chunk_start, start_epoch)
        self.assertEqual(first_chunk_end, start_epoch + 900)  # 15 minutes = 900 seconds
        
        # Check last chunk
        last_chunk_start, last_chunk_end = chunks[-1]
        self.assertEqual(last_chunk_end, end_epoch)
    
    def test_get_chunk_boundaries_small_range(self):
        """Test chunk boundary calculation for small range."""
        # Test 10-minute range with 15-minute chunks
        start_epoch = 1735689600
        end_epoch = 1735690200  # 10 minutes later
        
        chunks = self.poller._get_chunk_boundaries(start_epoch, end_epoch)
        
        # Should have 1 chunk (10 minutes < 15 minutes)
        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0][0], start_epoch)
        self.assertEqual(chunks[0][1], end_epoch)
    
    def test_epoch_to_datetime(self):
        """Test epoch to datetime conversion."""
        epoch = 1735689600
        dt = self.poller._epoch_to_datetime(epoch)
        
        self.assertIsInstance(dt, datetime)
        self.assertEqual(dt.year, 2025)
        self.assertEqual(dt.month, 1)
        self.assertEqual(dt.day, 1)
    
    @patch('utils.transaction_poller.APIConnectorFactory.create_connector')
    def test_fetch_transactions_for_chunk(self, mock_create_connector):
        """Test fetching transactions for a chunk."""
        # Mock the API connector
        mock_connector = MagicMock()
        mock_connector.get_normal_transactions.return_value = []
        mock_connector.get_internal_transactions.return_value = []
        mock_connector.get_erc20_transfers.return_value = []
        mock_connector.get_erc721_transfers.return_value = []
        mock_connector.get_erc1155_transfers.return_value = []
        mock_create_connector.return_value = mock_connector
        
        # Create a new poller with mocked connector
        poller = TransactionPoller(
            connector_type='etherscan',
            parser=self.parser,
            persistor=self.persistor,
            chunk_duration_minutes=15
        )
        
        start_epoch = 1735689600
        end_epoch = 1735689600 + 900  # 15 minutes
        
        result = poller._fetch_transactions_for_chunk(self.test_address, start_epoch, end_epoch)
        
        self.assertIsInstance(result, list)
        # Should be empty since we mocked empty responses
        self.assertEqual(len(result), 0)
    
    def test_poller_initialization(self):
        """Test poller initialization."""
        self.assertIsNotNone(self.poller)
        self.assertEqual(self.poller.chunk_duration_seconds, 900)  # 15 minutes
        self.assertEqual(self.poller.connector_type, 'etherscan')

if __name__ == '__main__':
    unittest.main()
