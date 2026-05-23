"""
ATC Datalink Backend - Main Application
Connects to TCP server and stores messages in MySQL database
"""

import logging
from logging.handlers import RotatingFileHandler
import configparser
import sys
import signal
import time
from pathlib import Path

from database_handler import DatabaseHandler
from tcp_client import TCPListener
from sse_server import SSEServer
from decode_handler import DecodeHandler
from acars_app_api import AcarsAppApi

# Configure logging - will be reconfigured after loading config
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
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
        self.tcp_client = None
        self.sse_server = None
        self.decode_handler = None
        self.acars_app_api = None
        self._sec = {}
        self.running = False
        
    def load_config(self):
        """Load configuration from INI file"""
        try:
            if not Path(self.config_file).exists():
                logger.error(f"Configuration file not found: {self.config_file}")
                return False
            
            self.config = configparser.ConfigParser()
            self.config.read(self.config_file)
            
            # Reconfigure logging with rotating file handler
            self._setup_logging()
            
            logger.info(f"Configuration loaded from {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False
    
    def _setup_logging(self):
        """Setup logging with rotating file handler based on config"""
        try:
            # Get logging config
            max_log_size_mb = self.config.getint('LOGGING', 'max_log_size_mb', fallback=10)
            backup_count = self.config.getint('LOGGING', 'backup_count', fallback=3)
            
            # Convert MB to bytes
            max_bytes = max_log_size_mb * 1024 * 1024
            
            # Create rotating file handler
            file_handler = RotatingFileHandler(
                'atc_datalink.log',
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.INFO)
            file_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
            
            # Add file handler to root logger
            root_logger = logging.getLogger()
            root_logger.addHandler(file_handler)
            
            logger.info(f"Logging configured: max_size={max_log_size_mb}MB, backups={backup_count}")
            
        except Exception as e:
            logger.warning(f"Error setting up logging config, using defaults: {e}")
    
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
                max_history_messages=100,  # Backend'de saklanacak history sayısı
                decode_handler=self.decode_handler,  # Decode handler'i geç
                **self._sec,
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
    
    def initialize_decode_handler(self):
        """Initialize ACARS message decoder"""
        try:
            # Check if decoding is enabled in config
            decoding_enabled = self.config.getboolean('DECODING', 'enabled', fallback=True)
            
            if not decoding_enabled:
                logger.info("Decoding disabled in config")
                self.decode_handler = None
                return True
            
            # Create decode handler
            self.decode_handler = DecodeHandler()
            
            if self.decode_handler.initialized:
                logger.info("Decode handler initialized successfully")
            else:
                logger.warning("Decode handler not initialized - decoding disabled")
            
            return True
            
        except Exception as e:
            logger.error(f"Error initializing decode handler: {e}")
            return False
    
    def _load_security_config(self):
        """Read [SECURITY] settings and return kwargs for server constructors.

        Returns an empty dict (auth disabled) when the section is missing,
        explicitly disabled, or no auth material is configured.
        """
        if not self.config.has_section('SECURITY'):
            logger.info("SECURITY section not in config; auth disabled")
            return {}
        if not self.config.getboolean('SECURITY', 'enabled', fallback=False):
            logger.info("Auth disabled by config")
            return {}
        from auth_helper import parse_api_keys
        api_keys = parse_api_keys(
            self.config.get('SECURITY', 'api_keys', fallback='')
        )
        jwt_secret = self.config.get('SECURITY', 'jwt_secret', fallback='') or None
        jwt_cookie_name = self.config.get(
            'SECURITY', 'jwt_cookie_name', fallback='datalink_session'
        )
        if not api_keys and not jwt_secret:
            logger.warning(
                "[SECURITY] enabled but no api_keys or jwt_secret; auth effectively disabled"
            )
            return {}
        logger.info(
            f"Auth enabled ({len(api_keys)} static keys, "
            f"jwt_secret={'set' if jwt_secret else 'unset'}, "
            f"cookie={jwt_cookie_name})"
        )
        return {
            'api_keys': api_keys,
            'jwt_secret': jwt_secret,
            'jwt_cookie_name': jwt_cookie_name,
        }

    def initialize_acars_app_api(self):
        """Initialize the ACARS Application API (optional, external-facing).

        Auth here is limited to the static X-API-Key (no JWT cookie); browsers
        do not call this module.
        """
        try:
            if not self.config.has_section('ACARS_APP_API'):
                logger.info("ACARS_APP_API section not in config; module disabled")
                self.acars_app_api = None
                return True

            enabled = self.config.getboolean('ACARS_APP_API', 'enabled', fallback=False)
            if not enabled:
                logger.info("ACARS Application API disabled by config")
                self.acars_app_api = None
                return True

            host = self.config.get('ACARS_APP_API', 'host', fallback='0.0.0.0')
            port = self.config.getint('ACARS_APP_API', 'port', fallback=10012)
            max_per_type = self.config.getint(
                'ACARS_APP_API', 'max_count_per_type', fallback=5
            )

            self.acars_app_api = AcarsAppApi(
                db_handler=self.db_handler,
                host=host,
                port=port,
                max_count_per_type=max_per_type,
                api_keys=self._sec.get('api_keys'),
            )

            if not self.acars_app_api.start():
                logger.error("Failed to start ACARS Application API")
                return False

            logger.info("ACARS Application API initialized successfully")
            return True

        except Exception as e:
            logger.error(f"Error initializing ACARS Application API: {e}")
            return False

    def initialize_tcp_client(self):
        """Initialize TCP client for receiving messages"""
        try:
            # Get listener configuration
            listener_host = self.config.get('LISTENER', 'host')
            listener_port = self.config.getint('LISTENER', 'port')
            max_idle_time = self.config.getint('LISTENER', 'max_idle_time', fallback=600)
            
            logger.info(f"Initializing TCP client for {listener_host}:{listener_port}")
            logger.info(f"TCP idle timeout: {max_idle_time}s")
            
            # Create TCP client
            self.tcp_client = TCPListener(
                host=listener_host,
                port=listener_port,
                message_callback=self.on_message_received,
                max_idle_time=max_idle_time
            )
            
            # Start client
            if not self.tcp_client.start():
                logger.error("Failed to start TCP client")
                return False
            
            # Set TCP status callback for SSE health endpoint (after TCP client is created)
            if hasattr(self, 'sse_server') and self.sse_server:
                self.sse_server.tcp_status_callback = lambda: 'connected' if self.tcp_client.is_connected() else 'disconnected'
                logger.info("TCP status callback set for SSE health endpoint")
            
            logger.info("TCP client initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing TCP client: {e}")
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
            
            # Decode message if possible
            try:
                if self.decode_handler and self.decode_handler.initialized:
                    json_data = self.decode_handler.process_message(json_data)
            except Exception as decode_error:
                logger.error(f"Decode exception: {decode_error}")
            
            # Store message in database with error handling
            try:
                db_success = self.db_handler.insert_message(source_ip, source_port, raw_data, json_data)
                if not db_success:
                    logger.error("Database insert failed")
            except Exception as db_error:
                logger.error(f"Database insert exception: {db_error}")
                import traceback
                logger.error(f"DB traceback:\n{traceback.format_exc()}")
            
            # Broadcast to frontend via SSE with error handling
            try:
                if self.sse_server:
                    self.sse_server.broadcast_message(json_data)
                else:
                    logger.warning("SSE server is None, cannot broadcast")
            except Exception as sse_error:
                logger.error(f"SSE broadcast exception: {sse_error}")
                import traceback
                logger.error(f"SSE traceback:\n{traceback.format_exc()}")
            
        except Exception as e:
            logger.error(f"Error handling received message: {e}")
            import traceback
            logger.error(f"Handler traceback:\n{traceback.format_exc()}")
    
    def start(self):
        """Start the ATC Datalink Backend"""
        logger.info("=" * 60)
        logger.info("Starting ATC Datalink Backend")
        logger.info("=" * 60)
        
        # Load configuration
        if not self.load_config():
            logger.error("Failed to load configuration")
            return False

        # Load security/auth config once; both servers get the same kwargs.
        self._sec = self._load_security_config()

        # Initialize database
        if not self.initialize_database():
            logger.error("Failed to initialize database")
            return False
        
        # Initialize decode handler
        if not self.initialize_decode_handler():
            logger.error("Failed to initialize decode handler")
            return False
        
        # Initialize SSE server
        if not self.initialize_sse_server():
            logger.error("Failed to initialize SSE server")
            return False

        # Initialize ACARS Application API (optional)
        if not self.initialize_acars_app_api():
            logger.error("Failed to initialize ACARS Application API")
            return False

        # Initialize TCP client
        if not self.initialize_tcp_client():
            logger.error("Failed to initialize TCP client")
            return False
        
        self.running = True
        logger.info("ATC Datalink Backend started successfully")
        logger.info("=" * 60)
        
        # Keep the application running
        try:
            last_stats_log = 0
            while self.running:
                time.sleep(1)
                
                current_time = time.time()
                
                # Periodically log statistics
                if int(current_time) % 60 == 0 and int(current_time) != last_stats_log:  # Every minute
                    last_stats_log = int(current_time)
                    
                    count = self.db_handler.get_message_count()
                    client_count = self.sse_server.get_client_count() if self.sse_server else 0
                    
                    # Get TCP client stats
                    if self.tcp_client:
                        stats = self.tcp_client.get_stats()
                        conn_status = 'CONNECTED' if stats['connected'] else 'DISCONNECTED'
                        idle_sec = int(stats.get('idle_seconds', 0))
                        conn_count = stats.get('connection_count', 0)
                        
                        logger.info(
                            f"Stats - TCP: {conn_status} (idle:{idle_sec}s, reconn:{conn_count}), "
                            f"Msgs: {stats['total_messages']}, DB: {count}, SSE: {client_count}, "
                            f"Thread: {'alive' if stats['thread_alive'] else 'DEAD'}"
                        )
                        
                        # Thread ölmüşse kritik uyarı
                        if not stats['thread_alive']:
                            logger.critical("TCP RECEIVER THREAD IS DEAD! Watchdog should restart it.")
                    else:
                        logger.info(f"Total messages in database: {count}, SSE clients: {client_count}")
                    
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
        
        return True
    
    def stop(self):
        """Stop the ATC Datalink Backend"""
        logger.info("Stopping ATC Datalink Backend...")
        self.running = False
        
        # Stop TCP client
        if self.tcp_client:
            self.tcp_client.stop()
        
        # Stop SSE server
        if self.sse_server:
            self.sse_server.stop()

        # Stop ACARS Application API
        if self.acars_app_api:
            self.acars_app_api.stop()

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
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        try:
            app.stop()
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")


if __name__ == '__main__':
    main()
