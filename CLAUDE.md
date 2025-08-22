# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a financial data management system that scrapes stock ticker information from NASDAQ and stores it in a SQLite database for analysis.

## Key Components

### Database Structure
- **Database File**: `StockData.db` - SQLite database for financial data
- **Main Tables**:
  - `tickers` - Stores stock symbols, company names, sectors, and industries
  - `historic_prices` - Stores daily OHLCV price data for all tickers
  - `Key_Data` - Alternative ticker information table

### Core Scripts

1. **`createdb.py`** - Creates the database structure
   - Initializes `StockData.db` with the `tickers` table
   - Run with: `python3 createdb.py` or `./createdb.py`

2. **`Data pulling/Get/nasdaq_ticker-list.py`** - Downloads NASDAQ ticker data
   - Uses Playwright to scrape and download ticker list from nasdaq.com
   - Saves CSV file to `Data/tickers/nasdaq_screener.csv`
   - Run with: `python3 "Data pulling/Get/nasdaq_ticker-list.py"`

3. **`Data pulling/Insert/insert_tickers.py`** - Populates database with ticker data
   - Reads from `Data/tickers/nasdaq_screener.csv`
   - Inserts ticker data into the database
   - Run with: `python3 "Data pulling/Insert/insert_tickers.py"`

4. **`Data pulling/Insert/ticker-prices.py`** - Fetches historical price data
   - Uses yfinance to download historical OHLCV data for all tickers
   - Processes in chunks of 50 with user confirmation between chunks
   - Automatically avoids re-downloading existing data
   - Supports dry-run mode for testing
   - Run with: `python3 "Data pulling/Insert/ticker-prices.py"`
   - Options:
     - `--chunk-size N`: Process N tickers per chunk (default: 50)
     - `--tickers AAPL MSFT`: Process specific tickers only
     - `--dry-run`: Preview what would be done without downloading
     - `--db-path`: Custom database path

## Development Commands

### Environment Setup
```bash
# Project uses Python 3.9 with virtual environment
source .venv/bin/activate
```

### Database Operations
```bash
# Create fresh database structure
python3 createdb.py

# Download latest ticker data
python3 "Data pulling/Get/nasdaq_ticker-list.py"

# Insert ticker data into database
python3 "Data pulling/Insert/insert_tickers.py"

# Fetch historical price data (processes in chunks)
python3 "Data pulling/Insert/ticker-prices.py"

# Fetch price data for specific tickers only
python3 "Data pulling/Insert/ticker-prices.py" --tickers AAPL MSFT GOOGL

# Test run without downloading (dry run)
python3 "Data pulling/Insert/ticker-prices.py" --dry-run
```

### SQL Queries
- Query templates are available in `queries.sql`
- Contains utility queries for data inspection and table management

## Dependencies

- **playwright** - Web scraping and browser automation
- **pandas** - Data manipulation for ticker insertion and price data processing
- **yfinance** - Fetching historical stock price data from Yahoo Finance
- **sqlite3** - Database operations (built-in Python module)

## File Structure
- `/Data/tickers/` - CSV data storage
- `/Data pulling/Get/` - Data acquisition scripts
- `/Data pulling/Insert/` - Database population scripts
- Root directory contains database and primary scripts

## Architecture Notes

The system follows a multi-step ETL process:
1. **Extract Tickers**: Web scraping via Playwright from NASDAQ
2. **Transform & Load Tickers**: CSV data processing with pandas into database
3. **Extract Historical Prices**: Fetch OHLCV data via yfinance API
4. **Load Prices**: Incremental loading with duplicate prevention

Key Features:
- **Incremental Updates**: Only fetches new data since last update per ticker
- **Chunked Processing**: Handles large datasets in manageable chunks with user control
- **Error Resilience**: Comprehensive logging and error handling for failed tickers
- **Database Integrity**: Uses UNIQUE constraints to prevent duplicate entries

The database is designed for both historical and forward-looking financial data with extensibility for additional tables (revenue estimates, earnings data, analyst recommendations, etc.).