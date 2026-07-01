"""
Database Handler Module
Manages MySQL database connections and operations for ATC Datalink Backend
Persistent MariaDB handler with self-recovery and auto-reconnect for long-term uptime
"""

import mysql.connector
from mysql.connector import Error
from mysql.connector import pooling
import logging
from datetime import datetime
import json
import time

logger = logging.getLogger(__name__)


class DatabaseHandler:
    """Persistent MariaDB handler with self-recovery and auto-reconnect"""
    
    def __init__(self, host, port, user, password, database, max_messages,
                 read_pool_size=8):
        """
        Initialize database handler

        Args:
            host (str): Database host address
            port (int): Database port
            user (str): Database username
            password (str): Database password
            database (str): Database name
            max_messages (int): Maximum number of messages to retain
            read_pool_size (int): Size of the separate connection pool used for
                read queries (API + stats). Keeps concurrent readers off the
                single writer connection, which is not thread-safe.
        """
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
        self.max_messages = max_messages
        self.read_pool_size = max(1, int(read_pool_size))
        # Writer connection — used ONLY by the single TCP receiver thread
        # (insert_message / _cleanup_old_messages). Single-threaded, so no lock.
        self.connection = None
        # Read pool — used by all reader threads (API queries, stats count).
        # mysql-connector connections are not thread-safe, so readers must never
        # share the writer connection.
        self.read_pool = None
        self.consecutive_failures = 0
        self.last_ping = 0
        self.ping_interval = 30  # saniye — her 30 saniyede bir kontrol (timeout'u önler)
        self.insert_count = 0  # Cleanup için mesaj sayacı

    def _connection_kwargs(self):
        """Shared connection kwargs for both the writer connection and pool."""
        return dict(
            host=self.host,
            port=self.port,
            user=self.user,
            password=self.password,
            database=self.database,
            autocommit=True,
            connection_timeout=30,
            use_pure=True,       # C extension yerine pure Python
            ssl_disabled=True,   # SSL devre dışı
        )

    def init_read_pool(self):
        """Create the read connection pool (idempotent). Call after connect()."""
        if self.read_pool is not None:
            return True
        try:
            self.read_pool = pooling.MySQLConnectionPool(
                pool_name='atc_read_pool',
                pool_size=self.read_pool_size,
                pool_reset_session=True,
                **self._connection_kwargs(),
            )
            logger.info(
                f"Read connection pool created (size={self.read_pool_size})"
            )
            return True
        except Error as e:
            logger.error(f"Failed to create read pool: {e}")
            self.read_pool = None
            return False

    def execute_read(self, sql, params=None):
        """Run a read query on a pooled connection and return all rows.

        Isolated from the writer connection so concurrent API/stats reads never
        corrupt the TCP receiver's insert path. Retries once on a stale pooled
        connection.
        """
        if self.read_pool is None and not self.init_read_pool():
            raise Error("Read pool is not available")

        last_err = None
        for attempt in range(2):
            conn = None
            cursor = None
            try:
                conn = self.read_pool.get_connection()
                # Pooled connections can go stale (wait_timeout); refresh.
                try:
                    conn.ping(reconnect=True, attempts=2, delay=1)
                except Error:
                    pass
                cursor = conn.cursor()
                cursor.execute(sql, params or ())
                return cursor.fetchall()
            except (mysql.connector.InterfaceError,
                    mysql.connector.OperationalError) as e:
                # Stale/broken pooled connection — retry once with a fresh one.
                last_err = e
                logger.warning(
                    f"Read query failed (attempt {attempt + 1}/2): {e}"
                )
                continue
            finally:
                if cursor:
                    try:
                        cursor.close()
                    except Exception:
                        pass
                if conn:
                    try:
                        conn.close()  # returns the connection to the pool
                    except Exception:
                        pass
        raise last_err if last_err else Error("Read query failed")
    
    def _safe_is_connected(self):
        """Güvenli bağlantı kontrolü - IndexError'dan korunur"""
        try:
            if not self.connection:
                return False
            return self.connection.is_connected()
        except (Error, IndexError, AttributeError) as e:
            logger.debug(f"Connection check failed: {e}")
            return False
    
    def _get_cursor(self):
        """Güvenli cursor alma - Bağlantı sorununda otomatik reconnect"""
        if not self._ensure_connection():
            raise Error("Cannot establish database connection")
        
        try:
            return self.connection.cursor()
        except (IndexError, Error, AttributeError) as e:
            # cursor() içindeki is_connected() IndexError fırlatabilir
            logger.warning(f"Cursor creation failed: {e}, attempting reconnect...")
            self.connection = None
            if not self.connect():
                raise Error("Reconnection failed after cursor error")
            return self.connection.cursor()
        
    def connect(self):
        """Bağlantıyı sıfırdan kur - Pool kullanmadan manuel yönetim"""
        max_attempts = 3
        attempt = 0
        
        while attempt < max_attempts:
            try:
                # Eğer bağlantı zaten varsa ve aktifse, tekrar kurma
                if self.connection and self._safe_is_connected():
                    return True

                # Yeni bağlantı kur
                self.connection = mysql.connector.connect(
                    **self._connection_kwargs()
                )

                if self.connection.is_connected():
                    self.consecutive_failures = 0
                    logger.info(f"Successfully connected to MariaDB: {self.database}")
                    # Okuma havuzunu ilk başarılı bağlantıda kur (idempotent).
                    self.init_read_pool()
                    return True
                    
            except Error as e:
                attempt += 1
                logger.error(f"MariaDB connection error (attempt {attempt}/{max_attempts}): {e}")
                self.connection = None
                
                if attempt < max_attempts:
                    time.sleep(2)  # Tekrar denemeden önce 2 saniye bekle
        
        # Tüm denemeler başarısız oldu
        self.consecutive_failures += 1
        return False
    
    def _ensure_connection(self):
        """Bağlantıyı test et, bozuksa yeniden kur - Düzenli ping ile sağlık kontrolü"""
        now = time.time()
        
        # Her 30 saniyede bir ping at (uzun süre boş kalsa bile bağlantıyı taze tut)
        if now - self.last_ping > self.ping_interval:
            try:
                if self.connection and self._safe_is_connected():
                    self.connection.ping(reconnect=True, attempts=2, delay=2)
                    self.last_ping = now
                    logger.debug("Connection ping successful")
                else:
                    raise Exception("Connection not active")
            except Exception as e:
                logger.warning(f"Connection check failed: {e}")
                self.connection = None
                time.sleep(2)
                if self.connect():
                    logger.info("Reconnection successful after ping failure")
                    self.last_ping = now
            
        # Eğer bağlantı halen yoksa veya aktif değilse tekrar kurmayı dene
        if not self.connection or not self._safe_is_connected():
            logger.warning("Connection not active, attempting reconnect...")
            
            # Çok fazla başarısız deneme varsa bekle
            if self.consecutive_failures >= 3:
                wait_time = min(30, 5 + (self.consecutive_failures - 3) * 2)
                logger.info(f"Too many consecutive failures ({self.consecutive_failures}), waiting {wait_time} seconds...")
                time.sleep(wait_time)
            
            return self.connect()
        
        return True
    
    def create_database_if_not_exists(self):
        """Create database if it doesn't exist"""
        temp_connection = None
        cursor = None
        try:
            # Connect without specifying database
            temp_connection = mysql.connector.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password
            )
            cursor = temp_connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")
            logger.info(f"Database '{self.database}' created or already exists")
            return True
        except Error as e:
            logger.error(f"Error creating database: {e}")
            return False
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
            if temp_connection:
                try:
                    if temp_connection.is_connected():
                        temp_connection.close()
                except:
                    pass
    
    def create_table_if_not_exists(self):
        """Create messages_json_raw table if it doesn't exist"""
        if not self._ensure_connection():
            logger.error("Database connection is not established")
            return False
        
        cursor = None
        try:
            cursor = self._get_cursor()
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
                INDEX idx_app_name (app_name),
                INDEX idx_label_ts (label, timestamp_msg),
                INDEX idx_timestamp_msg (timestamp_msg)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
            try:
                cursor.execute(create_table_query)
            except (IndexError, AttributeError) as ie:
                logger.error(f"Create table query failed (corrupt packet): {ie}")
                self.connection = None
                return False
            # autocommit=True olduğu için commit'e gerek yok
            logger.info("Table 'messages_json_raw' created or already exists")
            return True
        except Error as e:
            logger.error(f"Error creating table: {e}")
            self.connection = None
            return False
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
    
    def ensure_indexes(self):
        """Ensure the targeted read indexes exist on messages_json_raw.

        Added for existing installs where the table predates these indexes.
        MySQL has no `CREATE INDEX IF NOT EXISTS`, so existence is checked via
        information_schema first. On a large table the ALTER may take a few
        seconds the first time; subsequent startups find the index and skip.

        - idx_label_ts (label, timestamp_msg): narrows D-ATIS queries to A9 rows
          in timestamp order (no full scan / filesort; REGEXP runs on the small
          candidate set).
        - idx_timestamp_msg (timestamp_msg): serves the history page's time-range
          filter + ORDER BY timestamp_msg DESC.
        """
        wanted = {
            'idx_label_ts': 'ALTER TABLE messages_json_raw '
                            'ADD INDEX idx_label_ts (label, timestamp_msg)',
            'idx_timestamp_msg': 'ALTER TABLE messages_json_raw '
                                 'ADD INDEX idx_timestamp_msg (timestamp_msg)',
        }
        if not self._ensure_connection():
            logger.error("Cannot ensure indexes: no database connection")
            return False

        cursor = None
        try:
            cursor = self._get_cursor()
            cursor.execute(
                "SELECT DISTINCT index_name FROM information_schema.statistics "
                "WHERE table_schema = %s AND table_name = 'messages_json_raw'",
                (self.database,),
            )
            existing = {row[0] for row in cursor.fetchall()}

            for name, ddl in wanted.items():
                if name in existing:
                    logger.info(f"Index {name} already exists")
                    continue
                try:
                    logger.info(f"Creating index {name} (may take a moment)...")
                    cursor.execute(ddl)
                    logger.info(f"Index {name} created")
                except Error as e:
                    logger.error(f"Failed to create index {name}: {e}")
            return True
        except Error as e:
            logger.error(f"Error ensuring indexes: {e}")
            self.connection = None
            return False
        finally:
            if cursor:
                try:
                    cursor.close()
                except Exception:
                    pass

    def insert_message(self, source_ip, source_port, raw_data, json_data):
        """
        Insert a new message into the database
        
        Args:
            source_ip (str): Source IP address
            source_port (int): Source port
            raw_data (str): Raw message data (not used anymore, kept for compatibility)
            json_data (dict): Parsed JSON data
        """
        # Her mesajda bağlantıyı kontrol et (MySQL wait_timeout sorununu önler)
        if not self._ensure_connection():
            logger.error("Database connection is not established - attempting force reconnect")
            # Force reconnect
            self.connection = None
            if not self.connect():
                logger.error("Force reconnect failed")
                return False
        
        cursor = None
        try:
            cursor = self._get_cursor()
            
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
            
            # Handle ack field - convert to boolean
            ack_value = json_data.get('ack', False)
            if isinstance(ack_value, bool):
                ack = ack_value
            elif isinstance(ack_value, str):
                # If string, check if it's a truthy value (non-empty string means True)
                ack = bool(ack_value)
            else:
                ack = bool(ack_value)
            
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
            
            params = (
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
            )
            
            # Execute with IndexError protection and retry
            try:
                cursor.execute(insert_query, params)
            except (IndexError, AttributeError) as ie:
                # Corrupt packet - force reconnect and retry once
                logger.warning(f"Insert query failed (corrupt packet): {ie}, retrying...")
                self.connection = None
                cursor.close()
                
                # Retry once with fresh connection
                if not self.connect():
                    logger.error("Failed to reconnect for retry")
                    return False
                
                cursor = self._get_cursor()
                try:
                    cursor.execute(insert_query, params)
                except (IndexError, AttributeError, Error) as retry_err:
                    logger.error(f"Insert retry also failed: {retry_err}")
                    self.connection = None
                    return False
            
            # autocommit=True olduğu için commit'e gerek yok
            message_id = cursor.lastrowid
            
            # Mesaj sayacını artır
            self.insert_count += 1
            
            # Clean up old messages if limit exceeded - her 100 mesajda bir
            if self.insert_count % 100 == 0:
                try:
                    self._cleanup_old_messages()
                    logger.info(f"Periodic cleanup after {self.insert_count} inserts")
                except Exception as cleanup_err:
                    logger.debug(f"Cleanup failed (non-critical): {cleanup_err}")
            
            logger.debug(f"Inserted message ID: {message_id}")
            self.consecutive_failures = 0  # Başarılı işlemde sıfırla
            return True
            
        except Error as e:
            logger.error(f"Error inserting message: {e}")
            self.consecutive_failures += 1
            self.connection = None  # Hata durumunda bağlantıyı sıfırla
            return False
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
    
    def _cleanup_old_messages(self):
        """Remove old messages if count exceeds max_messages limit"""
        if not self._safe_is_connected():
            return
        
        cursor = None
        try:
            cursor = self._get_cursor()
            
            # Count total messages - IndexError'dan korun
            try:
                cursor.execute("SELECT COUNT(*) FROM messages_json_raw")
                count = cursor.fetchone()[0]
            except (IndexError, AttributeError) as ie:
                logger.warning(f"Cleanup count query failed (corrupt packet): {ie}")
                self.connection = None
                return  # Sessizce çık, kritik değil
            
            if count > self.max_messages:
                # Delete oldest messages
                messages_to_delete = count - self.max_messages
                delete_query = """
                DELETE FROM messages_json_raw 
                ORDER BY received_at ASC 
                LIMIT %s
                """
                try:
                    cursor.execute(delete_query, (messages_to_delete,))
                    # autocommit=True olduğu için commit'e gerek yok
                    logger.info(f"Cleaned up {messages_to_delete} old messages")
                except (IndexError, AttributeError) as ie:
                    logger.warning(f"Cleanup delete query failed (corrupt packet): {ie}")
                    self.connection = None
            
        except Error as e:
            logger.error(f"Error cleaning up old messages: {e}")
            self.connection = None
        finally:
            if cursor:
                try:
                    cursor.close()
                except:
                    pass
    
    def get_message_count(self):
        """Get total count of messages in database.

        Runs on the read pool (called from the main stats thread) so it never
        touches the TCP receiver's writer connection.
        """
        try:
            rows = self.execute_read("SELECT COUNT(*) FROM messages_json_raw")
            return rows[0][0] if rows else 0
        except Error as e:
            logger.error(f"Error getting message count: {e}")
            return 0
    
    def close(self):
        """Close database connection"""
        try:
            if self.connection and self._safe_is_connected():
                self.connection.close()
                logger.info("Database connection closed")
        except Exception as e:
            logger.debug(f"Error closing connection: {e}")
