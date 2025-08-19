#!/usr/bin/env python3
"""
Transaction Parser for Ethereum Transaction History Tracker
Parses raw transaction data into structured format.
"""

import logging
from datetime import datetime
from typing import Dict, Tuple
from api_connectors import APIConnectorFactory

class EthereumTransactionParser:
    """Parser for Ethereum transactions."""
    
    def __init__(self, logger=None, connector_type: str = 'etherscan'):
        self.logger = logger or logging.getLogger(__name__)
        self.connector_type = connector_type
        
        # Initialize API connector for token info
        try:
            self.api_connector = APIConnectorFactory.create_connector(connector_type)
        except Exception as e:
            self.logger.warning(f"Failed to create API connector for token info: {e}")
            self.api_connector = None
    
    def parse_transaction(self, tx: Dict, internal: bool = False) -> Dict:
        """Parse a single transaction and return structured data."""
        try:
            transaction_type = self._parse_transaction_type(tx, internal)
            value_amount = self._format_value(tx.get('value', '0'), int(tx.get('tokenDecimal', 18)))
            date_time = self._timestamp_to_datetime(tx.get('timeStamp', ''))
            
            asset_symbol_name = 'ETH'
            if tx.get('contractAddress'):
                symbol, name = self._get_token_info(tx.get('contractAddress', ''))
                asset_symbol_name = f"{symbol} ({name})"
            
            parsed_tx = {
                'transaction_hash': tx.get('hash', ''),
                'date_time': date_time,
                'from_address': tx.get('from', ''),
                'to_address': tx.get('to', ''),
                'transaction_type': transaction_type,
                'asset_contract_address': tx.get('contractAddress', ''),
                'asset_symbol_name': asset_symbol_name,
                'token_id': tx.get('tokenID', ''),
                'value_amount': value_amount,
                'gas_fee_eth': self._format_value(tx.get('gasUsed', '0'), 18),
                'gas_price': tx.get('gasPrice', ''),
                'block_number': tx.get('blockNumber', ''),
                'confirmations': tx.get('confirmations', ''),
                'is_error': tx.get('isError', '0')
            }
            
            return parsed_tx
            
        except Exception as e:
            self.logger.error(f"Error parsing transaction {tx.get('hash', 'unknown')}: {e}")
            return {
                'transaction_hash': tx.get('hash', ''),
                'date_time': self._timestamp_to_datetime(tx.get('timeStamp', '')),
                'from_address': tx.get('from', ''),
                'to_address': tx.get('to', ''),
                'transaction_type': 'ERROR',
                'asset_contract_address': '',
                'asset_symbol_name': 'ERROR',
                'token_id': '',
                'value_amount': '0',
                'gas_fee_eth': '0',
                'gas_price': '',
                'block_number': '',
                'confirmations': '',
                'is_error': '1'
            }
    
    def _parse_transaction_type(self, tx: Dict, internal: bool = False) -> str:
        """Determine transaction type based on transaction data."""
        if internal:
            return "Internal Transfer"
        
        if tx.get('to') and tx['to'].startswith('0x'):
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
                else:
                    return "Contract Interaction"
        
        return "ETH Transfer"
    
    def _format_value(self, value: str, decimals: int = 18) -> str:
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
    
    def _timestamp_to_datetime(self, timestamp: str) -> str:
        """Convert Unix timestamp to readable datetime in local timezone."""
        try:
            dt = datetime.fromtimestamp(int(timestamp))
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            return timestamp
    
    def _get_token_info(self, contract_address: str) -> Tuple[str, str]:
        """Get token symbol and name from contract address."""
        if not self.api_connector:
            return 'Unknown', 'Unknown'
        
        try:
            # Try to get token info from API connector
            if hasattr(self.api_connector, 'get_token_info'):
                symbol, name = self.api_connector.get_token_info(contract_address)
                return symbol, name
        except Exception as e:
            self.logger.debug(f"Could not get token info from API: {e}")
        
        # Fallback to hardcoded common tokens
        token_symbols = {
            '0xa0b86a33e6441b8c4c8c0b8c4c8c0b8c4c8c0b8c': 'USDC',
            '0xdac17f958d2ee523a2206206994597c13d831ec7': 'USDT',
            '0x2260fac5e5542a773aa44fbcfedf7c193bc2c599': 'WBTC',
            '0x514910771af9ca656af840dff83e8264ecf986ca': 'LINK',
            '0x1f9840a85d5af5bf1d1762f925bdaddc4201f984': 'UNI',
        }
        
        if contract_address.lower() in token_symbols:
            symbol = token_symbols[contract_address.lower()]
            return symbol, symbol
        
        return 'Unknown', 'Unknown'
