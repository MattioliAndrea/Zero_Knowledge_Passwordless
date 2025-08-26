import socket
import json
from typing import Dict, Any, Optional

class SocketClient:
    """TCP Socket client for communication"""
    
    def __init__(self, host: str = 'localhost', port: int = 8080):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
    
    def connect(self) -> bool:
        """Connect to server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            return True
        except Exception as e:
            print(f"Connection failed: {e}")
            return False
    
    def send_message(self, message: Dict[str, Any]) -> bool:
        """Send JSON message"""
        try:
            json_message = json.dumps(message)
            self.socket.send(json_message.encode())
            return True
        except Exception as e:
            print(f"Send failed: {e}")
            return False
    
    def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive JSON message"""
        try:
            data = self.socket.recv(1024).decode()
            return json.loads(data)
        except Exception as e:
            print(f"Receive failed: {e}")
            return None
    
    def close(self):
        """Close connection"""
        if self.socket:
            self.socket.close()

class SocketServer:
    """TCP Socket server for communication"""
    
    def __init__(self, host: str = 'localhost', port: int = 8080):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.client_socket: Optional[socket.socket] = None
    
    def start(self) -> bool:
        """Start server and listen for connections"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(1)
            print(f"Server listening on {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"Server start failed: {e}")
            return False
    
    def accept_connection(self) -> bool:
        """Accept client connection"""
        try:
            self.client_socket, addr = self.socket.accept()
            print(f"Client connected from {addr}")
            return True
        except Exception as e:
            print(f"Accept failed: {e}")
            return False
    
    def send_message(self, message: Dict[str, Any]) -> bool:
        """Send JSON message to client"""
        try:
            json_message = json.dumps(message)
            self.client_socket.send(json_message.encode())
            return True
        except Exception as e:
            print(f"Send failed: {e}")
            return False
    
    def receive_message(self) -> Optional[Dict[str, Any]]:
        """Receive JSON message from client"""
        try:
            data = self.client_socket.recv(1024).decode()
            return json.loads(data)
        except Exception as e:
            print(f"Receive failed: {e}")
            return None
    
    def close(self):
        """Close server and client connections"""
        if self.client_socket:
            self.client_socket.close()
        if self.socket:
            self.socket.close()
