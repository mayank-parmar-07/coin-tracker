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
import logging
from datetime import datetime
from typing import Optional
from dotenv import load_dotenv
from utils.transaction_poller import TransactionPoller, CSVPersistor
from utils.transaction_parser import EthereumTransactionParser

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
        
        # Initialize components
        self.parser = EthereumTransactionParser(logger, self.connector_type)
        self.persistor = CSVPersistor(".", logger)
        self.poller = TransactionPoller(
            connector_type=self.connector_type,
            parser=self.parser,
            persistor=self.persistor,
            chunk_duration_minutes=15,  # Single 15-minute interval
            logger=logger
        )
        
        logger.info(f"Using {self.connector_type} connector with 15-minute polling intervals")
        
    def validate_address(self, address: str) -> bool:
        """Validate Ethereum address format."""
        if self._w3:
            return self._w3.isAddress(address)
        else:
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
    
    def run(self, address: str, start_epoch: Optional[str] = None, end_epoch: Optional[str] = None) -> str:
        """Main method to run the transaction tracker using the poller."""
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
        
        # Use current time as end epoch if not provided
        if not end_epoch_int:
            end_epoch_int = int(datetime.now().timestamp())
            logger.info(f"Using current time as end epoch: {self.epoch_to_datetime(end_epoch_int)}")
        
        # Use a reasonable start epoch if not provided (e.g., 1 year ago)
        if not start_epoch_int:
            start_epoch_int = end_epoch_int - (365 * 24 * 60 * 60)  # 1 year ago
            logger.info(f"Using 1 year ago as start epoch: {self.epoch_to_datetime(start_epoch_int)}")
        
        epoch_range_str = f" from {self.epoch_to_datetime(start_epoch_int)} to {self.epoch_to_datetime(end_epoch_int)}"
        logger.info(f"Starting transaction polling for address: {address}{epoch_range_str}")
        
        try:
            # Use the poller to fetch transactions in 15-minute chunks
            filename = self.poller.poll_transactions(
                address=address,
                start_epoch=start_epoch_int,
                end_epoch=end_epoch_int
            )
            
            logger.info(f"\nTransaction Summary for {address}{epoch_range_str}:")
            logger.info(f"Total transactions: {self.poller.total_transactions}")
            logger.info(f"Total chunks processed: {self.poller.total_chunks_processed}")
            logger.info(f"Output file: {filename}")
            
            return filename
            
        except Exception as e:
            logger.error(f"Error during transaction polling: {e}")
            raise


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
