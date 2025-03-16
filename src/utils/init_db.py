import sqlite3
import os
from pathlib import Path

def init_database():
    """Initialize the SQLite database with required tables."""
    # Create data directory if it doesn't exist
    data_dir = Path(__file__).parent.parent.parent / 'data'
    data_dir.mkdir(exist_ok=True)
    
    # Connect to database
    db_path = data_dir / 'prototype.db'
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create Documents table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_name TEXT NOT NULL,
        file_type TEXT NOT NULL,
        parsed_text TEXT,
        gemini_interpretation TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create Entities table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Entities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        document_id INTEGER,
        entity_type TEXT NOT NULL,
        entity_value TEXT NOT NULL,
        source TEXT NOT NULL,
        confidence FLOAT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (document_id) REFERENCES Documents (id)
    )
    ''')
    
    # Create Matches table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Matches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        jd_id INTEGER,
        resume_id INTEGER,
        score FLOAT NOT NULL,
        gemini_insight TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (jd_id) REFERENCES Documents (id),
        FOREIGN KEY (resume_id) REFERENCES Documents (id)
    )
    ''')
    
    # Create Feedback table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS Feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        match_id INTEGER,
        user_rating INTEGER,
        comments TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (match_id) REFERENCES Matches (id)
    )
    ''')
    
    # Create API Usage table for tracking Gemini API calls
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS APIUsage (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        api_key TEXT NOT NULL,
        endpoint TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        success BOOLEAN,
        error_message TEXT
    )
    ''')
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Database initialized successfully at {db_path}")

if __name__ == "__main__":
    init_database() 