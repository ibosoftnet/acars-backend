"""
ATC Datalink Backend - Main Application
Listens to UDP messages and stores them in MySQL database
"""

import logging
import configparser
import sys
import signal
import time
from pathlib import Path

from database_handler import DatabaseHandler
from udp_listener import UDPListener
from sse_server import SSEServer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('atc_datalink.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


class ATCDatalinkBackend:
    """Main application class for ATC Datalink Backend"""
    
    def __init__(self, config_file='config.ini'):
        """
        Initialize the ATC Datalink Backend
        
        Args:
            config_file (str): Path to configuration file
        """
        self.config_file = config_file
        self.config = None
        self.db_handler = None
        self.udp_listener = None
        self.sse_server = None
        self.running = False
        
    def load_config(self):
        """Load configuration from INI file"""
        try:
            if not Path(self.config_file).exists():
                logger.error(f"Configuration file not found: {self.config_file}")
                return False
            
            self.config = configparser.ConfigParser()
            self.config.read(self.config_file)
            
            logger.info(f"Configuration loaded from {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False
    
    def initialize_database(self):
        """Initialize database connection and create tables"""
        try:
            # Get database configuration
            db_host = self.config.get('DATABASE', 'host')
            db_port = self.config.getint('DATABASE', 'port')
            db_user = self.config.get('DATABASE', 'user')
            db_password = self.config.get('DATABASE', 'password')
            db_name = self.config.get('DATABASE', 'database')
            max_messages = self.config.getint('RECORDING', 'max_messages')
            
            # Create database handler
            self.db_handler = DatabaseHandler(
                host=db_host,
                port=db_port,
                user=db_user,
                password=db_password,
                database=db_name,
                max_messages=max_messages
            )
            
            # Create database if not exists
            if not self.db_handler.create_database_if_not_exists():
                logger.error("Failed to create database")
                return False
            
            # Connect to database
            if not self.db_handler.connect():
                logger.error("Failed to connect to database")
                return False
            
            # Create table if not exists
            if not self.db_handler.create_table_if_not_exists():
                logger.error("Failed to create table")
                return False
            
            logger.info("Database initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            return False
    
    def initialize_sse_server(self):
        """Initialize SSE server for frontend communication"""
        try:
            # Get backend configuration
            backend_host = self.config.get('BACKEND', 'host')
            backend_port = self.config.getint('BACKEND', 'port')
            
            # Create SSE server (history count now controlled by frontend)
            self.sse_server = SSEServer(
                host=backend_host,
                port=backend_port,
                max_history_messages=100  # Backend'de saklanacak history sayısı
            )
            
            # Start server
            if not self.sse_server.start():
                logger.error("Failed to start SSE server")
                return False
            
            logger.info("SSE server initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing SSE server: {e}")
            return False
    
    def initialize_udp_listener(self):
        """Initialize UDP listener"""
        try:
            # Get listener configuration
            listener_host = self.config.get('LISTENER', 'host')
            listener_port = self.config.getint('LISTENER', 'port')
            
            # Create UDP listener with message callback
            self.udp_listener = UDPListener(
                host=listener_host,
                port=listener_port,
                message_callback=self.on_message_received
            )
            
            # Start listener
            if not self.udp_listener.start():
                logger.error("Failed to start UDP listener")
                return False
            
            logger.info("UDP listener initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing UDP listener: {e}")
            return False
    
    def on_message_received(self, source_ip, source_port, raw_data, json_data):
        """
        Callback function called when a UDP message is received
        
        Args:
            source_ip (str): Source IP address
            source_port (int): Source port
            raw_data (str): Raw ASCII data
            json_data (dict): Parsed JSON data
        """
        try:
            # Log message receipt
            station_id = json_data.get('station_id', 'Unknown')
            logger.info(f"Message from {source_ip}:{source_port} - Station: {station_id}")
            
            # Store message in database
            self.db_handler.insert_message(source_ip, source_port, raw_data, json_data)
            
            # Broadcast to frontend via SSE
            if self.sse_server:
                self.sse_server.broadcast_message(json_data)
            
        except Exception as e:
            logger.error(f"Error handling received message: {e}")
    
    def start(self):
        """Start the ATC Datalink Backend"""
        logger.info("=" * 60)
        logger.info("Starting ATC Datalink Backend")
        logger.info("=" * 60)
        
        # Load configuration
        if not self.load_config():
            logger.error("Failed to load configuration")
            return False
        
        # Initialize database
        if not self.initialize_database():
            logger.error("Failed to initialize database")
            return False
        
        # Initialize SSE server
        if not self.initialize_sse_server():
            logger.error("Failed to initialize SSE server")
            return False
        
        # Initialize UDP listener
        if not self.initialize_udp_listener():
            logger.error("Failed to initialize UDP listener")
            return False
        
        self.running = True
        logger.info("ATC Datalink Backend started successfully")
        logger.info("=" * 60)
        
        # Keep the application running
        try:
            while self.running:
                time.sleep(1)
                
                # Periodically log statistics
                if int(time.time()) % 60 == 0:  # Every minute
                    count = self.db_handler.get_message_count()
                    client_count = self.sse_server.get_client_count() if self.sse_server else 0
                    logger.info(f"Total messages in database: {count}, SSE clients: {client_count}")
                    
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        
        return True
    
    def stop(self):
        """Stop the ATC Datalink Backend"""
        logger.info("Stopping ATC Datalink Backend...")
        self.running = False
        
        # Stop UDP listener
        if self.udp_listener:
            self.udp_listener.stop()
        
        # Stop SSE server
        if self.sse_server:
            self.sse_server.stop()
        
        # Close database connection
        if self.db_handler:
            self.db_handler.close()
        
        logger.info("ATC Datalink Backend stopped")


def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    logger.info(f"Received signal {signum}")
    if hasattr(signal_handler, 'app') and signal_handler.app:
        signal_handler.app.stop()
    sys.exit(0)


def main():
    """Main entry point"""
    # Create application instance
    app = ATCDatalinkBackend()
    
    # Register signal handlers
    signal_handler.app = app
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start application
    try:
        app.start()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    finally:
        app.stop()


if __name__ == '__main__':
    main()
