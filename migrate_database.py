"""
Database Migration Script
Drops the old table and recreates with new structure
WARNING: This will delete all existing data!
"""

import mysql.connector
import configparser
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def migrate_database():
    """Migrate database to new structure"""
    
    # Load configuration
    config = configparser.ConfigParser()
    config.read('config.ini')
    
    try:
        # Get database configuration
        db_host = config.get('DATABASE', 'host')
        db_port = config.getint('DATABASE', 'port')
        db_user = config.get('DATABASE', 'user')
        db_password = config.get('DATABASE', 'password')
        db_name = config.get('DATABASE', 'database')
        
        # Connect to database
        logger.info(f"Connecting to database: {db_name}")
        connection = mysql.connector.connect(
            host=db_host,
            port=db_port,
            user=db_user,
            password=db_password,
            database=db_name
        )
        
        cursor = connection.cursor()
        
        # Warning
        logger.warning("=" * 70)
        logger.warning("WARNING: This will DROP the existing 'messages_json_raw' table!")
        logger.warning("All existing data will be LOST!")
        logger.warning("=" * 70)
        
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            logger.info("Migration cancelled by user")
            return
        
        # Drop existing table
        logger.info("Dropping old table...")
        cursor.execute("DROP TABLE IF EXISTS messages_json_raw")
        connection.commit()
        logger.info("Old table dropped successfully")
        
        # Create new table
        logger.info("Creating new table structure...")
        create_table_query = """
        CREATE TABLE messages_json_raw (
            id INT AUTO_INCREMENT PRIMARY KEY,
            received_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            source_ip VARCHAR(45),
            source_port INT,
            timestamp_msg DOUBLE,
            station_id VARCHAR(50),
            channel INT,
            freq DOUBLE,
            level DOUBLE,
            error INT,
            mode VARCHAR(10),
            label VARCHAR(20),
            block_id VARCHAR(10),
            ack BOOLEAN,
            tail VARCHAR(20),
            text TEXT,
            msgno VARCHAR(20),
            flight VARCHAR(20),
            assstat VARCHAR(50),
            app_name VARCHAR(50),
            app_ver VARCHAR(50),
            INDEX idx_received_at (received_at),
            INDEX idx_station_id (station_id),
            INDEX idx_freq (freq),
            INDEX idx_tail (tail),
            INDEX idx_flight (flight),
            INDEX idx_app_name (app_name)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
        """
        
        cursor.execute(create_table_query)
        connection.commit()
        logger.info("New table created successfully!")
        
        # Close connection
        cursor.close()
        connection.close()
        
        logger.info("=" * 70)
        logger.info("Migration completed successfully!")
        logger.info("You can now start the backend with: python main.py")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        sys.exit(1)


if __name__ == '__main__':
    migrate_database()
