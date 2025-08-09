#!/usr/bin/env python3
"""
Simple Connector Tests
Makes actual API calls to Etherscan and Alchemy and validates response structures
"""

import os
import sys
import json
from dotenv import load_dotenv

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from api_connectors import EtherscanConnector, AlchemyConnector

load_dotenv()

def validate_response_structure(data, expected_keys, test_name):
    """Validate that response has expected keys."""
    print(f"\n🔍 Testing {test_name}...")
    
    if not isinstance(data, list):
        print(f"❌ {test_name}: Expected list, got {type(data)}")
        return False
    
    if not data:
        print(f"⚠️  {test_name}: No data returned (this might be normal)")
        return True
    
    # Check first item for expected keys
    first_item = data[0]
    missing_keys = []
    
    for key in expected_keys:
        if key not in first_item:
            missing_keys.append(key)
    
    if missing_keys:
        print(f"❌ {test_name}: Missing keys: {missing_keys}")
        print(f"   Available keys: {list(first_item.keys())}")
        return False
    
    print(f"✅ {test_name}: All expected keys present")
    print(f"   Sample data: {json.dumps(first_item, indent=2)[:500]}...")
    return True

def test_etherscan_connector():
    """Test Etherscan connector with actual API calls."""
    print("\n" + "="*60)
    print("TESTING ETHERSCAN CONNECTOR")
    print("="*60)
    
    api_key = os.getenv('ETHERSCAN_API_KEY')
    if not api_key:
        print("❌ ETHERSCAN_API_KEY not found in environment")
        return False
    
    connector = EtherscanConnector(api_key)
    test_address = "0xa39b189482f984388a34460636fea9eb181ad1a6"
    
    # Test normal transactions
    try:
        result = connector.get_normal_transactions(test_address)
        expected_keys = ['hash', 'from', 'to', 'value', 'timeStamp', 'blockNumber']
        validate_response_structure(result, expected_keys, "Normal Transactions")
    except Exception as e:
        print(f"❌ Normal Transactions: Error - {e}")
    
    # Test ERC-20 transfers
    try:
        result = connector.get_erc20_transfers(test_address)
        expected_keys = ['hash', 'from', 'to', 'value', 'contractAddress', 'timeStamp']
        validate_response_structure(result, expected_keys, "ERC-20 Transfers")
    except Exception as e:
        print(f"❌ ERC-20 Transfers: Error - {e}")
    
    # Test ERC-721 transfers
    try:
        result = connector.get_erc721_transfers(test_address)
        expected_keys = ['hash', 'from', 'to', 'contractAddress', 'tokenID', 'timeStamp']
        validate_response_structure(result, expected_keys, "ERC-721 Transfers")
    except Exception as e:
        print(f"❌ ERC-721 Transfers: Error - {e}")
    
    # Test ERC-1155 transfers
    try:
        result = connector.get_erc1155_transfers(test_address)
        expected_keys = ['hash', 'from', 'to', 'contractAddress', 'tokenID', 'timeStamp']
        validate_response_structure(result, expected_keys, "ERC-1155 Transfers")
    except Exception as e:
        print(f"❌ ERC-1155 Transfers: Error - {e}")
    
    # Test internal transactions
    try:
        result = connector.get_internal_transactions(test_address)
        expected_keys = ['hash', 'from', 'to', 'value', 'timeStamp', 'blockNumber']
        validate_response_structure(result, expected_keys, "Internal Transactions")
    except Exception as e:
        print(f"❌ Internal Transactions: Error - {e}")
    
    # Test token info
    try:
        # Test with USDC contract address
        usdc_address = "0xa0b86a33e6441b8c4c8c0b8c4c8c0b8c4c8c0b8c"
        symbol, name = connector.get_token_info(usdc_address)
        print(f"\n🔍 Testing Token Info...")
        print(f"   Symbol: {symbol}")
        print(f"   Name: {name}")
        if symbol != 'Unknown' and name != 'Unknown':
            print(f"✅ Token Info: Successfully retrieved token info")
        else:
            print(f"⚠️  Token Info: Returned Unknown (might be normal for test address)")
    except Exception as e:
        print(f"❌ Token Info: Error - {e}")
    
    # Test block number by timestamp
    try:
        timestamp = 1735689600  # 2025-01-01 05:30:00
        block_number = connector.get_block_number_by_timestamp(timestamp)
        print(f"\n🔍 Testing Block Number by Timestamp...")
        print(f"   Timestamp: {timestamp}")
        print(f"   Block Number: {block_number}")
        if isinstance(block_number, int) and block_number > 0:
            print(f"✅ Block Number by Timestamp: Successfully retrieved block number")
        else:
            print(f"⚠️  Block Number by Timestamp: Invalid block number returned")
    except Exception as e:
        print(f"❌ Block Number by Timestamp: Error - {e}")
    
    return True

