#!/usr/bin/env python3
"""
API Connector Factory
"""

import os
from typing import Optional
from .base_connector import APIConnector
from .etherscan_connector import EtherscanConnector
from .alchemy_connector import AlchemyConnector

class APIConnectorFactory:
    """Factory for creating API connectors."""
    
    @staticmethod
    def create_connector(connector_type: str) -> APIConnector:
        """Create a connector instance based on type."""
        if connector_type.lower() == 'etherscan':
            api_key = os.getenv('ETHERSCAN_API_KEY')
            if not api_key:
                raise ValueError("ETHERSCAN_API_KEY not found in environment variables")
            return EtherscanConnector(api_key)
        
        elif connector_type.lower() == 'alchemy':
            api_key = os.getenv('ALCHEMY_API_KEY')
            if not api_key:
                raise ValueError("ALCHEMY_API_KEY not found in environment variables")
            return AlchemyConnector(api_key)
        
        else:
            raise ValueError(f"Unknown connector type: {connector_type}")
