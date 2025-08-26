import os
import socket
import threading
import json
import time
from collections import deque
from libs.interfaces.icrypto_utils import ICryptoUtils
from libs.interfaces.izkp_core import IZKPCore
from libs.zkp_core import ZKPCore
from libs.bruteforce_worker import BruteForceWorker

os.makedirs("Cracked_Key", exist_ok=True)

class AnthonyCore:
    def __init__(self,active_mode=False, listen_host='localhost', listen_port=8081, forward_host='localhost', forward_port=8080,zkp: IZKPCore = None):
        self.listen_host = listen_host
        self.listen_port = listen_port
        self.forward_host = forward_host
        self.forward_port = forward_port
        self.log_queue = deque(maxlen=100) # mantiene solo gli ultimi 100 log
        self.sidebar_logs = []
        self.brute_force_targets = {}  # {user_id: known_public_key}
        self.zkp = zkp or ZKPCore()
        self.active_mode=active_mode
        self.server_socket = None  # Fixed: store server socket reference
        
    def start_proxy(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.listen_host, self.listen_port))
        self.server_socket.listen()
        print(f"[Anthony] In ascolto su {self.listen_host}:{self.listen_port}...")

        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                #print(f"[Anthony] Nuova connessione da {addr} requested on {client_socket.getsockname()}")
                
                # Log the connection attempt
                self.log("NEW CONNECTION", f" CLIENT from {str(addr)} requested {client_socket.getsockname()}")
                
                threading.Thread(target=self.handle_connection, args=(client_socket,), daemon=True).start()
        except Exception as e:
            print(f"[Anthony] Errore nel proxy: {e}")
            self.log("ERROR", {"event": "proxy_error", "error": str(e), "timestamp": time.time()})
        finally:
            if self.server_socket:  # Fixed: use correct reference
                self.server_socket.close()
                print("[Anthony] Socket chiuso.")

    def handle_connection(self, client_socket):
        forward_socket = None
        try:
            forward_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            forward_socket.connect((self.forward_host, self.forward_port))
            
            self.log("NEW CONNECTION", f"SERVER request {self.forward_host}:{self.forward_port}")
            
            #print(f"Request send on {forward_socket.getpeername()}")
            threading.Thread(target=self.forward, args=(client_socket, forward_socket, "Peggy → Victor"), daemon=True).start()
            threading.Thread(target=self.forward, args=(forward_socket, client_socket, "Victor → Peggy"), daemon=True).start()
        except Exception as e:
            print(f"[Anthony] Errore connessione a Victor: {e}")
            self.log("ERROR",f"connection_error: {str(e)}")
            
            # Clean up sockets on connection error
            try:
                if client_socket:
                    client_socket.close()
                if forward_socket:
                    forward_socket.close()
            except:
                pass

    def forward(self, source_socket:socket, dest_socket:socket, direction):
        try:
            while True:
                data = source_socket.recv(4096)
                if not data:
                    self.log("CONNECTION", f"connection_closed {direction}")
                    break
                    
                try:
                    message = json.loads(data.decode())
                    self.log(direction, message)
                    print(f"[{direction}] {message}")

                    if message.get("type") == "response" and self.active_mode:
                        threading.Thread(target=self._attempt_bruteforce, args=(message,), daemon=True).start()

                    dest_socket.send(json.dumps(message).encode())

                except json.JSONDecodeError as e:
                    # Log raw data when JSON parsing fails
                    self.log(f"{direction} (RAW)", {"raw_data": data.decode('utf-8', errors='replace'), "error": str(e), "timestamp": time.time()})
                    print(f"[Anthony] Errore parsing JSON in {direction}: {e}")
                    # Forward raw data anyway
                    dest_socket.send(data)
                except Exception as e:
                    self.log("ERROR", {"event": "forward_error", "direction": direction, "error": str(e), "timestamp": time.time()})
                    print(f"[Anthony] Errore processing in {direction}: {e}")
                    
        except Exception as e:
            print(f"[Anthony] Errore forwarding: {direction} {e}")
            self.log("ERROR", {"event": "forwarding_error", "direction": direction, "error": str(e), "timestamp": time.time()})
        finally:
            # Clean up connections
            self._cleanup_connection( dest_socket, direction)

    def _cleanup_connection(self, dest_socket, direction):
        """Clean up socket connections properly"""
        try:
            dest_socket.shutdown(socket.SHUT_RDWR)
            dest_socket.close()
            print(f"[Anthony] Chiusura dest_socket per {direction}")
        except Exception as e:
            print(f"[Anthony] Errore chiusura dest_socket: {e}")

    def log(self, direction, message):

        entry = {"direction": direction, "message": message, "timestamp": time.time()}
        self.log_queue.append(entry)

    def get_log_queue(self):
        return list(self.log_queue)  # Fixed: return the actual queue
    
    def toggle_mode(self):
        self.active_mode = not self.active_mode
        print(f"[Anthony] Modalità attiva: {self.active_mode}")
        
    def _track_brute_force_target(self, message):
        """
        Salva l'user_id e la sua chiave pubblica osservata dalla registrazione.
        """
        user_id = message.get("user_id")
        public_key = message.get("public_key")
        if user_id and public_key:
            self.brute_force_targets[user_id] = {
                "public_key": public_key,
                "system_params": message.get("system_params")
            }
            print(f"[Anthony] Tracciato target '{user_id}' con public_key={public_key}")
        else:
            print("[Anthony] Messaggio di registrazione incompleto. Target ignorato.")

    def _attempt_bruteforce(self, msg):
        """
        Simula attacco brute-force sulla chiave pubblica osservata per tentare di trovare la password.
        """
        user_id = msg.get("user_id")
        if not user_id:
            self._log_gui("[BruteForce]", "❌ Nessun user_id fornito nel messaggio.")
            return
        
        device_public_key = msg.get("device_public_key", {})
        systemparams = device_public_key.get("system_params", {})
        try:
            public_key = int(device_public_key.get("public_key"))
            g = int(systemparams.get("g"))
            p = int(systemparams.get("p"))
            q = int(systemparams.get("q"))
            bit_length = int(systemparams.get("bit_length", 0))  # opzionale
        except (ValueError, TypeError) as e:
            self._log_gui("[BruteForce]", f"❌ Parametri non validi nel messaggio: {e}")
            return   

        if bit_length > 64:
            self._log_gui("[BruteForce]", f"🚫 Salto attacco su '{user_id}': bit_length troppo elevato ({bit_length} bit)")
            return
        else:
            self._log_gui("[BruteForce]", f"🧠 Attacco su '{user_id}' con g={g}, p={p}, y={public_key}, q={q}")
            x = BruteForceWorker._baby_step_giant_step_parallel(g, public_key, p, q)

        if x is not None:
            self._log_gui("[BruteForce]", f"✅ Password trovata per '{user_id}': {x}")
                # Salva risultato in file
            filename = f"Cracked_Key/{user_id}.json"
            os.makedirs("Cracked_Key", exist_ok=True)

            result = {
                "user_id": user_id,
                "private_key": str(x),
                "public_key": str(public_key),
                "params": {
                    "g": str(g),
                    "p": str(p),
                    "q": str(q),
                    "bit_length": str(bit_length)
                }
            }
            
            with open(filename, "w") as f:
                json.dump(result, f, indent=2)
            
            self._log_gui("[BruteForce]", f"💾 Risultato salvato in {filename}")
            
        else:
            self._log_gui("[BruteForce]", f"❌ Nessuna corrispondenza per '{user_id}'")
    
    def _log_gui(self, direction, message):
        """
        Inserisce un log nel queue visibile dalla GUI e opzionalmente nella sidebar.
        """
        entry = {"direction": direction, "message": message, "timestamp": time.time()}
        self.log_queue.append(entry)

        # Sidebar logs (solo per brute force)
        if "BruteForce" in direction:  # safe check
            self.sidebar_logs.append(entry)
        
        print(f"{direction} {message}")
        
        


