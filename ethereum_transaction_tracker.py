#!/usr/bin/env python3
"""
Ethereum Transaction History Tracker

This script retrieves transaction history for a specified Ethereum wallet address
and exports it to a structured CSV file with relevant transaction details.

Usage:
    python ethereum_transaction_tracker.py <wallet_address> [start_epoch] [end_epoch]
    
Examples:
    python ethereum_transaction_tracker.py 0xa39b189482f984388a34460636fea9eb181ad1a6
    python ethereum_transaction_tracker.py 0xa39b189482f984388a34460636fea9eb181ad1a6 1704067200
    python ethereum_transaction_tracker.py 0xa39b189482f984388a34460636fea9eb181ad1a6 1704067200 1735689600
"""

import os
import sys
import requests
import pandas as pd
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
import json
from web3 import Web3
from dotenv import load_dotenv
import time
import logging
from api_connectors import APIConnectorFactory

load_dotenv()

def setup_logging():
    """Setup logging with level from config."""
    log_level_str = os.getenv('LOG_LEVEL', 'INFO').upper()
    
    try:
        log_level = getattr(logging, log_level_str)
    except AttributeError:
        print(f"Invalid log level '{log_level_str}'. Using INFO instead.")
        log_level = logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('ethereum_tracker.log')
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.debug(f"Logging level set to: {log_level_str}")
    return logger

logger = setup_logging()

