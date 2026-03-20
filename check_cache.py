#!/usr/bin/env python3
import sqlite3
import os

cache_path = ".nimbus_cache/notion.db"
if os.path.exists(cache_path):
    try:
        conn = sqlite3.connect(cache_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        print(f"Tables: {tables}")
        
        if tables:
            for table in tables:
                table_name = table[0]
                cur.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cur.fetchone()[0]
                print(f"  {table_name}: {count} records")
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
else:
    print("Cache file not found")
