"""
SSE Server Module
Broadcasts messages to connected frontend clients in real-time using Server-Sent Events
"""

from flask import Flask, Response, request
from flask_cors import CORS
import json
import logging
import time
from datetime import datetime
from threading import Thread, Event, Lock
import queue

logger = logging.getLogger(__name__)


class SSEServer:
    """Handles SSE connections and message broadcasting"""
    
    def __init__(self, host, port, max_history_messages=100, decode_handler=None):
        """
        Initialize SSE server
        
        Args:
            host (str): IP address to bind to
            port (int): Port to listen on
            max_history_messages (int): Maximum history messages to keep in backend
                                       (Frontend decides how many to display)
            decode_handler: DecodeHandler instance for ACARS decoding
        """
        self.host = host
        self.port = port
        self.max_history_messages = max_history_messages
        self.decode_handler = decode_handler
        self.clients = {}  # Dictionary to store client queues
        self.recent_messages = []
        self.app = Flask(__name__)
        CORS(self.app)  # Enable CORS for all routes
        self.server = None
        self.thread = None
        self.running = Event()
        self.client_lock = Lock()
        self.client_id_counter = 0
        self.tcp_status_callback = None  # Callback to get TCP connection status
        
        # Setup Flask routes
        self._setup_routes()
        
    def _setup_routes(self):
        """Setup Flask routes"""
        
        @self.app.route('/stream')
        def stream():
            """SSE endpoint for streaming messages"""
            return Response(
                self._event_stream(),
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache, no-store, must-revalidate',
                    'Connection': 'keep-alive',
                    'X-Accel-Buffering': 'no',  # Disable nginx buffering
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Methods': 'GET, OPTIONS',
                    'Access-Control-Allow-Headers': 'Content-Type'
                }
            )
        
        @self.app.route('/health')
        def health():
            """Health check endpoint"""
            # TCP connection status (if tcp_status_callback is set)
            tcp_status = 'unknown'
            if hasattr(self, 'tcp_status_callback') and self.tcp_status_callback:
                tcp_status = self.tcp_status_callback()
            
            return {
                'status': 'ok', 
                'clients': len(self.clients),
                'recent_messages': len(self.recent_messages),
                'tcp_status': tcp_status
            }
        
        @self.app.route('/decode', methods=['POST', 'OPTIONS'])
        def decode():
            """Decode ACARS message endpoint"""
            if request.method == 'OPTIONS':
                return '', 200
            
            try:
                data = request.get_json()
                label = data.get('label', '')
                text = data.get('text', '')
                
                if not label or not text:
                    return {'error': 'Label and text required'}, 400
                
                if not self.decode_handler or not self.decode_handler.initialized:
                    return {'error': 'Decoder not available'}, 503
                
                if not self.decode_handler.is_decodable(label):
                    return {'decodable': False, 'decoded': None}
                
                decoded = self.decode_handler.decode_message(label, text)
                return {'decodable': True, 'decoded': decoded}
                
            except Exception as e:
                logger.error(f"Decode endpoint error: {e}")
                return {'error': str(e)}, 500
    
    def _event_stream(self):
        """
        Generator function for SSE stream
        Sends messages to connected client
        """
        # Get client IP and store it immediately before request context is lost
        try:
            client_ip = str(request.remote_addr) if request and hasattr(request, 'remote_addr') else 'unknown'
        except (RuntimeError, AttributeError):
            client_ip = 'unknown'
        
        # Create a queue for this client
        client_queue = queue.Queue(maxsize=100)
        
        # Initialize client_id to None to avoid reference errors
        client_id = None
        
        try:
            with self.client_lock:
                self.client_id_counter += 1
                client_id = self.client_id_counter
                self.clients[client_id] = client_queue
            
            logger.info(f"New SSE client connected: {client_ip} (ID: {client_id})")
            
            # İLK ÖNCE heartbeat gönder ki browser hemen bağlandığını anlasın
            yield f": heartbeat\n\n"
            
            # Geçmiş mesajları GÖNDERME - Sadece canlı mesajlar!
            logger.info(f"Client {client_id} ready for live messages")
            
            last_heartbeat = time.time()
            
            # Keep connection alive and send messages
            while self.running.is_set():
                try:
                    # Get message from queue with timeout
                    message = client_queue.get(timeout=1.0)
                    yield f"data: {json.dumps(message)}\n\n"
                    
                except queue.Empty:
                    # Send heartbeat every 15 seconds to keep connection alive
                    current_time = time.time()
                    if current_time - last_heartbeat >= 15:
                        yield f": heartbeat\n\n"
                        last_heartbeat = current_time
                        
        except GeneratorExit:
            logger.info(f"Client disconnected: {client_ip} (ID: {client_id})")
        except Exception as e:
            logger.error(f"Error in event stream for client {client_ip} (ID: {client_id}): {e}")
        finally:
            # Remove client from the dictionary
            if client_id is not None:
                with self.client_lock:
                    if client_id in self.clients:
                        del self.clients[client_id]
    
    def start(self):
        """Start SSE server in a separate thread"""
        if self.thread and self.thread.is_alive():
            logger.warning("SSE server is already running")
            return False
        
        try:
            self.running.set()
            self.thread = Thread(target=self._run_server, daemon=True)
            self.thread.start()
            
            # Wait for the server to start
            time.sleep(1)
            
            logger.info(f"SSE server started on http://{self.host}:{self.port}/stream")
            return True
                
        except Exception as e:
            logger.error(f"Error starting SSE server: {e}")
            return False
    
    def _run_server(self):
        """Run SSE server (runs in separate thread)"""
        try:
            # Disable Flask request logging to reduce noise
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.WARNING)
            
            logger.info("SSE server is running and accepting connections")
            self.app.run(host=self.host, port=self.port, threaded=True)
            
        except Exception as e:
            logger.error(f"SSE server error: {e}")
    
    def broadcast_message(self, message_data):
        """
        Broadcast a message to all connected clients
        
        Args:
            message_data (dict): Message data to broadcast
        """
        if not self.running.is_set():
            logger.warning("Server is not running, cannot broadcast message")
            return
        
        # Add to recent messages
        self.recent_messages.append(message_data)
        
        # Keep only the last max_history_messages in backend
        if len(self.recent_messages) > self.max_history_messages:
            self.recent_messages = self.recent_messages[-self.max_history_messages:]
        
        # Prepare message
        message = {
            'type': 'message',
            'data': message_data
        }
        
        # Broadcast to all connected clients
        with self.client_lock:
            disconnected_clients = []
            for client_id, client_queue in self.clients.items():
                try:
                    # Try to add message to queue without blocking
                    client_queue.put_nowait(message)
                except queue.Full:
                    logger.warning(f"Client {client_id} queue is full, marking for disconnect")
                    disconnected_clients.append(client_id)
                except Exception as e:
                    logger.error(f"Error sending to client {client_id}: {e}")
                    disconnected_clients.append(client_id)
            
            # Remove disconnected clients
            for client_id in disconnected_clients:
                if client_id in self.clients:
                    del self.clients[client_id]
    
    def stop(self):
        """Stop the SSE server"""
        logger.info("Stopping SSE server...")
        self.running.clear()
        
        # Clear all client queues
        with self.client_lock:
            self.clients.clear()
        
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=3.0)
        
        logger.info("SSE server stopped")
    
    def get_client_count(self):
        """Get number of connected clients"""
        with self.client_lock:
            return len(self.clients)
