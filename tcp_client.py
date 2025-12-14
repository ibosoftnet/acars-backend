"""
TCP Client Module
Connects to TCP server and receives JSON data
"""

import socket
import logging
import json
import re
import time
from threading import Thread, Event

logger = logging.getLogger(__name__)


class TCPListener:
    """Handles TCP client connection and message parsing"""
    
    def __init__(self, host, port, message_callback):
        """
        Initialize TCP client
        
        Args:
            host (str): Server IP address to connect to
            port (int): Server port to connect to
            message_callback (callable): Function to call when message is received
                                       Signature: callback(source_ip, source_port, raw_data, json_data)
        """
        self.host = host
        self.port = port
        self.message_callback = message_callback
        self.client_socket = None
        self.running = Event()
        self.thread = None
        self.last_message_time = None
        self.total_messages_received = 0
        
    def start(self):
        """Start the TCP client in a separate thread"""
        if self.thread and self.thread.is_alive():
            logger.warning("TCP client is already running")
            return False
        
        try:
            logger.info(f"TCP client will connect to {self.host}:{self.port}")
            
            # Start client thread
            self.running.set()
            self.thread = Thread(target=self._listen, daemon=True)
            self.thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting TCP client: {e}")
            return False
    
    def stop(self):
        """Stop the TCP client"""
        logger.info("Stopping TCP client...")
        self.running.clear()
        
        if self.thread:
            self.thread.join(timeout=3.0)
        
        if self.client_socket:
            try:
                self.client_socket.close()
            except:
                pass
            
        logger.info("TCP client stopped")
    
    def _listen(self):
        """Main client loop: connect to server and receive data"""
        logger.info("TCP client thread started")
        reconnect_delay = 5
        
        while self.running.is_set():
            try:
                # Connect to server
                logger.info(f"Connecting to TCP server {self.host}:{self.port}...")
                self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.client_socket.connect((self.host, self.port))
                logger.info(f"Connected to TCP server {self.host}:{self.port}")
                
                # Receive data
                buffer = ""
                self.client_socket.settimeout(300.0)  # 5 minute timeout
                
                while self.running.is_set():
                    try:
                        data = self.client_socket.recv(4096)
                        
                        if not data:
                            logger.warning("Connection closed by server")
                            break
                        
                        # Decode and add to buffer
                        buffer += data.decode('ascii', errors='ignore')
                        
                        # Process complete messages (lines ending with newline)
                        while '\n' in buffer:
                            line, buffer = buffer.split('\n', 1)
                            line = line.strip()
                            
                            if line:
                                self.last_message_time = time.time()
                                self.total_messages_received += 1
                                self._process_message(line, (self.host, self.port))
                        
                        # Prevent buffer overflow (max 100KB)
                        if len(buffer) > 100000:
                            logger.warning("Buffer overflow, clearing buffer")
                            buffer = buffer[-10000:]
                    
                    except socket.timeout:
                        logger.warning("Connection timeout")
                        break
                    except Exception as e:
                        if self.running.is_set():
                            logger.error(f"Error receiving data: {e}")
                        break
                
            except Exception as e:
                if self.running.is_set():
                    logger.error(f"TCP client error: {e}")
                    logger.info(f"Reconnecting in {reconnect_delay} seconds...")
                    time.sleep(reconnect_delay)
            finally:
                if self.client_socket:
                    try:
                        self.client_socket.close()
                    except:
                        pass
                    self.client_socket = None
        
        logger.info(f"TCP client thread stopped (total messages received: {self.total_messages_received})")
    
    def _process_message(self, raw_data, addr):
        """
        Process received TCP message
        
        Args:
            raw_data (str): Raw ASCII string
            addr (tuple): Source address (ip, port)
        """
        source_ip, source_port = addr
        
        try:
            # Extract JSON from the message
            json_data = self._extract_json(raw_data)
            
            if json_data:
                # Call the callback function with exception handling
                if self.message_callback:
                    try:
                        self.message_callback(source_ip, source_port, raw_data, json_data)
                    except Exception as callback_error:
                        logger.error(f"Error in message callback: {callback_error}")
                        import traceback
                        logger.error(f"Callback traceback:\n{traceback.format_exc()}")
            else:
                logger.warning(f"No valid JSON found in message from {source_ip}:{source_port}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            import traceback
            logger.error(f"Processing traceback:\n{traceback.format_exc()}")
    
    def _extract_json(self, raw_data):
        """
        Extract JSON object from raw ASCII data
        
        Args:
            raw_data (str): Raw ASCII string
            
        Returns:
            dict: Parsed JSON data or None if not found
        """
        try:
            # Look for JSON pattern (starts with { and ends with })
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            matches = re.findall(json_pattern, raw_data)
            
            for match in matches:
                try:
                    # Try to parse as JSON
                    json_obj = json.loads(match)
                    return json_obj
                except json.JSONDecodeError:
                    continue
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting JSON: {e}")
            return None
    
    def is_running(self):
        """Check if client is running"""
        return self.running.is_set()
    
    def is_thread_alive(self):
        """Check if client thread is alive"""
        return self.thread is not None and self.thread.is_alive()
    
    def is_connected(self):
        """Check if connected to server"""
        return self.client_socket is not None
    
    def get_stats(self):
        """Get client statistics"""
        return {
            'running': self.running.is_set(),
            'thread_alive': self.is_thread_alive(),
            'total_messages': self.total_messages_received,
            'last_message_time': self.last_message_time
        }
