#!/usr/bin/env python3
"""
Base API Connector Interface
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple

class APIConnector(ABC):
    """Abstract base class for API connectors."""
    
    @abstractmethod
    def get_normal_transactions(self, address: str, start_epoch: Optional[int] = None, end_epoch: Optional[int] = None) -> List[Dict]:
        """Get normal transactions for an address."""
        pass
    
    @abstractmethod
    def get_internal_transactions(self, address: str, start_epoch: Optional[int] = None, end_epoch: Optional[int] = None) -> List[Dict]:
        """Get internal transactions for an address."""
        pass
    
    @abstractmethod
    def get_erc20_transfers(self, address: str, start_epoch: Optional[int] = None, end_epoch: Optional[int] = None) -> List[Dict]:
        """Get ERC-20 token transfers for an address."""
        pass
    
    @abstractmethod
    def get_erc721_transfers(self, address: str, start_epoch: Optional[int] = None, end_epoch: Optional[int] = None) -> List[Dict]:
        """Get ERC-721 NFT transfers for an address."""
        pass
    
    @abstractmethod
    def get_erc1155_transfers(self, address: str, start_epoch: Optional[int] = None, end_epoch: Optional[int] = None) -> List[Dict]:
        """Get ERC-1155 transfers for an address."""
        pass
    
    @abstractmethod
    def get_token_info(self, contract_address: str) -> Tuple[str, str]:
        """Get token symbol and name from contract address."""
        pass
    
    @abstractmethod
    def get_block_number_by_timestamp(self, timestamp: int) -> int:
        """Get block number for a given timestamp."""
        pass
