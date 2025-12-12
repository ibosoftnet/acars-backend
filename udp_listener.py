"""
UDP Listener Module
Listens for incoming UDP messages and extracts JSON data
"""

import socket
import logging
import json
import re
from threading import Thread, Event

logger = logging.getLogger(__name__)


class UDPListener:
    """Handles UDP socket listening and message parsing"""
    
    def __init__(self, host, port, message_callback):
        """
        Initialize UDP listener
        
        Args:
            host (str): IP address to bind to
            port (int): Port to listen on
            message_callback (callable): Function to call when message is received
                                       Signature: callback(source_ip, source_port, raw_data, json_data)
        """
        self.host = host
        self.port = port
        self.message_callback = message_callback
        self.socket = None
        self.running = Event()
        self.thread = None
        
    def start(self):
        """Start the UDP listener in a separate thread"""
        if self.thread and self.thread.is_alive():
            logger.warning("UDP listener is already running")
            return False
        
        try:
            # Create UDP socket
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.settimeout(1.0)  # Set timeout for graceful shutdown
            
            logger.info(f"UDP listener bound to {self.host}:{self.port}")
            
            # Start listening thread
            self.running.set()
            self.thread = Thread(target=self._listen, daemon=True)
            self.thread.start()
            
            return True
            
        except Exception as e:
            logger.error(f"Error starting UDP listener: {e}")
            return False
    
    def stop(self):
        """Stop the UDP listener"""
        logger.info("Stopping UDP listener...")
        self.running.clear()
        
        if self.thread:
            self.thread.join(timeout=3.0)
        
        if self.socket:
            self.socket.close()
            
        logger.info("UDP listener stopped")
    
    def _listen(self):
        """Main listening loop (runs in separate thread)"""
        logger.info("UDP listener thread started")
        consecutive_errors = 0
        last_message_time = None
        
        while self.running.is_set():
            try:
                # Receive data with timeout
                data, addr = self.socket.recvfrom(65535)
                
                if data:
                    last_message_time = __import__('time').time()
                    self._process_message(data, addr)
                    consecutive_errors = 0  # Reset error counter on success
                    
            except socket.timeout:
                # Timeout is normal, allows checking running flag
                continue
            except Exception as e:
                consecutive_errors += 1
                if self.running.is_set():
                    logger.error(f"Error receiving UDP data (consecutive errors: {consecutive_errors}): {e}")
                    if consecutive_errors >= 10:
                        logger.critical(f"Too many consecutive errors ({consecutive_errors}), listener may be broken!")
                        consecutive_errors = 0  # Reset to avoid spam
        
        logger.info("UDP listener thread stopped")
    
    def _process_message(self, data, addr):
        """
        Process received UDP message
        
        Args:
            data (bytes): Raw UDP data
            addr (tuple): Source address (ip, port)
        """
        source_ip, source_port = addr
        
        try:
            # Decode data as ASCII
            raw_ascii = data.decode('ascii', errors='ignore')
            
            # Extract JSON from the message
            json_data = self._extract_json(raw_ascii)
            
            if json_data:
                logger.debug(f"Received message from {source_ip}:{source_port}")
                logger.debug(f"JSON data: {json_data}")
                
                # Call the callback function with exception handling
                if self.message_callback:
                    try:
                        self.message_callback(source_ip, source_port, raw_ascii, json_data)
                    except Exception as callback_error:
                        logger.error(f"ERROR in message callback: {callback_error}")
                        import traceback
                        logger.error(f"Callback traceback: {traceback.format_exc()}")
            else:
                logger.warning(f"No valid JSON found in message from {source_ip}:{source_port}")
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            import traceback
            logger.error(f"Processing traceback: {traceback.format_exc()}")
    
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
            # This regex finds a complete JSON object
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
        """Check if listener is running"""
        return self.running.is_set()