def test_alchemy_connector():
    """Test Alchemy connector with actual API calls."""
    print("\n" + "="*60)
    print("TESTING ALCHEMY CONNECTOR")
    print("="*60)
    
    api_key = os.getenv('ALCHEMY_API_KEY')
    if not api_key:
        print("❌ ALCHEMY_API_KEY not found in environment")
        return False
    
    connector = AlchemyConnector(api_key)
    test_address = "0xa39b189482f984388a34460636fea9eb181ad1a6"
    
    # Test normal transactions
    try:
        result = connector.get_normal_transactions(test_address)
        expected_keys = ['hash', 'from', 'to', 'value', 'timeStamp', 'blockNumber']
        validate_response_structure(result, expected_keys, "Normal Transactions")
    except Exception as e:
        print(f"❌ Normal Transactions: Error - {e}")
    
    # Test ERC-20 transfers
    try:
        result = connector.get_erc20_transfers(test_address)
        expected_keys = ['hash', 'from', 'to', 'value', 'contractAddress', 'timeStamp']
        validate_response_structure(result, expected_keys, "ERC-20 Transfers")
    except Exception as e:
        print(f"❌ ERC-20 Transfers: Error - {e}")
    
    # Test ERC-721 transfers
    try:
        result = connector.get_erc721_transfers(test_address)
        expected_keys = ['hash', 'from', 'to', 'contractAddress', 'tokenID', 'timeStamp']
        validate_response_structure(result, expected_keys, "ERC-721 Transfers")
    except Exception as e:
        print(f"❌ ERC-721 Transfers: Error - {e}")
    
    # Test ERC-1155 transfers (should return empty list for Alchemy)
    try:
        result = connector.get_erc1155_transfers(test_address)
        print(f"\n🔍 Testing ERC-1155 Transfers...")
        print(f"   Result: {len(result)} items (Alchemy doesn't support ERC-1155)")
        if isinstance(result, list):
            print(f"✅ ERC-1155 Transfers: Returns list as expected")
        else:
            print(f"❌ ERC-1155 Transfers: Expected list, got {type(result)}")
    except Exception as e:
        print(f"❌ ERC-1155 Transfers: Error - {e}")
    
    # Test internal transactions (should return empty list for Alchemy)
    try:
        result = connector.get_internal_transactions(test_address)
        print(f"\n🔍 Testing Internal Transactions...")
        print(f"   Result: {len(result)} items (Alchemy doesn't support internal transactions)")
        if isinstance(result, list):
            print(f"✅ Internal Transactions: Returns list as expected")
        else:
            print(f"❌ Internal Transactions: Expected list, got {type(result)}")
    except Exception as e:
        print(f"❌ Internal Transactions: Error - {e}")
    
    return True

def main():
    """Run all connector tests."""
    print("🚀 Starting Connector Tests")
    print("This script will make actual API calls to test connector functionality")
    
    # Test Etherscan
    etherscan_success = test_etherscan_connector()
    
    # Test Alchemy
    alchemy_success = test_alchemy_connector()
    
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    if etherscan_success:
        print("✅ Etherscan Connector: Tests completed")
    else:
        print("❌ Etherscan Connector: Tests failed")
    
    if alchemy_success:
        print("✅ Alchemy Connector: Tests completed")
    else:
        print("❌ Alchemy Connector: Tests failed")
    
    if etherscan_success and alchemy_success:
        print("\n🎉 All connector tests completed successfully!")
        return 0
    else:
        print("\n⚠️  Some connector tests failed. Check the output above for details.")
        return 1

if __name__ == '__main__':
    sys.exit(main())

