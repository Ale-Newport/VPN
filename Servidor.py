#!/usr/bin/env python3
"""
Servidor VPN Simple
Ejecutar en el ordenador conectado a la WiFi X
Requiere: pip install cryptography
"""

import socket
import threading
import subprocess
import sys
import os
from cryptography.fernet import Fernet
import json
import time

class VPNServer:
    def __init__(self, port=8080):
        self.port = port
        self.clients = []
        self.running = False
        
        # Generar clave de cifrado
        self.key = Fernet.generate_key()
        self.cipher = Fernet(self.key)
        
        # Guardar la clave en archivo para el cliente
        with open('vpn_key.txt', 'wb') as f:
            f.write(self.key)
        
        print(f"Clave VPN guardada en vpn_key.txt")
        print(f"Clave: {self.key.decode()}")
    
    def get_local_ip(self):
        """Obtener IP local del servidor"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"
    
    def handle_client(self, client_socket, address):
        """Manejar conexión de cliente"""
        print(f"Cliente conectado desde {address}")
        
        try:
            while self.running:
                # Recibir datos del cliente
                encrypted_data = client_socket.recv(4096)
                if not encrypted_data:
                    break
                
                try:
                    # Descifrar datos
                    decrypted_data = self.cipher.decrypt(encrypted_data)
                    request = json.loads(decrypted_data.decode())
                    
                    # Procesar solicitud
                    response = self.process_request(request)
                    
                    # Enviar respuesta cifrada
                    encrypted_response = self.cipher.encrypt(json.dumps(response).encode())
                    client_socket.send(encrypted_response)
                    
                except Exception as e:
                    print(f"Error procesando solicitud: {e}")
                    break
        
        except Exception as e:
            print(f"Error con cliente {address}: {e}")
        
        finally:
            client_socket.close()
            if client_socket in self.clients:
                self.clients.remove(client_socket)
            print(f"Cliente {address} desconectado")
    
    def process_request(self, request):
        """Procesar solicitudes del cliente"""
        try:
            if request['type'] == 'web_request':
                # Hacer solicitud web por el cliente
                import urllib.request
                import urllib.parse
                
                url = request['url']
                method = request.get('method', 'GET')
                headers = request.get('headers', {})
                data = request.get('data', None)
                
                req = urllib.request.Request(url, data=data, headers=headers)
                req.get_method = lambda: method
                
                with urllib.request.urlopen(req, timeout=10) as response:
                    content = response.read()
                    return {
                        'status': 'success',
                        'status_code': response.getcode(),
                        'headers': dict(response.headers),
                        'content': content.decode('utf-8', errors='ignore')
                    }
            
            elif request['type'] == 'ping':
                return {'status': 'pong', 'server_time': time.time()}
            
            elif request['type'] == 'speed_test':
                # Test de velocidad simple
                test_data = 'x' * 1024 * 100  # 100KB
                return {'status': 'success', 'data': test_data}
            
            else:
                return {'status': 'error', 'message': 'Tipo de solicitud no reconocido'}
        
        except Exception as e:
            return {'status': 'error', 'message': str(e)}
    
    def start_server(self):
        """Iniciar servidor VPN"""
        self.running = True
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        try:
            server_socket.bind(('0.0.0.0', self.port))
            server_socket.listen(5)
            
            local_ip = self.get_local_ip()
            print(f"Servidor VPN iniciado en {local_ip}:{self.port}")
            print(f"Esperando conexiones...")
            print(f"Para conectarse usar: {local_ip}:{self.port}")
            print("Presiona Ctrl+C para detener")
            
            while self.running:
                try:
                    client_socket, address = server_socket.accept()
                    self.clients.append(client_socket)
                    
                    # Crear hilo para manejar cliente
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                
                except KeyboardInterrupt:
                    break
                except Exception as e:
                    print(f"Error aceptando conexión: {e}")
        
        except Exception as e:
            print(f"Error iniciando servidor: {e}")
        
        finally:
            self.running = False
            server_socket.close()
            print("Servidor VPN detenido")
    
    def stop_server(self):
        """Detener servidor"""
        self.running = False
        for client in self.clients:
            client.close()

def main():
    print("=== Servidor VPN Simple ===")
    print("Este servidor permite a clientes remotos usar tu conexión a internet")
    print()
    
    try:
        port = int(input("Puerto del servidor (8080): ") or "8080")
    except ValueError:
        port = 8080
    
    server = VPNServer(port)
    
    try:
        server.start_server()
    except KeyboardInterrupt:
        print("\nDeteniendo servidor...")
        server.stop_server()

if __name__ == "__main__":
    main()