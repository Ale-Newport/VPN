#!/usr/bin/env python3
"""
Cliente VPN Simple
Ejecutar en el dispositivo que quiere conectarse remotamente
Requiere: pip install cryptography requests
"""

import socket
import json
import sys
import os
import time
from cryptography.fernet import Fernet
import urllib.request
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class VPNClient:
    def __init__(self, server_host, server_port, key):
        self.server_host = server_host
        self.server_port = server_port
        self.cipher = Fernet(key)
        self.connected = False
        self.socket = None
        self.proxy_port = 8888
    
    def connect_to_server(self):
        """Conectar al servidor VPN"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server_host, self.server_port))
            self.connected = True
            print(f"Conectado al servidor VPN {self.server_host}:{self.server_port}")
            return True
        except Exception as e:
            print(f"Error conectando al servidor: {e}")
            return False
    
    def send_request(self, request):
        """Enviar solicitud al servidor VPN"""
        if not self.connected:
            return {'status': 'error', 'message': 'No conectado al servidor'}
        
        try:
            # Cifrar y enviar solicitud
            encrypted_request = self.cipher.encrypt(json.dumps(request).encode())
            self.socket.send(encrypted_request)
            
            # Recibir respuesta
            encrypted_response = self.socket.recv(65536)  # 64KB max
            decrypted_response = self.cipher.decrypt(encrypted_response)
            
            return json.loads(decrypted_response.decode())
        
        except Exception as e:
            print(f"Error enviando solicitud: {e}")
            self.connected = False
            return {'status': 'error', 'message': str(e)}
    
    def test_connection(self):
        """Probar conexión con el servidor"""
        response = self.send_request({'type': 'ping'})
        if response['status'] == 'pong':
            print("✓ Conexión VPN funcionando correctamente")
            return True
        else:
            print("✗ Error en la conexión VPN")
            return False
    
    def web_request(self, url, method='GET', headers=None, data=None):
        """Hacer solicitud web a través del servidor VPN"""
        request = {
            'type': 'web_request',
            'url': url,
            'method': method,
            'headers': headers or {},
            'data': data
        }
        
        return self.send_request(request)
    
    def start_proxy_server(self):
        """Iniciar servidor proxy local"""
        class ProxyHandler(BaseHTTPRequestHandler):
            def __init__(self, *args, vpn_client=None, **kwargs):
                self.vpn_client = vpn_client
                super().__init__(*args, **kwargs)
            
            def do_GET(self):
                self.handle_request('GET')
            
            def do_POST(self):
                self.handle_request('POST')
            
            def handle_request(self, method):
                try:
                    # Obtener URL completa
                    url = self.path if self.path.startswith('http') else f"http://{self.headers.get('Host', '')}{self.path}"
                    
                    # Obtener headers
                    headers = dict(self.headers)
                    
                    # Obtener datos POST si es necesario
                    data = None
                    if method == 'POST':
                        content_length = int(self.headers.get('Content-Length', 0))
                        if content_length > 0:
                            data = self.rfile.read(content_length)
                    
                    # Hacer solicitud a través de VPN
                    response = self.vpn_client.web_request(url, method, headers, data)
                    
                    if response['status'] == 'success':
                        # Enviar respuesta exitosa
                        self.send_response(response['status_code'])
                        
                        # Enviar headers
                        for header, value in response['headers'].items():
                            if header.lower() not in ['transfer-encoding', 'content-encoding']:
                                self.send_header(header, value)
                        
                        self.end_headers()
                        self.wfile.write(response['content'].encode('utf-8'))
                    
                    else:
                        # Enviar error
                        self.send_response(500)
                        self.send_header('Content-Type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(f"Error VPN: {response.get('message', 'Unknown error')}".encode())
                
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-Type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(f"Error: {str(e)}".encode())
            
            def log_message(self, format, *args):
                print(f"Proxy: {format % args}")
        
        # Crear handler con referencia al cliente VPN
        def handler_factory(*args, **kwargs):
            return ProxyHandler(*args, vpn_client=self, **kwargs)
        
        try:
            server = HTTPServer(('127.0.0.1', self.proxy_port), handler_factory)
            print(f"Servidor proxy iniciado en http://127.0.0.1:{self.proxy_port}")
            print("Configura tu navegador para usar este proxy HTTP")
            print("Presiona Ctrl+C para detener")
            server.serve_forever()
        except KeyboardInterrupt:
            print("\nDeteniendo servidor proxy...")
        except Exception as e:
            print(f"Error en servidor proxy: {e}")
    
    def disconnect(self):
        """Desconectar del servidor VPN"""
        if self.socket:
            self.socket.close()
        self.connected = False
        print("Desconectado del servidor VPN")

def load_key_from_file(filename='vpn_key.txt'):
    """Cargar clave desde archivo"""
    try:
        with open(filename, 'rb') as f:
            return f.read()
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo {filename}")
        print("Copia el archivo vpn_key.txt del servidor a este directorio")
        return None

def main():
    print("=== Cliente VPN Simple ===")
    print("Este cliente se conecta al servidor VPN para usar su conexión")
    print()
    
    # Obtener configuración
    server_host = input("IP del servidor VPN: ").strip()
    if not server_host:
        print("Error: Debes especificar la IP del servidor")
        return
    
    try:
        server_port = int(input("Puerto del servidor (8080): ") or "8080")
    except ValueError:
        server_port = 8080
    
    # Cargar clave
    print("\nCargando clave de cifrado...")
    key_input = input("Pega la clave aquí (o presiona Enter para cargar desde archivo): ").strip()
    
    if key_input:
        try:
            key = key_input.encode()
        except:
            print("Error: Clave inválida")
            return
    else:
        key = load_key_from_file()
        if not key:
            return
    
    # Crear cliente VPN
    client = VPNClient(server_host, server_port, key)
    
    try:
        # Conectar al servidor
        if not client.connect_to_server():
            return
        
        # Probar conexión
        if not client.test_connection():
            return
        
        print("\n=== Opciones ===")
        print("1. Iniciar servidor proxy (recomendado)")
        print("2. Hacer solicitud web manual")
        print("3. Test de velocidad")
        
        choice = input("\nSelecciona una opción (1): ").strip() or "1"
        
        if choice == "1":
            # Iniciar servidor proxy en hilo separado
            proxy_thread = threading.Thread(target=client.start_proxy_server)
            proxy_thread.daemon = True
            proxy_thread.start()
            
            print("\nServidor proxy ejecutándose...")
            print("Para usarlo en tu navegador:")
            print(f"- Proxy HTTP: 127.0.0.1:{client.proxy_port}")
            print("- Tipo: HTTP")
            print("\nPresiona Enter para detener...")
            input()
        
        elif choice == "2":
            url = input("URL a solicitar: ").strip()
            if url:
                response = client.web_request(url)
                print(f"\nRespuesta: {response}")
        
        elif choice == "3":
            print("Ejecutando test de velocidad...")
            start_time = time.time()
            response = client.send_request({'type': 'speed_test'})
            end_time = time.time()
            
            if response['status'] == 'success':
                data_size = len(response['data'])
                duration = end_time - start_time
                speed = (data_size / 1024 / 1024) / duration  # MB/s
                print(f"Velocidad: {speed:.2f} MB/s")
            else:
                print(f"Error en test: {response}")
    
    except KeyboardInterrupt:
        print("\nDeteniendo cliente...")
    
    finally:
        client.disconnect()

if __name__ == "__main__":
    main()