"""
Database Handler Module
Manages MySQL database connections and operations for ATC Datalink Backend
"""

import mysql.connector
from mysql.connector import Error
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class DatabaseHandler:
    """Handles all database operations for the ATC Datalink system"""
    
    def __init__(self, host, port, user, password, database, max_messages):
        """
        Initialize database handler
        
        Args:
            host (str): Database host address
            port (int): Database port
            user (str): Database username
            password (str): Database password
            database (str): Database name
            max_messages (int): Maximum number of messages to retain
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.max_messages = max_messages
        self.connection = None
        self.consecutive_failures = 0
        
    def connect(self):
        """Establish connection to MySQL database"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                autocommit=False,
                pool_reset_session=True
            )
            if self.connection.is_connected():
                self.consecutive_failures = 0
                logger.info(f"Successfully connected to MySQL database: {self.database}")
                return True
        except Error as e:
            logger.error(f"Error connecting to MySQL database: {e}")
            self.consecutive_failures += 1
            return False
    
    def _ensure_connection(self):
        """Ensure database connection is alive, reconnect if necessary"""
        import time
        
        try:
            if self.connection and self.connection.is_connected():
                # Test connection with a ping
                self.connection.ping(reconnect=False, attempts=1, delay=0)
                return True
        except Exception as e:
            logger.warning(f"Connection lost: {e}")
        
        # If too many consecutive failures, wait before retrying
        if self.consecutive_failures >= 3:
            logger.info(f"Too many consecutive failures ({self.consecutive_failures}), waiting 5 seconds...")
            time.sleep(5)
        
        # Connection is lost, try to reconnect
        logger.info(f"Attempting to reconnect (consecutive failures: {self.consecutive_failures})...")
        if self.connect():
            logger.info("Reconnection successful")
            return True
        else:
            logger.error("Reconnection attempt failed")
            return False
    
    def create_database_if_not_exists(self):
        """Create database if it doesn't exist"""
        try:
            # Connect without specifying database
            connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            cursor = connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            logger.info(f"Database '{self.database}' created or already exists")
            cursor.close()
            connection.close()
            return True
        except Error as e:
            logger.error(f"Error creating database: {e}")
            return False
    
    def create_table_if_not_exists(self):
        """Create messages_json_raw table if it doesn't exist"""
        if not self._ensure_connection():
            logger.error("Database connection is not established")
            return False
        
        try:
            cursor = self.connection.cursor()
            create_table_query = """
            CREATE TABLE IF NOT EXISTS messages_json_raw (
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
            self.connection.commit()
            logger.info("Table 'messages_json_raw' created or already exists")
            cursor.close()
            return True
        except Error as e:
            logger.error(f"Error creating table: {e}")
            return False
    
    def insert_message(self, source_ip, source_port, raw_data, json_data):
        """
        Insert a new message into the database
        
        Args:
            source_ip (str): Source IP address
            source_port (int): Source port
            raw_data (str): Raw message data (not used anymore, kept for compatibility)
            json_data (dict): Parsed JSON data
        """
        if not self.connection or not self.connection.is_connected():
            logger.error("Database connection is not established")
            return False
        
        try:
            cursor = self.connection.cursor()
            
            # Extract all fields from JSON
            timestamp_msg = json_data.get('timestamp', None)
            station_id = json_data.get('station_id', '')
            channel = json_data.get('channel', None)
            freq = json_data.get('freq', None)
            level = json_data.get('level', None)
            error = json_data.get('error', None)
            mode = json_data.get('mode', '')
            label = json_data.get('label', '')
            block_id = json_data.get('block_id', '')
            ack = json_data.get('ack', False)
            tail = json_data.get('tail', '')
            text = json_data.get('text', '')
            msgno = json_data.get('msgno', '')
            flight = json_data.get('flight', '')
            assstat = json_data.get('assstat', '')
            
            # Extract app name and version from nested object (excluding proxied fields)
            app_name = ''
            app_ver = ''
            if 'app' in json_data and isinstance(json_data['app'], dict):
                app_name = json_data['app'].get('name', '')
                app_ver = json_data['app'].get('ver', '')
            
            insert_query = """
            INSERT INTO messages_json_raw 
            (source_ip, source_port, timestamp_msg, station_id, channel, 
             freq, level, error, mode, label, block_id, ack, tail, text, 
             msgno, flight, assstat, app_name, app_ver)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                source_ip,
                source_port,
                timestamp_msg,
                station_id,
                channel,
                freq,
                level,
                error,
                mode,
                label,
                block_id,
                ack,
                tail,
                text,
                msgno,
                flight,
                assstat,
                app_name,
                app_ver
            ))
            
            self.connection.commit()
            message_id = cursor.lastrowid
            cursor.close()
            
            # Clean up old messages if limit exceeded
            self._cleanup_old_messages()
            
            logger.debug(f"Inserted message ID: {message_id}")
            return True
            
        except Error as e:
            logger.error(f"Error inserting message: {e}")
            return False
    
    def _cleanup_old_messages(self):
        """Remove old messages if count exceeds max_messages limit"""
        try:
            cursor = self.connection.cursor()
            
            # Count total messages
            cursor.execute("SELECT COUNT(*) FROM messages_json_raw")
            count = cursor.fetchone()[0]
            
            if count > self.max_messages:
                # Delete oldest messages
                messages_to_delete = count - self.max_messages
                delete_query = """
                DELETE FROM messages_json_raw 
                ORDER BY received_at ASC 
                LIMIT %s
                """
                cursor.execute(delete_query, (messages_to_delete,))
                self.connection.commit()
                logger.info(f"Cleaned up {messages_to_delete} old messages")
            
            cursor.close()
            
        except Error as e:
            logger.error(f"Error cleaning up old messages: {e}")
    
    def get_message_count(self):
        """Get total count of messages in database"""
        if not self.connection or not self.connection.is_connected():
            return 0
        
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT COUNT(*) FROM messages_json_raw")
            count = cursor.fetchone()[0]
            cursor.close()
            return count
        except Error as e:
            logger.error(f"Error getting message count: {e}")
            return 0
    
    def close(self):
        """Close database connection"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            logger.info("Database connection closed")
