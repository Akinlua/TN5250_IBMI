#!/usr/bin/env python3
"""
Database Recreation Script

This script drops and recreates all database tables.
"""

import os
from sqlalchemy import create_engine
from api.models import Base

def recreate_database():
    """Drop and recreate all database tables"""
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/tn5250_api')
    engine = create_engine(database_url)
    
    print("Dropping all tables...")
    Base.metadata.drop_all(engine)
    
    print("Creating all tables...")
    Base.metadata.create_all(engine)
    
    print("Database recreation completed!")
    print("Tables created:")
    for table_name in Base.metadata.tables.keys():
        print(f"  - {table_name}")

if __name__ == "__main__":
    recreate_database() 