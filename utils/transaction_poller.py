#!/usr/bin/env python3
"""
Transaction Poller for Ethereum Transaction History Tracker
Polls transactions in 15-minute chunks and handles parsing and persistence.
"""

import os
import sys
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import pandas as pd
from api_connectors import APIConnectorFactory
from dotenv import load_dotenv

load_dotenv()

class CSVPersistor:
    """CSV implementation of transaction persistor."""
    
    def __init__(self, output_dir: str = ".", logger=None):
        self.output_dir = output_dir
        self.logger = logger or logging.getLogger(__name__)
        os.makedirs(output_dir, exist_ok=True)
    
    def persist_transactions(self, transactions: List[Dict], filename: str = None) -> str:
        """Persist transactions to CSV file."""
        if not transactions:
            self.logger.warning("No transactions to persist.")
            return ""
        
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"ethereum_transactions_{timestamp}.csv"
        
        filepath = os.path.join(self.output_dir, filename)
        
        df = pd.DataFrame(transactions)
        
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
        df_export.to_csv(filepath, index=False)
        
        self.logger.info(f"Persisted {len(transactions)} transactions to {filepath}")
        return filepath
    
    def append_transactions(self, transactions: List[Dict], filename: str) -> bool:
        """Append transactions to existing CSV file."""
        if not transactions:
            return True
        
        filepath = os.path.join(self.output_dir, filename)
        
        if os.path.exists(filepath):
            try:
                existing_df = pd.read_csv(filepath)
                self.logger.info(f"Appending {len(transactions)} transactions to existing file {filepath}")
            except Exception as e:
                self.logger.error(f"Error reading existing file {filepath}: {e}")
                return False
        else:
            existing_df = pd.DataFrame()
            self.logger.info(f"Creating new file {filepath} with {len(transactions)} transactions")
        
        new_df = pd.DataFrame(transactions)
        
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
        
        new_df_export = new_df[column_order]
        
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
        
        new_df_export = new_df_export.rename(columns=column_mapping)
        
        if not existing_df.empty:
            combined_df = pd.concat([existing_df, new_df_export], ignore_index=True)
        else:
            combined_df = new_df_export
        
        combined_df.to_csv(filepath, index=False)
        
        self.logger.info(f"Successfully appended {len(transactions)} transactions to {filepath}")
        return True

