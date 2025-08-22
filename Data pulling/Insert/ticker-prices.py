#!/usr/bin/env python3
"""
Historical Stock Price Data Fetcher
Fetches historical price data for all tickers in the database using yfinance.
Processes in chunks with user confirmation and avoids duplicate downloads.
"""

import sqlite3
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import sys
import logging
from typing import List, Tuple, Optional, Dict
import argparse
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ticker_prices_log.txt'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StockPriceUpdater:
    """Manages fetching and storing historical stock price data"""
    
    def __init__(self, db_path: str = "../../StockData.db", chunk_size: int = 50):
        """Initialize the updater with database connection"""
        self.db_path = Path(db_path).resolve()
        self.chunk_size = chunk_size
        self.conn = None
        self.cursor = None
        self.connect_db()
        
    def connect_db(self):
        """Establish database connection"""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            logger.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
            
    def get_all_tickers(self) -> List[Tuple[int, str, str]]:
        """Fetch all tickers from the database"""
        query = """
            SELECT ticker_id, symbol, company_name 
            FROM tickers 
            ORDER BY symbol
        """
        self.cursor.execute(query)
        return self.cursor.fetchall()
    
    def get_latest_price_date(self, ticker_id: int) -> Optional[datetime]:
        """Get the latest date we have price data for a ticker"""
        query = """
            SELECT MAX(date) 
            FROM historic_prices 
            WHERE ticker_id = ?
        """
        self.cursor.execute(query, (ticker_id,))
        result = self.cursor.fetchone()
        
        if result and result[0]:
            # Convert string date to datetime
            return datetime.strptime(result[0], '%Y-%m-%d')
        return None
    
    def fetch_historical_data(self, symbol: str, start_date: Optional[datetime] = None) -> pd.DataFrame:
        """
        Fetch historical data for a symbol from Yahoo Finance
        
        Args:
            symbol: Stock ticker symbol
            start_date: Start date for data fetch. If None, fetches all available history
            
        Returns:
            DataFrame with historical price data
        """
        try:
            ticker = yf.Ticker(symbol)
            
            # If we have existing data, fetch from the next day
            if start_date:
                start_date = start_date + timedelta(days=1)
                # Don't fetch if we're already up to date (start_date is in the future)
                if start_date >= datetime.now():
                    logger.info(f"  {symbol}: Already up to date")
                    return pd.DataFrame()
                    
                df = ticker.history(start=start_date, auto_adjust=False)
            else:
                # Fetch all available history
                df = ticker.history(period="max", auto_adjust=False)
            
            if df.empty:
                logger.warning(f"  {symbol}: No data available")
                return df
                
            # Reset index to make date a column
            df.reset_index(inplace=True)
            
            # Rename columns to match our database schema
            df.rename(columns={
                'Date': 'date',
                'Open': 'open',
                'High': 'high',
                'Low': 'low',
                'Close': 'close',
                'Adj Close': 'adj_close',
                'Volume': 'volume'
            }, inplace=True)
            
            # Remove timezone info if present
            if pd.api.types.is_datetime64_any_dtype(df['date']):
                df['date'] = df['date'].dt.tz_localize(None)
            
            return df
            
        except Exception as e:
            logger.error(f"  {symbol}: Error fetching data - {e}")
            return pd.DataFrame()
    
    def insert_price_data(self, ticker_id: int, df: pd.DataFrame) -> int:
        """
        Insert price data into the database
        
        Returns:
            Number of rows inserted
        """
        if df.empty:
            return 0
            
        try:
            # Prepare data for insertion
            data_to_insert = []
            for _, row in df.iterrows():
                data_to_insert.append((
                    ticker_id,
                    row['date'].strftime('%Y-%m-%d') if pd.notna(row['date']) else None,
                    row['open'] if pd.notna(row['open']) else None,
                    row['high'] if pd.notna(row['high']) else None,
                    row['low'] if pd.notna(row['low']) else None,
                    row['close'] if pd.notna(row['close']) else None,
                    row['adj_close'] if pd.notna(row['adj_close']) else None,
                    int(row['volume']) if pd.notna(row['volume']) else None
                ))
            
            # Batch insert with IGNORE to skip any duplicates
            self.cursor.executemany("""
                INSERT OR IGNORE INTO historic_prices 
                (ticker_id, date, open, high, low, close, adj_close, volume)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, data_to_insert)
            
            self.conn.commit()
            rows_inserted = self.cursor.rowcount
            return len(data_to_insert)  # Return actual number of rows we tried to insert
            
        except sqlite3.Error as e:
            logger.error(f"Database error during insertion: {e}")
            self.conn.rollback()
            return 0
    
    def process_ticker(self, ticker_id: int, symbol: str, company_name: str, dry_run: bool = False) -> Dict:
        """
        Process a single ticker: check existing data, fetch new data, and store it
        
        Returns:
            Dictionary with processing results
        """
        result = {
            'symbol': symbol,
            'success': False,
            'rows_added': 0,
            'error': None
        }
        
        try:
            # Check what data we already have
            latest_date = self.get_latest_price_date(ticker_id)
            
            if latest_date:
                logger.info(f"  {symbol}: Last data from {latest_date.strftime('%Y-%m-%d')}")
            else:
                logger.info(f"  {symbol}: No existing data, fetching full history")
            
            if dry_run:
                result['success'] = True
                result['dry_run'] = True
                return result
            
            # Fetch new data
            df = self.fetch_historical_data(symbol, latest_date)
            
            if not df.empty:
                # Insert the data
                rows_added = self.insert_price_data(ticker_id, df)
                result['rows_added'] = rows_added
                result['success'] = True
                
                if rows_added > 0:
                    logger.info(f"  {symbol}: Added {rows_added} new price records")
                else:
                    logger.info(f"  {symbol}: No new data to add")
            else:
                result['success'] = True  # No error, just no new data
                
        except Exception as e:
            result['error'] = str(e)
            logger.error(f"  {symbol}: Unexpected error - {e}")
            
        return result
    
    def process_chunk(self, tickers: List[Tuple[int, str, str]], chunk_num: int, 
                     total_chunks: int, dry_run: bool = False) -> Dict:
        """
        Process a chunk of tickers
        
        Returns:
            Dictionary with chunk processing results
        """
        chunk_results = {
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'rows_added': 0,
            'ticker_results': []
        }
        
        print(f"\n{'='*60}")
        print(f"Processing Chunk {chunk_num}/{total_chunks}")
        print(f"{'='*60}")
        print(f"Tickers in this chunk: {len(tickers)}")
        print(f"Symbols: {', '.join([t[1] for t in tickers[:10]])}" + 
              (f"... and {len(tickers)-10} more" if len(tickers) > 10 else ""))
        
        if dry_run:
            print("\n= DRY RUN MODE - No data will be downloaded")
        
        # Process each ticker with a small delay to avoid rate limiting
        for i, (ticker_id, symbol, company_name) in enumerate(tickers, 1):
            print(f"\n[{i}/{len(tickers)}] Processing {symbol} - {company_name[:40]}...")
            
            result = self.process_ticker(ticker_id, symbol, company_name, dry_run)
            chunk_results['ticker_results'].append(result)
            chunk_results['processed'] += 1
            
            if result['success']:
                chunk_results['successful'] += 1
                chunk_results['rows_added'] += result.get('rows_added', 0)
            else:
                chunk_results['failed'] += 1
            
            # Small delay between requests to be respectful to Yahoo Finance
            if not dry_run and i < len(tickers):
                time.sleep(0.5)
        
        return chunk_results
    
    def run(self, specific_tickers: Optional[List[str]] = None, dry_run: bool = False):
        """
        Main execution method
        
        Args:
            specific_tickers: List of specific ticker symbols to process (optional)
            dry_run: If True, only show what would be done without fetching data
        """
        try:
            # Get tickers to process
            all_tickers = self.get_all_tickers()
            
            if specific_tickers:
                # Filter to only specified tickers
                all_tickers = [t for t in all_tickers if t[1] in specific_tickers]
                if not all_tickers:
                    print("No matching tickers found in database")
                    return
            
            total_tickers = len(all_tickers)
            print(f"\n=Ê Found {total_tickers} tickers to process")
            
            if total_tickers == 0:
                print("No tickers found in database. Please run insert_tickers.py first.")
                return
            
            # Split into chunks
            chunks = [all_tickers[i:i + self.chunk_size] 
                     for i in range(0, total_tickers, self.chunk_size)]
            total_chunks = len(chunks)
            
            print(f"=æ Will process in {total_chunks} chunks of up to {self.chunk_size} tickers each")
            
            # Process statistics
            total_processed = 0
            total_successful = 0
            total_failed = 0
            total_rows_added = 0
            
            # Process each chunk
            for chunk_num, chunk in enumerate(chunks, 1):
                # Ask for user confirmation before each chunk
                if chunk_num > 1:  # Always process first chunk
                    print(f"\n{'='*60}")
                    response = input(f"\n= Ready to process chunk {chunk_num}/{total_chunks}? (y/n/q): ").lower()
                    if response == 'q':
                        print("Exiting...")
                        break
                    elif response != 'y':
                        print("Skipping this chunk...")
                        continue
                
                # Process the chunk
                chunk_results = self.process_chunk(chunk, chunk_num, total_chunks, dry_run)
                
                # Update totals
                total_processed += chunk_results['processed']
                total_successful += chunk_results['successful']
                total_failed += chunk_results['failed']
                total_rows_added += chunk_results['rows_added']
                
                # Show chunk summary
                print(f"\n{'='*60}")
                print(f"Chunk {chunk_num} Summary:")
                print(f"   Successful: {chunk_results['successful']}")
                print(f"  L Failed: {chunk_results['failed']}")
                print(f"  =È Rows added: {chunk_results['rows_added']}")
                print(f"{'='*60}")
            
            # Final summary
            print(f"\n{'='*60}")
            print("=Ê FINAL SUMMARY")
            print(f"{'='*60}")
            print(f"Total tickers processed: {total_processed}/{total_tickers}")
            print(f"Successful: {total_successful}")
            print(f"Failed: {total_failed}")
            print(f"Total rows added: {total_rows_added}")
            print(f"{'='*60}")
            
            if dry_run:
                print("\n= This was a DRY RUN - no data was actually downloaded")
                
        except KeyboardInterrupt:
            print("\n\n  Process interrupted by user")
            logger.info("Process interrupted by user")
        except Exception as e:
            logger.error(f"Unexpected error in main execution: {e}")
            raise
        finally:
            self.close()
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")


def main():
    """Main entry point with command-line interface"""
    parser = argparse.ArgumentParser(
        description="Fetch historical stock price data for tickers in the database"
    )
    parser.add_argument(
        '--chunk-size', 
        type=int, 
        default=50,
        help='Number of tickers to process in each chunk (default: 50)'
    )
    parser.add_argument(
        '--tickers',
        nargs='+',
        help='Specific ticker symbols to process (e.g., AAPL MSFT GOOGL)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without actually fetching data'
    )
    parser.add_argument(
        '--db-path',
        default='../../StockData.db',
        help='Path to the SQLite database (default: ../../StockData.db)'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("=È HISTORICAL STOCK PRICE DATA FETCHER")
    print("="*60)
    print(f"Database: {Path(args.db_path).resolve()}")
    print(f"Chunk size: {args.chunk_size}")
    if args.tickers:
        print(f"Specific tickers: {', '.join(args.tickers)}")
    if args.dry_run:
        print("Mode: DRY RUN (no data will be fetched)")
    print("="*60)
    
    # Create and run the updater
    updater = StockPriceUpdater(db_path=args.db_path, chunk_size=args.chunk_size)
    updater.run(specific_tickers=args.tickers, dry_run=args.dry_run)


if __name__ == "__main__":
    main()