class EthereumTransactionTracker:
    def __init__(self, connector_type: str = None):
        if connector_type:
            self.connector_type = connector_type
        else:
            self.connector_type = os.getenv('CONNECTOR_TYPE', 'etherscan')
        
        try:
            self.api_connector = APIConnectorFactory.create_connector(self.connector_type)
            logger.info(f"Using {self.connector_type} connector")
        except Exception as e:
            logger.error(f"Failed to create connector: {e}")
            raise
        
        alchemy_api_key = os.getenv('ALCHEMY_API_KEY')
        if alchemy_api_key:
            self.w3 = Web3(Web3.HTTPProvider(f'https://eth-mainnet.g.alchemy.com/v2/{alchemy_api_key}'))
        else:
            self.w3 = None
            
        self.uniswap_addresses = {
            '0x7a250d5630b4cf539739df2c5dacb4c659f2488d': 'Uniswap V2 Router',
            '0xe592427a0aece92de3edee1f18e0157c05861564': 'Uniswap V3 Router',
            '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984': 'Uniswap Token',
        }
        
    def validate_address(self, address: str) -> bool:
        """Validate Ethereum address format."""
        if not address.startswith('0x'):
            return False
        if len(address) != 42:
            return False
        try:
            int(address[2:], 16)
            return True
        except ValueError:
            return False
    
    def validate_epoch(self, epoch_str: str) -> Optional[int]:
        """Validate and parse epoch string."""
        try:
            epoch = int(epoch_str)
            if epoch < 0:
                return None
            return epoch
        except ValueError:
            return None
    
    def epoch_to_datetime(self, epoch: int) -> datetime:
        """Convert epoch to datetime object in local timezone."""
        return datetime.fromtimestamp(epoch)
    
    def datetime_to_epoch(self, dt: datetime) -> int:
        """Convert datetime object to epoch."""
        return int(dt.timestamp())
    
    def parse_transaction_type(self, tx: Dict, internal: bool = False) -> str:
        """Determine transaction type based on transaction data."""
        if internal:
            return "Internal Transfer"
        
        if tx.get('to') and tx['to'].startswith('0x'):
            to_address = tx['to'].lower()
            
            if to_address in self.uniswap_addresses:
                return "Uniswap Trade"
            
            if tx.get('input') and tx['input'] != '0x':
                input_data = tx['input'].lower()
                if input_data.startswith('0xa9059cbb'):  # transfer(address,uint256)
                    return "ERC-20 Transfer"
                elif input_data.startswith('0x23b872dd'):  # transferFrom(address,address,uint256)
                    return "ERC-20 Transfer"
                elif input_data.startswith('0x42842e0e'):  # safeTransferFrom(address,address,uint256)
                    return "ERC-721 Transfer"
                elif input_data.startswith('0xf242432a'):  # safeTransferFrom(address,address,uint256,uint256,bytes)
                    return "ERC-1155 Transfer"
                elif input_data.startswith('0x38ed1739'):  # swapExactTokensForTokens
                    return "Uniswap Trade"
                elif input_data.startswith('0x7ff36ab5'):  # swapExactETHForTokens
                    return "Uniswap Trade"
                elif input_data.startswith('0x18cbafe5'):  # swapExactTokensForETH
                    return "Uniswap Trade"
                elif input_data.startswith('0x4a25d94a'):  # swapExactTokensForTokens (V3)
                    return "Uniswap Trade"
                elif input_data.startswith('0x5c11d795'):  # exactInputSingle
                    return "Uniswap Trade"
                elif input_data.startswith('0x414bf389'):  # exactInput
                    return "Uniswap Trade"
                else:
                    return "Contract Interaction"
        
        return "ETH Transfer"
    
    def format_value(self, value: str, decimals: int = 18) -> str:
        """Format token value with proper decimals."""
        try:
            if value == '0':
                return '0'
            
            value_int = int(value)
            if value_int == 0:
                return '0'
            
            value_decimal = value_int / (10 ** decimals)
            return f"{value_decimal:.6f}"
        except (ValueError, TypeError):
            return value
    
    def timestamp_to_datetime(self, timestamp: str) -> str:
        """Convert Unix timestamp to readable datetime in local timezone."""
        try:
            dt = datetime.fromtimestamp(int(timestamp))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return timestamp
    
    def _create_transaction_dict(self, tx: Dict, tx_type: str, asset_symbol_name: str = 'ETH', token_id: str = '', decimals: int = 18) -> Dict:
        """Create a standardized transaction dictionary."""
        return {
            'transaction_hash': tx.get('hash', ''),
            'date_time': self.timestamp_to_datetime(tx.get('timeStamp', '')),
            'from_address': tx.get('from', ''),
            'to_address': tx.get('to', ''),
            'transaction_type': tx_type,
            'asset_contract_address': tx.get('contractAddress', ''),
            'asset_symbol_name': asset_symbol_name,
            'token_id': token_id,
            'value_amount': self.format_value(tx.get('value', '0'), decimals),
            'gas_fee_eth': self.format_value(tx.get('gasUsed', '0'), 18),
            'gas_price': tx.get('gasPrice', ''),
            'block_number': tx.get('blockNumber', ''),
            'confirmations': tx.get('confirmations', ''),
            'is_error': tx.get('isError', '0')
        }
    
    def _process_transaction_batch(self, transactions: List[Dict], tx_type: str, address: str) -> List[Dict]:
        """Process a batch of transactions of the same type."""
        processed_transactions = []
        
        for tx in transactions:
            # Default values
            asset_symbol_name = 'ETH'
            token_id = ''
            decimals = 18
            gas_fee_eth = self.format_value(tx.get('gasUsed', '0'), 18)
            
            # Handle token-specific logic
            if tx_type in ['ERC-20 Transfer', 'ERC-721 Transfer', 'ERC-1155 Transfer']:
                contract_address = tx.get('contractAddress', '')
                if contract_address:
                    symbol, name = self.api_connector.get_token_info(contract_address)
                    asset_symbol_name = f"{symbol} ({name})"
                
                if tx_type == 'ERC-721 Transfer':
                    token_id = tx.get('tokenID', '')
                    # ERC-721 typically has value of 1 (one NFT)
                    tx['value'] = '1'
                elif tx_type == 'ERC-1155 Transfer':
                    token_id = tx.get('tokenID', '')
                    decimals = int(tx.get('tokenDecimal', 18))
                else:  # ERC-20
                    decimals = int(tx.get('tokenDecimal', 18))
            
            # Handle internal transactions (no gas fee)
            if tx_type == 'Internal Transfer':
                gas_fee_eth = '0'
            
            transaction = self._create_transaction_dict(tx, tx_type, asset_symbol_name, token_id, decimals)
            transaction['gas_fee_eth'] = gas_fee_eth
            
            processed_transactions.append(transaction)
        
        return processed_transactions
    
    def _get_transaction_method(self, tx_type: str):
        """Get the appropriate method for fetching transactions by type."""
        method_map = {
            'normal': self.api_connector.get_normal_transactions,
            'internal': self.api_connector.get_internal_transactions,
            'erc20': self.api_connector.get_erc20_transfers,
            'erc721': self.api_connector.get_erc721_transfers,
            'erc1155': self.api_connector.get_erc1155_transfers
        }
        return method_map.get(tx_type)
    
    def process_transactions(self, address: str, start_epoch: Optional[int] = None, end_epoch: Optional[int] = None) -> List[Dict]:
        """Process all types of transactions and return structured data."""
        epoch_range_str = ""
        if start_epoch and end_epoch:
            start_dt = self.epoch_to_datetime(start_epoch)
            end_dt = self.epoch_to_datetime(end_epoch)
            epoch_range_str = f" from {start_dt.strftime('%Y-%m-%d %H:%M:%S')} to {end_dt.strftime('%Y-%m-%d %H:%M:%S')}"
        elif start_epoch:
            start_dt = self.epoch_to_datetime(start_epoch)
            epoch_range_str = f" from {start_dt.strftime('%Y-%m-%d %H:%M:%S')}"
        elif end_epoch:
            end_dt = self.epoch_to_datetime(end_epoch)
            epoch_range_str = f" until {end_dt.strftime('%Y-%m-%d %H:%M:%S')}"
            
        logger.info(f"Fetching transaction history for address: {address}{epoch_range_str}")
        
        all_transactions = []
        
        # Define transaction types to process
        transaction_types = [
            ('normal', 'Normal Transactions', 'ETH Transfer'),
            ('internal', 'Internal Transactions', 'Internal Transfer'),
            ('erc20', 'ERC-20 Token Transfers', 'ERC-20 Transfer'),
            ('erc721', 'ERC-721 NFT Transfers', 'ERC-721 Transfer'),
            ('erc1155', 'ERC-1155 Transfers', 'ERC-1155 Transfer')
        ]
        
        for tx_type, log_message, transaction_type in transaction_types:
            logger.info(f"Fetching {log_message.lower()}...")
            
            try:
                method = self._get_transaction_method(tx_type)
                if method:
                    transactions = method(address, start_epoch, end_epoch)
                    processed_transactions = self._process_transaction_batch(transactions, transaction_type, address)
                    all_transactions.extend(processed_transactions)
                    logger.info(f"Found {len(processed_transactions)} {log_message.lower()}")
                else:
                    logger.warning(f"No method found for transaction type: {tx_type}")
                    
            except Exception as e:
                logger.error(f"Error fetching {log_message.lower()}: {e}")
                continue
        
        all_transactions.sort(key=lambda x: x['date_time'], reverse=True)
        
        return all_transactions
    
    def export_to_csv(self, transactions: List[Dict], address: str) -> str:
        """Export transactions to CSV file."""
        if not transactions:
            logger.warning("No transactions found to export.")
            return ""
        
        df = pd.DataFrame(transactions)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"ethereum_transactions_{address}_{timestamp}.csv"
        
        column_order = [
            'transaction_hash',
            'date_time',
            'from_address',
            'to_address',
            'transaction_type',
            'asset_contract_address',
            'asset_symbol_name',
            'token_id',
            'value_amount',
            'gas_fee_eth'
        ]
        
        df_export = df[column_order]
        
        column_mapping = {
            'transaction_hash': 'Transaction Hash',
            'date_time': 'Date & Time',
            'from_address': 'From Address',
            'to_address': 'To Address',
            'transaction_type': 'Transaction Type',
            'asset_contract_address': 'Asset Contract Address',
            'asset_symbol_name': 'Asset Symbol / Name',
            'token_id': 'Token ID',
            'value_amount': 'Value / Amount',
            'gas_fee_eth': 'Gas Fee (ETH)'
        }
        
        df_export = df_export.rename(columns=column_mapping)
        df_export.to_csv(filename, index=False)
        
        logger.info(f"Exported {len(transactions)} transactions to {filename}")
        return filename
    
    def run(self, address: str, start_epoch: Optional[str] = None, end_epoch: Optional[str] = None) -> str:
        """Main method to run the transaction tracker."""
        if not self.validate_address(address):
            logger.error(f"Invalid Ethereum address format: {address}")
            return ""
        
        start_epoch_int = None
        end_epoch_int = None
        
        if start_epoch:
            start_epoch_int = self.validate_epoch(start_epoch)
            if not start_epoch_int:
                logger.error(f"Invalid start epoch: {start_epoch}. Must be a positive integer.")
                return ""
        
        if end_epoch:
            end_epoch_int = self.validate_epoch(end_epoch)
            if not end_epoch_int:
                logger.error(f"Invalid end epoch: {end_epoch}. Must be a positive integer.")
                return ""
        
        if start_epoch_int and end_epoch_int and start_epoch_int > end_epoch_int:
            logger.error("Start epoch cannot be after end epoch.")
            return ""
        
        transactions = self.process_transactions(address, start_epoch_int, end_epoch_int)
        
        if not transactions:
            logger.warning("No transactions found for this address and epoch range.")
            return ""
        
        filename = self.export_to_csv(transactions, address)
        
        epoch_range_str = ""
        if start_epoch_int and end_epoch_int:
            start_dt = self.epoch_to_datetime(start_epoch_int)
            end_dt = self.epoch_to_datetime(end_epoch_int)
            epoch_range_str = f" from {start_dt.strftime('%Y-%m-%d %H:%M:%S')} to {end_dt.strftime('%Y-%m-%d %H:%M:%S')}"
        elif start_epoch_int:
            start_dt = self.epoch_to_datetime(start_epoch_int)
            epoch_range_str = f" from {start_dt.strftime('%Y-%m-%d %H:%M:%S')}"
        elif end_epoch_int:
            end_dt = self.epoch_to_datetime(end_epoch_int)
            epoch_range_str = f" until {end_dt.strftime('%Y-%m-%d %H:%M:%S')}"
            
        logger.info(f"\nTransaction Summary for {address}{epoch_range_str}:")
        logger.info(f"Total transactions: {len(transactions)}")
        
        type_counts = {}
        for tx in transactions:
            tx_type = tx['transaction_type']
            type_counts[tx_type] = type_counts.get(tx_type, 0) + 1
        
        for tx_type, count in type_counts.items():
            logger.info(f"  {tx_type}: {count}")
        
        return filename