class TransactionPoller:
    """Polls transactions in 15-minute chunks."""
    
    def __init__(self, 
                 connector_type: str,
                 parser,
                 persistor,
                 chunk_duration_minutes: int = 15,
                 logger=None):
        self.connector_type = connector_type
        self.parser = parser
        self.persistor = persistor
        self.chunk_duration_seconds = chunk_duration_minutes * 60
        self.logger = logger or logging.getLogger(__name__)
        
        try:
            self.api_connector = APIConnectorFactory.create_connector(connector_type)
            self.logger.info(f"Using {connector_type} connector for polling")
        except Exception as e:
            self.logger.error(f"Failed to create connector: {e}")
            raise
        
        self.total_transactions = 0
        self.total_chunks_processed = 0
        self.start_time = None
        self.last_processed_time = None
    
    def _epoch_to_datetime(self, epoch: int) -> datetime:
        """Convert epoch to datetime object in local timezone."""
        return datetime.fromtimestamp(epoch)
    
    def _datetime_to_epoch(self, dt: datetime) -> int:
        """Convert datetime object to epoch."""
        return int(dt.timestamp())
    
    def _get_chunk_boundaries(self, start_epoch: int, end_epoch: int) -> List[tuple[int, int]]:
        """Get list of chunk boundaries for the given time range."""
        chunks = []
        current_end = end_epoch
        
        while current_end > start_epoch:
            current_start = max(start_epoch, current_end - self.chunk_duration_seconds)
            chunks.append((current_start, current_end))
            current_end = current_start
        
        return list(reversed(chunks))
    
    def _fetch_transactions_for_chunk(self, address: str, start_epoch: int, end_epoch: int) -> List[Dict]:
        """Fetch all types of transactions for a specific time chunk."""
        all_transactions = []
        
        self.logger.debug(f"Fetching normal transactions for chunk {start_epoch} - {end_epoch}")
        normal_txs = self.api_connector.get_normal_transactions(address, start_epoch, end_epoch)
        for tx in normal_txs:
            parsed_tx = self.parser.parse_transaction(tx, internal=False)
            all_transactions.append(parsed_tx)
        
        self.logger.debug(f"Fetching internal transactions for chunk {start_epoch} - {end_epoch}")
        internal_txs = self.api_connector.get_internal_transactions(address, start_epoch, end_epoch)
        for tx in internal_txs:
            parsed_tx = self.parser.parse_transaction(tx, internal=True)
            all_transactions.append(parsed_tx)
        
        self.logger.debug(f"Fetching ERC-20 transfers for chunk {start_epoch} - {end_epoch}")
        erc20_txs = self.api_connector.get_erc20_transfers(address, start_epoch, end_epoch)
        for tx in erc20_txs:
            parsed_tx = self.parser.parse_transaction(tx, internal=False)
            all_transactions.append(parsed_tx)
        
        self.logger.debug(f"Fetching ERC-721 transfers for chunk {start_epoch} - {end_epoch}")
        erc721_txs = self.api_connector.get_erc721_transfers(address, start_epoch, end_epoch)
        for tx in erc721_txs:
            parsed_tx = self.parser.parse_transaction(tx, internal=False)
            all_transactions.append(parsed_tx)
        
        self.logger.debug(f"Fetching ERC-1155 transfers for chunk {start_epoch} - {end_epoch}")
        erc1155_txs = self.api_connector.get_erc1155_transfers(address, start_epoch, end_epoch)
        for tx in erc1155_txs:
            parsed_tx = self.parser.parse_transaction(tx, internal=False)
            all_transactions.append(parsed_tx)
        
        return all_transactions
    
    def poll_transactions(self, address: str, start_epoch: int, end_epoch: int, output_filename: str = None) -> str:
        """Poll transactions in 15-minute chunks from end_epoch back to start_epoch."""
        self.start_time = datetime.now()
        self.total_transactions = 0
        self.total_chunks_processed = 0
        
        self.logger.info(f"Starting transaction polling for address: {address}")
        self.logger.info(f"Time range: {self._epoch_to_datetime(start_epoch)} to {self._epoch_to_datetime(end_epoch)}")
        self.logger.info(f"Chunk duration: {self.chunk_duration_seconds // 60} minutes")
        
        if not output_filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"ethereum_transactions_{address}_{timestamp}.csv"
        
        chunks = self._get_chunk_boundaries(start_epoch, end_epoch)
        total_chunks = len(chunks)
        
        self.logger.info(f"Processing {total_chunks} chunks of {self.chunk_duration_seconds // 60} minutes each")
        
        try:
            for i, (chunk_start, chunk_end) in enumerate(chunks, 1):
                chunk_start_dt = self._epoch_to_datetime(chunk_start)
                chunk_end_dt = self._epoch_to_datetime(chunk_end)
                
                self.logger.info(f"Processing chunk {i}/{total_chunks}: {chunk_start_dt} to {chunk_end_dt}")
                
                chunk_transactions = self._fetch_transactions_for_chunk(address, chunk_start, chunk_end)
                
                if chunk_transactions:
                    chunk_transactions.sort(key=lambda x: x.get('date_time', ''), reverse=True)
                    
                    if i == 1:
                        self.persistor.persist_transactions(chunk_transactions, output_filename)
                    else:
                        self.persistor.append_transactions(chunk_transactions, output_filename)
                    
                    self.total_transactions += len(chunk_transactions)
                    self.logger.info(f"Chunk {i}/{total_chunks} completed: {len(chunk_transactions)} transactions")
                else:
                    self.logger.info(f"Chunk {i}/{total_chunks} completed: No transactions found")
                
                self.total_chunks_processed = i
                self.last_processed_time = chunk_end_dt
                
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.logger.warning("Polling interrupted by user")
            self._log_progress("INTERRUPTED")
            raise
        except Exception as e:
            self.logger.error(f"Error during polling: {e}")
            self._log_progress("ERROR")
            raise
        finally:
            self._log_final_summary(output_filename)
        
        return output_filename
    
    def _log_progress(self, status: str):
        """Log current progress."""
        if self.last_processed_time:
            self.logger.info(f"Polling {status} - Last processed time: {self.last_processed_time}")
            self.logger.info(f"Processed {self.total_chunks_processed} chunks with {self.total_transactions} transactions")
    
    def _log_final_summary(self, output_filename: str):
        """Log final summary."""
        end_time = datetime.now()
        duration = end_time - self.start_time if self.start_time else timedelta(0)
        
        self.logger.info("=" * 60)
        self.logger.info("POLLING SUMMARY")
        self.logger.info("=" * 60)
        self.logger.info(f"Start time: {self.start_time}")
        self.logger.info(f"End time: {end_time}")
        self.logger.info(f"Duration: {duration}")
        self.logger.info(f"Total chunks processed: {self.total_chunks_processed}")
        self.logger.info(f"Total transactions: {self.total_transactions}")
        self.logger.info(f"Output file: {output_filename}")
        self.logger.info("=" * 60)
