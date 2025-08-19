#!/usr/bin/env python3
"""
Alchemy API Connector Implementation
"""

import requests
import logging
from typing import Dict, List, Optional, Tuple
from .base_connector import APIConnector
import time

logger = logging.getLogger(__name__)

class AlchemyConnector(APIConnector):
    """Alchemy API connector implementation."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = f"https://eth-mainnet.g.alchemy.com/v2/{api_key}"
    
    def _make_request(self, method: str, params: Dict = None) -> Dict:
        """Make API request to Alchemy."""
        if method == 'GET':
            try:
                response = requests.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed: {e}")
                return {'error': str(e)}
        else:  # POST
            try:
                response = requests.post(self.base_url, json=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except requests.exceptions.RequestException as e:
                logger.error(f"API request failed: {e}")
                return {'error': str(e)}
    
    def _get_current_head_block(self) -> int:
        """Get the current head block number."""
        params = {
            'id': 1,
            'jsonrpc': '2.0',
            'method': 'eth_blockNumber',
            'params': []
        }
        
        data = self._make_request('POST', params)
        if 'result' in data:
            return int(data['result'], 16)
        else:
            # Fallback to a reasonable default if we can't get the head block
            logger.warning("Could not get current head block, using fallback")
            return 23000000  # Conservative fallback
    
    def _get_block_range_from_epochs(self, start_epoch: Optional[int] = None, end_epoch: Optional[int] = None) -> Tuple[str, str]:
        """Convert epoch timestamps to block numbers for API calls."""
        if start_epoch is None and end_epoch is None:
            logger.debug("No time range specified, using full block range: 0x0 to latest")
            return '0x0', 'latest'
        
        # Get current head block
        head_block = self._get_current_head_block()
        
        if start_epoch is None:
            from_block = '0x0'
        else:
            # For start time, go back a reasonable number of blocks
            # Use a conservative approach: assume 15 seconds per block
            blocks_back = min((int(time.time()) - start_epoch) // 15, head_block)
            from_block = hex(max(0, head_block - blocks_back))
        
        if end_epoch is None:
            to_block = 'latest'
        else:
            # For end time, use current head block if it's in the future
            if end_epoch > int(time.time()):
                to_block = 'latest'
            else:
                # Calculate blocks back from current time
                blocks_back = min((int(time.time()) - end_epoch) // 15, head_block)
                to_block = hex(max(0, head_block - blocks_back))
        
        logger.debug(f"Time range {start_epoch} to {end_epoch} converted to block range: {from_block} to {to_block} (head: {hex(head_block)})")
        return from_block, to_block
    
    def get_normal_transactions(self, address: str, start_epoch: Optional[int] = None, end_epoch: Optional[int] = None) -> List[Dict]:
        """Get normal transactions for an address."""
        from_block, to_block = self._get_block_range_from_epochs(start_epoch, end_epoch)
        
        params = {
            'id': 1,
            'jsonrpc': '2.0',
            'method': 'alchemy_getAssetTransfers',
            'params': [
                {
                    'fromBlock': from_block,
                    'toBlock': to_block,
                    'category': ['external'],
                    'withMetadata': True,
                    'excludeZeroValue': False,
                    'maxCount': '0x3e8',
                    'order': 'desc',
                    'fromAddress': address
                }
            ]
        }
        
        data = self._make_request('POST', params)
        
        if 'result' in data and 'transfers' in data['result']:
            transfers = data['result']['transfers']
            transactions = []
            
            for transfer in transfers:
                tx = {
                    'hash': transfer.get('hash', ''),
                    'from': transfer.get('from', ''),
                    'to': transfer.get('to', ''),
                    'value': transfer.get('value', '0'),
                    'timeStamp': str(transfer.get('timestamp', 0)),
                    'blockNumber': str(transfer.get('blockNum', 0)),
                    'gasUsed': transfer.get('gasUsed', '0'),
                    'gasPrice': transfer.get('gasPrice', '0')
                }
                transactions.append(tx)
            
            return transactions
        else:
            error_message = data.get('error', 'Unknown error')
            if 'No transactions found' in error_message or 'No records found' in error_message:
                logger.info(f"No normal transactions found for address {address} in the specified time range")
            else:
                logger.error(f"Error fetching normal transactions from Alchemy: {error_message}")
            return []
    
    def get_internal_transactions(self, address: str, start_epoch: Optional[int] = None, end_epoch: Optional[int] = None) -> List[Dict]:
        """Get internal transactions for an address."""
        # Alchemy doesn't have direct internal transaction endpoint
        # Return empty list for now
        logger.info("Internal transactions not directly supported by Alchemy API")
        return []
    
    def get_erc20_transfers(self, address: str, start_epoch: Optional[int] = None, end_epoch: Optional[int] = None) -> List[Dict]:
        """Get ERC-20 token transfers for an address."""
        from_block, to_block = self._get_block_range_from_epochs(start_epoch, end_epoch)
        
        params = {
            'id': 1,
            'jsonrpc': '2.0',
            'method': 'alchemy_getAssetTransfers',
            'params': [
                {
                    'fromBlock': from_block,
                    'toBlock': to_block,
                    'category': ['erc20'],
                    'withMetadata': True,
                    'excludeZeroValue': False,
                    'maxCount': '0x3e8',
                    'order': 'desc',
                    'fromAddress': address
                }
            ]
        }
        
        data = self._make_request('POST', params)
        
        if 'result' in data and 'transfers' in data['result']:
            transfers = data['result']['transfers']
            transactions = []
            
            for transfer in transfers:
                tx = {
                    'hash': transfer.get('hash', ''),
                    'from': transfer.get('from', ''),
                    'to': transfer.get('to', ''),
                    'value': transfer.get('value', '0'),
                    'contractAddress': transfer.get('rawContract', {}).get('address', ''),
                    'tokenName': transfer.get('asset', ''),
                    'tokenSymbol': transfer.get('asset', ''),
                    'tokenDecimal': '18',
                    'timeStamp': str(transfer.get('timestamp', 0)),
                    'blockNumber': str(transfer.get('blockNum', 0)),
                    'gasUsed': transfer.get('gasUsed', '0'),
                    'gasPrice': transfer.get('gasPrice', '0')
                }
                transactions.append(tx)
            
            return transactions
        else:
            error_message = data.get('error', 'Unknown error')
            if 'No transactions found' in error_message or 'No records found' in error_message:
                logger.info(f"No ERC-20 transfers found for address {address} in the specified time range")
            else:
                logger.error(f"Error fetching ERC-20 transfers from Alchemy: {error_message}")
            return []
    
    def get_erc721_transfers(self, address: str, start_epoch: Optional[int] = None, end_epoch: Optional[int] = None) -> List[Dict]:
        """Get ERC-721 NFT transfers for an address."""
        from_block, to_block = self._get_block_range_from_epochs(start_epoch, end_epoch)
        
        params = {
            'id': 1,
            'jsonrpc': '2.0',
            'method': 'alchemy_getAssetTransfers',
            'params': [
                {
                    'fromBlock': from_block,
                    'toBlock': to_block,
                    'category': ['erc721'],
                    'withMetadata': True,
                    'excludeZeroValue': False,
                    'maxCount': '0x3e8',
                    'order': 'desc',
                    'fromAddress': address
                }
            ]
        }
        
        data = self._make_request('POST', params)
        
        if 'result' in data and 'transfers' in data['result']:
            transfers = data['result']['transfers']
            transactions = []
            
            for transfer in transfers:
                tx = {
                    'hash': transfer.get('hash', ''),
                    'from': transfer.get('from', ''),
                    'to': transfer.get('to', ''),
                    'value': '1',
                    'contractAddress': transfer.get('rawContract', {}).get('address', ''),
                    'tokenID': transfer.get('tokenId', ''),
                    'timeStamp': str(transfer.get('timestamp', 0)),
                    'blockNumber': str(transfer.get('blockNum', 0)),
                    'gasUsed': transfer.get('gasUsed', '0'),
                    'gasPrice': transfer.get('gasPrice', '0')
                }
                transactions.append(tx)
            
            return transactions
        else:
            error_message = data.get('error', 'Unknown error')
            if 'No transactions found' in error_message or 'No records found' in error_message:
                logger.info(f"No ERC-721 transfers found for address {address} in the specified time range")
            else:
                logger.error(f"Error fetching ERC-721 transfers from Alchemy: {error_message}")
            return []
    
    def get_erc1155_transfers(self, address: str, start_epoch: Optional[int] = None, end_epoch: Optional[int] = None) -> List[Dict]:
        """Get ERC-1155 transfers for an address."""
        # Alchemy doesn't have direct ERC-1155 endpoint
        # Return empty list for now
        logger.info("ERC-1155 transfers not directly supported by Alchemy API")
        return []
    
    def get_token_info(self, contract_address: str) -> Tuple[str, str]:
        """Get token symbol and name from contract address."""
        # Alchemy doesn't have direct token info endpoint
        # Return default values
        return 'Unknown', 'Unknown'
    
    def get_block_number_by_timestamp(self, timestamp: int) -> int:
        """Get block number for a given timestamp."""
        # Alchemy doesn't have direct block by timestamp endpoint
        # Return estimation
        return timestamp // 12  # Rough estimation: 1 block every 12 seconds