def main():
    """Main function to handle command line arguments and run the tracker."""
    if len(sys.argv) < 2 or len(sys.argv) > 4:
        logger.error("Usage: python ethereum_transaction_tracker.py <wallet_address> [start_epoch] [end_epoch]")
        logger.error("Examples:")
        logger.error("  python ethereum_transaction_tracker.py 0xa39b189482f984388a34460636fea9eb181ad1a6")
        logger.error("  python ethereum_transaction_tracker.py 0xa39b189482f984388a34460636fea9eb181ad1a6 1704067200")
        logger.error("  python ethereum_transaction_tracker.py 0xa39b189482f984388a34460636fea9eb181ad1a6 1704067200 1735689600")
        sys.exit(1)
    
    address = sys.argv[1]
    start_epoch = sys.argv[2] if len(sys.argv) > 2 else None
    end_epoch = sys.argv[3] if len(sys.argv) > 3 else None
    
    connector_type = os.getenv('CONNECTOR_TYPE', 'etherscan')
    
    try:
        tracker = EthereumTransactionTracker(connector_type)
        filename = tracker.run(address, start_epoch, end_epoch)
        
        if filename and filename != "":
            logger.info(f"\nTransaction history exported to: {filename}")
        else:
            logger.info("No transactions found for the specified address and time range.")
            
    except Exception as e:
        logger.error(f"Error initializing tracker: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
