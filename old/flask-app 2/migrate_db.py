#!/usr/bin/env python3
"""
Fixed Database migration script to add the share_token column
This version handles the UNIQUE constraint properly
"""

import sqlite3
import os
from pathlib import Path

def migrate_database():
    """Add share_token column to draft_version table if it doesn't exist"""
    
    # Try multiple possible database locations
    possible_paths = [
        Path(__file__).parent / "draft_mode.db",
        Path(__file__).parent / "instance" / "draft_mode.db",
        Path(__file__).parent / "instance" / "draft_mode.sqlite",
        Path(__file__).parent / "draft_mode.sqlite"
    ]
    
    db_path = None
    for path in possible_paths:
        if path.exists():
            db_path = path
            break
    
    if db_path is None:
        print("Database file not found in any of these locations:")
        for path in possible_paths:
            print(f"  - {path}")
        
        # Try to find any .db or .sqlite files
        print("\nSearching for database files...")
        for pattern in ["*.db", "*.sqlite", "*.sqlite3"]:
            for found_db in Path(__file__).parent.rglob(pattern):
                print(f"  Found: {found_db}")
        
        print("\nPlease specify the correct database path or create a new one.")
        return False
    
    print(f"Migrating database: {db_path}")
    
    try:
        # Connect to the database
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Check if share_token column exists
        cursor.execute("PRAGMA table_info(draft_version)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'share_token' not in columns:
            print("Adding share_token column to draft_version table...")
            
            # First, add the column WITHOUT the UNIQUE constraint
            cursor.execute("""
                ALTER TABLE draft_version 
                ADD COLUMN share_token VARCHAR(32)
            """)
            
            print("✓ share_token column added successfully")
            
            # Now create a unique index separately (this is optional and can be done later)
            try:
                cursor.execute("""
                    CREATE UNIQUE INDEX idx_draft_version_share_token 
                    ON draft_version(share_token) 
                    WHERE share_token IS NOT NULL
                """)
                print("✓ Unique index on share_token created successfully")
            except sqlite3.Error as e:
                print(f"⚠ Warning: Could not create unique index (this is okay): {e}")
                
        else:
            print("✓ share_token column already exists")
        
        # Commit the changes
        conn.commit()
        print("✓ Database migration completed successfully")
        
        # Verify the migration
        cursor.execute("PRAGMA table_info(draft_version)")
        columns = [column[1] for column in cursor.fetchall()]
        if 'share_token' in columns:
            print("✓ Migration verified: share_token column is present")
        else:
            print("✗ Migration verification failed: share_token column not found")
            return False
            
    except sqlite3.Error as e:
        print(f"✗ Database migration failed: {e}")
        return False
    
    finally:
        if conn:
            conn.close()
    
    return True

def check_database_schema():
    """Check the current database schema"""
    possible_paths = [
        Path(__file__).parent / "draft_mode.db",
        Path(__file__).parent / "instance" / "draft_mode.db",
        Path(__file__).parent / "instance" / "draft_mode.sqlite",
        Path(__file__).parent / "draft_mode.sqlite"
    ]
    
    db_path = None
    for path in possible_paths:
        if path.exists():
            db_path = path
            break
    
    if db_path is None:
        print("No database found to check")
        return False
    
    print(f"\nChecking database schema: {db_path}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Get draft_version table info
        cursor.execute("PRAGMA table_info(draft_version)")
        columns = cursor.fetchall()
        
        print("\nDraft_version table columns:")
        for col in columns:
            col_id, name, type_, not_null, default, pk = col
            print(f"  {name}: {type_}")
        
        # Check if share_token exists
        column_names = [col[1] for col in columns]
        if 'share_token' in column_names:
            print("✓ share_token column exists")
            
            # Check how many rows have share_token
            cursor.execute("SELECT COUNT(*) FROM draft_version WHERE share_token IS NOT NULL")
            count_with_token = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM draft_version")
            total_count = cursor.fetchone()[0]
            
            print(f"  Rows with share_token: {count_with_token}/{total_count}")
            
        else:
            print("✗ share_token column missing")
        
        conn.close()
        
    except sqlite3.Error as e:
        print(f"Error checking database: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("Starting database migration...")
    print("=" * 50)
    
    # First check current schema
    check_database_schema()
    
    # Then migrate
    if migrate_database():
        print("\n" + "=" * 50)
        print("Migration completed! Verifying results...")
        check_database_schema()
        print("\nYou can now start your Flask app.")
    else:
        print("\nMigration failed! Please check the error messages above.")