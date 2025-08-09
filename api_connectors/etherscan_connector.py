#!/usr/bin/env python3
"""
Etherscan API Connector Implementation
"""

import requests
import logging
from typing import Dict, List, Optional, Tuple
from .base_connector import APIConnector

logger = logging.getLogger(__name__)

class EtherscanConnector(APIConnector):
    """Etherscan API connector implementation."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.etherscan.io/api"
    
    def _make_request(self, params: Dict) -> Dict:
        """Make API request to Etherscan."""
        params['apikey'] = self.api_key
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return {'status': '0', 'message': str(e)}
    
    def get_normal_transactions(self, address: str, start_epoch: Optional[int] = None, end_epoch: Optional[int] = None) -> List[Dict]:
        """Get normal transactions for an address."""
        params = {
            'module': 'account',
            'action': 'txlist',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'sort': 'desc'
        }
        
        if start_epoch:
            start_block = self.get_block_number_by_timestamp(start_epoch)
            params['startblock'] = start_block
        
        if end_epoch:
            end_block = self.get_block_number_by_timestamp(end_epoch)
            params['endblock'] = end_block
        
        data = self._make_request(params)
        
        if data['status'] == '1':
            transactions = data['result']
            
            if start_epoch or end_epoch:
                filtered_transactions = []
                for tx in transactions:
                    tx_timestamp = int(tx.get('timeStamp', 0))
                    if start_epoch and tx_timestamp < start_epoch:
                        continue
                    if end_epoch and tx_timestamp > end_epoch:
                        continue
                    filtered_transactions.append(tx)
                return filtered_transactions
            
            return transactions
        else:
            error_message = data.get('message', 'Unknown error')
            if 'No transactions found' in error_message or 'No records found' in error_message:
                logger.info(f"No normal transactions found for address {address} in the specified time range")
            else:
                logger.error(f"Error fetching normal transactions: {error_message}")
            return []
    
    def get_internal_transactions(self, address: str, start_epoch: Optional[int] = None, end_epoch: Optional[int] = None) -> List[Dict]:
        """Get internal transactions for an address."""
        params = {
            'module': 'account',
            'action': 'txlistinternal',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'sort': 'desc'
        }
        
        if start_epoch:
            start_block = self.get_block_number_by_timestamp(start_epoch)
            params['startblock'] = start_block
        
        if end_epoch:
            end_block = self.get_block_number_by_timestamp(end_epoch)
            params['endblock'] = end_block
        
        data = self._make_request(params)
        
        if data['status'] == '1':
            transactions = data['result']
            
            if start_epoch or end_epoch:
                filtered_transactions = []
                for tx in transactions:
                    tx_timestamp = int(tx.get('timeStamp', 0))
                    if start_epoch and tx_timestamp < start_epoch:
                        continue
                    if end_epoch and tx_timestamp > end_epoch:
                        continue
                    filtered_transactions.append(tx)
                return filtered_transactions
            
            return transactions
        else:
            error_message = data.get('message', 'Unknown error')
            if 'No transactions found' in error_message or 'No records found' in error_message:
                logger.info(f"No internal transactions found for address {address} in the specified time range")
            else:
                logger.error(f"Error fetching internal transactions: {error_message}")
            return []
    
    def get_erc20_transfers(self, address: str, start_epoch: Optional[int] = None, end_epoch: Optional[int] = None) -> List[Dict]:
        """Get ERC-20 token transfers for an address."""
        params = {
            'module': 'account',
            'action': 'tokentx',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'sort': 'desc'
        }
        
        if start_epoch:
            start_block = self.get_block_number_by_timestamp(start_epoch)
            params['startblock'] = start_block
        
        if end_epoch:
            end_block = self.get_block_number_by_timestamp(end_epoch)
            params['endblock'] = end_block
        
        data = self._make_request(params)
        
        if data['status'] == '1':
            transactions = data['result']
            
            if start_epoch or end_epoch:
                filtered_transactions = []
                for tx in transactions:
                    tx_timestamp = int(tx.get('timeStamp', 0))
                    if start_epoch and tx_timestamp < start_epoch:
                        continue
                    if end_epoch and tx_timestamp > end_epoch:
                        continue
                    filtered_transactions.append(tx)
                return filtered_transactions
            
            return transactions
        else:
            error_message = data.get('message', 'Unknown error')
            if 'No transactions found' in error_message or 'No records found' in error_message:
                logger.info(f"No ERC-20 transfers found for address {address} in the specified time range")
            else:
                logger.error(f"Error fetching ERC-20 transfers: {error_message}")
            return []
    
    def get_erc721_transfers(self, address: str, start_epoch: Optional[int] = None, end_epoch: Optional[int] = None) -> List[Dict]:
        """Get ERC-721 NFT transfers for an address."""
        params = {
            'module': 'account',
            'action': 'tokennfttx',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'sort': 'desc'
        }
        
        if start_epoch:
            start_block = self.get_block_number_by_timestamp(start_epoch)
            params['startblock'] = start_block
        
        if end_epoch:
            end_block = self.get_block_number_by_timestamp(end_epoch)
            params['endblock'] = end_block
        
        data = self._make_request(params)
        
        if data['status'] == '1':
            transactions = data['result']
            
            if start_epoch or end_epoch:
                filtered_transactions = []
                for tx in transactions:
                    tx_timestamp = int(tx.get('timeStamp', 0))
                    if start_epoch and tx_timestamp < start_epoch:
                        continue
                    if end_epoch and tx_timestamp > end_epoch:
                        continue
                    filtered_transactions.append(tx)
                return filtered_transactions
            
            return transactions
        else:
            error_message = data.get('message', 'Unknown error')
            if 'No transactions found' in error_message or 'No records found' in error_message:
                logger.info(f"No ERC-721 transfers found for address {address} in the specified time range")
            else:
                logger.error(f"Error fetching ERC-721 transfers: {error_message}")
            return []
    
    def get_erc1155_transfers(self, address: str, start_epoch: Optional[int] = None, end_epoch: Optional[int] = None) -> List[Dict]:
        """Get ERC-1155 transfers for an address."""
        params = {
            'module': 'account',
            'action': 'token1155tx',
            'address': address,
            'startblock': 0,
            'endblock': 99999999,
            'sort': 'desc'
        }
        
        if start_epoch:
            start_block = self.get_block_number_by_timestamp(start_epoch)
            params['startblock'] = start_block
        
        if end_epoch:
            end_block = self.get_block_number_by_timestamp(end_epoch)
            params['endblock'] = end_block
        
        data = self._make_request(params)
        
        if data['status'] == '1':
            transactions = data['result']
            
            if start_epoch or end_epoch:
                filtered_transactions = []
                for tx in transactions:
                    tx_timestamp = int(tx.get('timeStamp', 0))
                    if start_epoch and tx_timestamp < start_epoch:
                        continue
                    if end_epoch and tx_timestamp > end_epoch:
                        continue
                    filtered_transactions.append(tx)
                return filtered_transactions
            
            return transactions
        else:
            error_message = data.get('message', 'Unknown error')
            if 'No transactions found' in error_message or 'No records found' in error_message:
                logger.info(f"No ERC-1155 transfers found for address {address} in the specified time range")
            else:
                logger.error(f"Error fetching ERC-1155 transfers: {error_message}")
            return []
    
    def get_token_info(self, contract_address: str) -> Tuple[str, str]:
        """Get token symbol and name from contract address."""
        params = {
            'module': 'token',
            'action': 'tokeninfo',
            'contractaddress': contract_address
        }
        
        data = self._make_request(params)
        
        if data['status'] == '1' and data['result']:
            token_info = data['result'][0]
            symbol = token_info.get('symbol', 'Unknown')
            name = token_info.get('name', 'Unknown')
            return symbol, name
        
        return 'Unknown', 'Unknown'
    
    def get_block_number_by_timestamp(self, timestamp: int) -> int:
        """Get block number for a given timestamp."""
        params = {
            'module': 'block',
            'action': 'getblocknobytime',
            'timestamp': timestamp,
            'closest': 'before'
        }
        
        data = self._make_request(params)
        
        if data['status'] == '1':
            return int(data['result'])
        
        # Fallback estimation
        logger.warning(f"Could not get block number for timestamp {timestamp}, using estimation")
        return timestamp // 12  # Rough estimation: 1 block every 12 seconds
