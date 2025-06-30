#!/usr/bin/env python3
"""
Script to recreate database tables with updated schema
"""

from api.database import DatabaseService
from api.models import Base
from sqlalchemy import create_engine
import os

def main():
    # Get database URL
    database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:password@localhost:5432/tn5250_api')
    engine = create_engine(database_url)

    print('Dropping existing tables...')
    Base.metadata.drop_all(engine)
    
    print('Creating new tables with updated schema...')
    Base.metadata.create_all(engine)
    
    print('Database schema updated successfully!')
    print('All tables now have proper auto-increment primary keys.')

if __name__ == "__main__":
    main() 