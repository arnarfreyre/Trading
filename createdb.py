#!/usr/bin/env python3
"""
Forward-Looking Financial Data Database Creator
Creates an SQLite database structure for financial data with historic prices
"""

import sqlite3
from datetime import datetime


class StockDataDB:
    """Manages SQLite database for forward-looking financial data"""

    def __init__(self, db_path: str = "StockData.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()

    def create_tables(self):
        """Create all necessary tables for forward data"""

        # Main ticker information table
        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS tickers
                            (
                                ticker_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                                symbol       TEXT UNIQUE NOT NULL,
                                company_name TEXT,
                                sector       TEXT,
                                industry     TEXT,
                                last_updated TIMESTAMP
                            )
                            ''')

        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS Key_Data
                            (
                                ticker_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                                symbol       TEXT UNIQUE NOT NULL,
                                company_name TEXT,
                                sector       TEXT,
                                industry     TEXT,
                                last_updated TIMESTAMP
                            )
                            ''')

        # Historic prices table (normalized structure)
        self.cursor.execute('''
                            CREATE TABLE IF NOT EXISTS historic_prices
                            (
                                price_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                                ticker_id  INTEGER NOT NULL,
                                date       DATE    NOT NULL,
                                open       REAL,
                                high       REAL,
                                low        REAL,
                                close      REAL,
                                adj_close  REAL,
                                volume     INTEGER,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                FOREIGN KEY (ticker_id) REFERENCES tickers (ticker_id),
                                UNIQUE (ticker_id, date)
                            )
                            ''')

        # Create index for faster queries
        self.cursor.execute('''
                            CREATE INDEX IF NOT EXISTS idx_historic_prices_date
                                ON historic_prices (date)
                            ''')

        self.cursor.execute('''
                            CREATE INDEX IF NOT EXISTS idx_historic_prices_ticker
                                ON historic_prices (ticker_id)
                            ''')

        self.conn.commit()
        print("✅ Database tables created successfully")

    def display_summary(self):
        """Display summary of tables in database"""
        print("\n" + "=" * 60)
        print("📈 DATABASE STRUCTURE SUMMARY")
        print("=" * 60)

        # Get all table names
        self.cursor.execute("""
                            SELECT name
                            FROM sqlite_master
                            WHERE type = 'table'
                            ORDER BY name
                            """)
        tables = self.cursor.fetchall()

        print(f"\nTotal tables created: {len(tables)}")
        print("\nTables:")
        for table in tables:
            table_name = table[0]
            # Get column count for each table
            self.cursor.execute(f"PRAGMA table_info({table_name})")
            columns = self.cursor.fetchall()
            print(f"  • {table_name}: {len(columns)} columns")

        print("\nTable Descriptions:")
        print("  • tickers: Stores basic ticker information")
        print("  • Key_Data: Alternative ticker information table")
        print("  • historic_prices: Stores daily price data for all tickers")

        print("=" * 60)

    def close(self):
        """Close database connection"""
        self.conn.close()


def main():
    """Main function to create empty database structure"""

    # Create database instance
    print("\n🔧 Creating empty database...")
    db = StockDataDB("StockData.db")

    # Create tables
    db.create_tables()

    # Display summary
    db.display_summary()

    # Close database
    db.close()
    print("\n✅ Empty database created successfully!")
    print("📁 Database saved to: StockData.db")
    print("💡 Ready for data population from yfinance")


if __name__ == "__main__":
    main()