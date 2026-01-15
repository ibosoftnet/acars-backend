"""
TCP Client Module - Robust Implementation
Connects to TCP server and receives JSON data with watchdog monitoring
"""

import socket
import logging
import json
import re
import time
import select
from threading import Thread, Event, Lock

logger = logging.getLogger(__name__)


class TCPListener:
    """
    Robust TCP client with automatic reconnection and health monitoring.
    Uses select() for non-blocking I/O and watchdog for connection health.
    """
    
    def __init__(self, host, port, message_callback, max_idle_time=600):
        """
        Initialize TCP client
        
        Args:
            host (str): Server IP address to connect to
            port (int): Server port to connect to
            message_callback (callable): Function to call when message is received
            max_idle_time (int): Maximum idle time in seconds before reconnect (default: 600)
        """
        self.host = host
        self.port = port
        self.message_callback = message_callback
        
        # Connection state
        self.client_socket = None
        self.connected = False
        self.socket_lock = Lock()
        
        # Threading
        self.running = Event()
        self.receiver_thread = None
        self.watchdog_thread = None
        
        # Statistics
        self.total_messages_received = 0
        self.last_message_time = None
        self.last_data_time = None  # Any data received (for watchdog)
        self.connection_count = 0
        self.error_count = 0
        
        # Configuration
        self.watchdog_interval = 60  # Check every 60 seconds
        self.max_idle_time = max_idle_time  # Configurable idle timeout
        self.reconnect_delay = 5  # 5 seconds between reconnect attempts
        
    def start(self):
        """Start the TCP client"""
        if self.receiver_thread and self.receiver_thread.is_alive():
            logger.warning("TCP client is already running")
            return False
        
        try:
            logger.info(f"Starting TCP client for {self.host}:{self.port}")
            
            self.running.set()
            
            # Start receiver thread
            self.receiver_thread = Thread(target=self._receiver_loop, name="TCP-Receiver", daemon=True)
            self.receiver_thread.start()
            
            # Start watchdog thread
            self.watchdog_thread = Thread(target=self._watchdog_loop, name="TCP-Watchdog", daemon=True)
            self.watchdog_thread.start()
            
            logger.info("TCP client started successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error starting TCP client: {e}")
            return False
    
    def stop(self):
        """Stop the TCP client"""
        logger.info("Stopping TCP client...")
        self.running.clear()
        
        # Close socket to unblock recv
        self._close_socket()
        
        # Wait for threads
        if self.receiver_thread:
            self.receiver_thread.join(timeout=5.0)
        if self.watchdog_thread:
            self.watchdog_thread.join(timeout=2.0)
            
        logger.info(f"TCP client stopped (total messages: {self.total_messages_received})")
    
    def _connect(self):
        """Establish TCP connection"""
        with self.socket_lock:
            # Close existing socket if any
            if self.client_socket:
                try:
                    self.client_socket.close()
                except:
                    pass
                self.client_socket = None
                self.connected = False
            
            try:
                # Create new socket
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
                
                # Set TCP keepalive parameters (Windows)
                try:
                    sock.ioctl(socket.SIO_KEEPALIVE_VALS, (1, 30000, 5000))  # Enable, 30s idle, 5s interval
                except (AttributeError, OSError):
                    pass  # Not available on all platforms
                
                # CRITICAL: Use non-blocking connect with select() to guarantee timeout works
                sock.setblocking(False)
                
                # Attempt connection (will return immediately with EINPROGRESS/EWOULDBLOCK)
                try:
                    sock.connect((self.host, self.port))
                except (BlockingIOError, socket.error) as e:
                    # Expected: connection in progress
                    if e.errno not in (10035, 115):  # WSAEWOULDBLOCK on Windows, EINPROGRESS on Linux
                        raise
                
                # Wait for connection to complete with timeout using select()
                logger.debug(f"Waiting for connection to complete (10s timeout)...")
                _, writable, exceptional = select.select([], [sock], [sock], 10.0)
                
                if exceptional:
                    raise socket.error("Connection failed (exceptional condition)")
                
                if not writable:
                    raise socket.timeout("Connection timeout after 10 seconds")
                
                # Verify connection succeeded
                err = sock.getsockopt(socket.SOL_SOCKET, socket.SO_ERROR)
                if err != 0:
                    raise socket.error(f"Connection failed with error code {err}")
                
                self.client_socket = sock
                self.connected = True
                self.connection_count += 1
                self.last_data_time = time.time()
                
                logger.info(f"Connected to {self.host}:{self.port} (connection #{self.connection_count})")
                return True
                
            except Exception as e:
                logger.error(f"Connection failed: {e}")
                self.error_count += 1
                return False
    
    def _close_socket(self):
        """Safely close socket"""
        # Set connected to False FIRST (outside lock) so receiver loop sees it immediately
        was_connected = self.connected
        self.connected = False
        
        with self.socket_lock:
            if self.client_socket:
                try:
                    # Shutdown will wake up any blocking recv/select calls
                    self.client_socket.shutdown(socket.SHUT_RDWR)
                except Exception as e:
                    logger.debug(f"Socket shutdown exception (expected): {e}")
                try:
                    self.client_socket.close()
                except Exception as e:
                    logger.debug(f"Socket close exception: {e}")
                self.client_socket = None
        
        if was_connected:
            logger.info("Socket closed and connected flag set to False")
    
    def _receiver_loop(self):
        """Main receiver loop with automatic reconnection - BULLETPROOF VERSION"""
        logger.info("Receiver thread started")
        buffer = ""
        last_heartbeat = time.time()
        iteration = 0
        
        while self.running.is_set():
            iteration += 1
            
            # Heartbeat every 10 seconds to prove thread is alive
            if time.time() - last_heartbeat > 10:
                logger.info(f"[HEARTBEAT] Receiver loop alive, iteration #{iteration}")
                last_heartbeat = time.time()
            
            # ============ CONNECTION PHASE ============
            # CRITICAL: Check connection flag FIRST before touching socket
            if not self.connected:
                logger.info(f"[RECONNECT] Disconnected (flag=False), attempting to connect to {self.host}:{self.port}...")
                
                try:
                    success = self._connect()
                    if not success:
                        logger.warning(f"[RECONNECT] Failed (error count: {self.error_count}), retry in {self.reconnect_delay}s")
                        time.sleep(self.reconnect_delay)
                        continue
                    
                    logger.info(f"[RECONNECT] SUCCESS! Connected to {self.host}:{self.port}")
                    buffer = ""  # Clear buffer on reconnect
                    continue  # Go back to start
                    
                except Exception as e:
                    logger.error(f"[RECONNECT] Exception during connect: {e}", exc_info=True)
                    self.connected = False
                    time.sleep(self.reconnect_delay)
                    continue
            
            # Get socket ONLY after confirming connected=True
            with self.socket_lock:
                sock = self.client_socket
            
            if not sock:
                logger.error("[FATAL] Socket is None despite connected=True!")
                self.connected = False
                continue
            
            # ============ SELECT PHASE ============
            # Wait for socket to become readable with 1s timeout
            try:
                readable, _, exceptional = select.select([sock], [], [sock], 1.0)
            except Exception as e:
                logger.warning(f"[SELECT] Failed (socket closed): {e}")
                self._close_socket()
                continue
            
            # CRITICAL: Re-check connected flag after select (watchdog may have closed socket)
            if not self.connected:
                logger.info("[SELECT] Connection closed by watchdog during select")
                continue
            
            # Handle exceptional condition
            if exceptional:
                logger.warning("[SELECT] Socket in exceptional condition")
                self._close_socket()
                continue
            
            # If timeout (no data), loop back to check connected flag again
            if not readable:
                continue
            
            # ============ RECEIVE PHASE ============
            # Socket is readable, try to receive data
            try:
                data = sock.recv(8192)
            except Exception as e:
                logger.error(f"[RECV] Socket error: {e}")
                self._close_socket()
                continue
            
            # Empty data means connection closed by remote
            if not data:
                logger.warning("[RECV] Connection closed by remote (empty recv)")
                self._close_socket()
                continue
            
            # ============ PROCESSING PHASE ============
            # Update timestamp and process data
            self.last_data_time = time.time()
            
            try:
                buffer += data.decode('ascii', errors='ignore')
            except Exception as e:
                logger.error(f"[DECODE] Error: {e}")
                continue
            
            # Process complete lines
            while '\n' in buffer:
                try:
                    line, buffer = buffer.split('\n', 1)
                    line = line.strip()
                    if line:
                        self._process_line(line)
                except Exception as e:
                    logger.error(f"[PROCESS] Line processing error: {e}")
                    break  # Break out of line processing, not main loop
            
            # Prevent buffer overflow
            if len(buffer) > 100000:
                logger.warning("[BUFFER] Overflow detected, trimming to 10KB")
                buffer = buffer[-10000:]
        
        logger.info("Receiver thread stopped gracefully")
    
    def _watchdog_loop(self):
        """Watchdog thread to detect stuck connections"""
        logger.info("Watchdog thread started")
        
        while self.running.is_set():
            time.sleep(self.watchdog_interval)
            
            if not self.running.is_set():
                break
            
            # Active connection health check
            if self.connected:
                with self.socket_lock:
                    sock = self.client_socket
                    
                    if sock:
                        try:
                            # Try to get peer name - if connection is broken, this will fail
                            sock.getpeername()
                            
                            # Also check idle time
                            if self.last_data_time:
                                idle_time = time.time() - self.last_data_time
                                
                                if idle_time > self.max_idle_time:
                                    logger.warning(f"No data for {idle_time:.0f}s, forcing reconnect (watchdog)")
                                    self._close_socket()
                                    logger.info(f"Watchdog: Socket closed, connected={self.connected}, will reconnect")
                                elif idle_time > 120:  # Log if idle more than 2 minutes
                                    logger.debug(f"Connection idle for {idle_time:.0f}s")
                        except (OSError, socket.error) as e:
                            # Socket is broken
                            logger.warning(f"Socket health check failed: {e} - forcing reconnect")
                            self._close_socket()
                    else:
                        # Socket is None but connected is True - inconsistent state
                        logger.warning("Connected flag is True but socket is None - fixing state")
                        self.connected = False
            
            # Check if receiver thread is alive
            if not self.receiver_thread or not self.receiver_thread.is_alive():
                logger.critical("Receiver thread is dead!")
                # Try to restart receiver thread
                if self.running.is_set():
                    logger.info("Attempting to restart receiver thread...")
                    self.receiver_thread = Thread(target=self._receiver_loop, name="TCP-Receiver", daemon=True)
                    self.receiver_thread.start()
        
        logger.info("Watchdog thread stopped")
    
    def _process_line(self, line):
        """Process a single line of data"""
        try:
            json_data = self._extract_json(line)
            
            if json_data:
                self.total_messages_received += 1
                self.last_message_time = time.time()
                
                if self.message_callback:
                    try:
                        self.message_callback(self.host, self.port, line, json_data)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
            else:
                # Log non-JSON data for debugging (only if it seems meaningful)
                if len(line) > 5:
                    if len(line) > 100:
                        logger.debug(f"Non-JSON data: {line[:100]}...")
                    else:
                        logger.debug(f"Non-JSON data: {line}")
                    
        except Exception as e:
            logger.error(f"Process error: {e}")
    
    def _extract_json(self, raw_data):
        """Extract JSON object from raw data"""
        try:
            # Try direct JSON parse first (fastest)
            return json.loads(raw_data)
        except json.JSONDecodeError:
            pass
        
        try:
            # Look for JSON pattern
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, raw_data)
            
            for match in matches:
                try:
                    return json.loads(match)
                except json.JSONDecodeError:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"JSON extraction error: {e}")
            return None
    
    def is_running(self):
        """Check if client is running"""
        return self.running.is_set()
    
    def is_thread_alive(self):
        """Check if receiver thread is alive"""
        return self.receiver_thread is not None and self.receiver_thread.is_alive()
    
    def is_connected(self):
        """Check if connected to server"""
        # Simple but reliable: check the flag that we manage internally
        return self.connected and self.client_socket is not None
    
    def get_stats(self):
        """Get client statistics"""
        idle_time = 0
        if self.last_data_time:
            idle_time = time.time() - self.last_data_time
            
        return {
            'running': self.running.is_set(),
            'connected': self.connected,
            'thread_alive': self.is_thread_alive(),
            'total_messages': self.total_messages_received,
            'last_message_time': self.last_message_time,
            'last_data_time': self.last_data_time,
            'idle_seconds': idle_time,
            'connection_count': self.connection_count,
            'error_count': self.error_count
        }
    
    def force_reconnect(self):
        """Force a reconnection (can be called externally)"""
        logger.info("Force reconnect requested")
        self._close_socket()
