import pandas as pd
import sqlite3
from datetime import datetime

df = pd.read_csv('../../Data/tickers/nasdaq_screener.csv')
conn = sqlite3.connect('../../StockData.db')
data = [(row[0], row[1], row[2], row[3], datetime.now()) 
        for row in df[['Symbol', 'Name', 'Sector', 'Industry']].values]
conn.executemany(
    'INSERT OR IGNORE INTO tickers (symbol, company_name, sector, industry, last_updated) VALUES (?, ?, ?, ?, ?)',
    data
)
conn.commit()
changes = conn.total_changes
conn.close()
print(f"Inserted {changes} new tickers")