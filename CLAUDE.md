# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a financial data management system that scrapes stock ticker information from NASDAQ and stores it in a SQLite database for analysis.

## Key Components

### Database Structure
- **Database File**: `StockData.db` - SQLite database for financial data
- **Main Table**: `tickers` - Stores stock symbols, company names, sectors, and industries

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
```

### SQL Queries
- Query templates are available in `queries.sql`
- Contains utility queries for data inspection and table management

## Dependencies

- **playwright** - Web scraping and browser automation
- **pandas** - Data manipulation for ticker insertion
- **sqlite3** - Database operations (built-in Python module)

## File Structure
- `/Data/tickers/` - CSV data storage
- `/Data pulling/Get/` - Data acquisition scripts
- `/Data pulling/Insert/` - Database population scripts
- Root directory contains database and primary scripts

## Architecture Notes

The system follows a three-step ETL process:
1. **Extract**: Web scraping via Playwright from NASDAQ
2. **Transform**: CSV data processing with pandas
3. **Load**: SQLite database storage

The database is designed for forward-looking financial data with future extensibility for additional tables (revenue estimates, earnings data, analyst recommendations, etc.).