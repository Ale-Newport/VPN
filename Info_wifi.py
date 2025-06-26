#!/usr/bin/env python3
"""
Detector de Información WiFi
Obtiene todos los datos necesarios para configurar la página de detección
Requiere: pip install requests psutil netifaces
"""

import socket
import subprocess
import platform
import re
import json
import requests
import sys
import os

try:
    import psutil
    import netifaces
except ImportError:
    print("Instalando dependencias necesarias...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psutil", "netifaces"])
    import psutil
    import netifaces

class WiFiInfoDetector:
    def __init__(self):
        self.system = platform.system()
        self.wifi_info = {}
        
    def get_local_ip(self):
        """Obtener IP local"""
        try:
            # Método 1: Conectar a servidor externo
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except:
            # Método 2: Usar netifaces
            try:
                gateways = netifaces.gateways()
                default_gateway = gateways['default'][netifaces.AF_INET]
                interface = default_gateway[1]
                addresses = netifaces.ifaddresses(interface)
                return addresses[netifaces.AF_INET][0]['addr']
            except:
                return "127.0.0.1"
    
    def get_gateway_ip(self):
        """Obtener IP del gateway/router"""
        try:
            if self.system == "Windows":
                result = subprocess.run(['ipconfig'], capture_output=True, text=True, shell=True)
                output = result.stdout
                
                # Buscar gateway por defecto
                gateway_match = re.search(r'Default Gateway.*?(\d+\.\d+\.\d+\.\d+)', output, re.DOTALL)
                if gateway_match:
                    return gateway_match.group(1)
            
            elif self.system in ["Linux", "Darwin"]:
                # Método 1: ip route (Linux)
                try:
                    result = subprocess.run(['ip', 'route', 'show', 'default'], 
                                          capture_output=True, text=True)
                    output = result.stdout
                    gateway_match = re.search(r'default via (\d+\.\d+\.\d+\.\d+)', output)
                    if gateway_match:
                        return gateway_match.group(1)
                except:
                    pass
                
                # Método 2: route (macOS/Linux)
                try:
                    result = subprocess.run(['route', '-n', 'get', 'default'], 
                                          capture_output=True, text=True)
                    output = result.stdout
                    gateway_match = re.search(r'gateway: (\d+\.\d+\.\d+\.\d+)', output)
                    if gateway_match:
                        return gateway_match.group(1)
                except:
                    pass
                
                # Método 3: netstat
                try:
                    result = subprocess.run(['netstat', '-rn'], capture_output=True, text=True)
                    output = result.stdout
                    for line in output.split('\n'):
                        if 'default' in line or '0.0.0.0' in line:
                            parts = line.split()
                            for part in parts:
                                if re.match(r'\d+\.\d+\.\d+\.\d+', part) and part != '0.0.0.0':
                                    return part
                except:
                    pass
            
            # Método fallback usando netifaces
            gateways = netifaces.gateways()
            return gateways['default'][netifaces.AF_INET][0]
            
        except Exception as e:
            print(f"Error obteniendo gateway: {e}")
            return "192.168.1.1"
    
    def get_wifi_name(self):
        """Obtener nombre de la red WiFi"""
        try:
            if self.system == "Windows":
                result = subprocess.run(['netsh', 'wlan', 'show', 'profiles'], 
                                      capture_output=True, text=True, shell=True)
                output = result.stdout
                
                # Obtener perfil conectado actualmente
                result2 = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], 
                                       capture_output=True, text=True, shell=True)
                interface_output = result2.stdout
                
                ssid_match = re.search(r'SSID\s*:\s*(.+)', interface_output)
                if ssid_match:
                    return ssid_match.group(1).strip()
            
            elif self.system == "Darwin":  # macOS
                result = subprocess.run(['/System/Library/PrivateFrameworks/Apple80211.framework/Versions/Current/Resources/airport', '-I'], 
                                      capture_output=True, text=True)
                output = result.stdout
                ssid_match = re.search(r'SSID: (.+)', output)
                if ssid_match:
                    return ssid_match.group(1).strip()
            
            elif self.system == "Linux":
                # Método 1: iwgetid
                try:
                    result = subprocess.run(['iwgetid', '-r'], capture_output=True, text=True)
                    if result.returncode == 0:
                        return result.stdout.strip()
                except:
                    pass
                
                # Método 2: nmcli
                try:
                    result = subprocess.run(['nmcli', '-t', '-f', 'active,ssid', 'dev', 'wifi'], 
                                          capture_output=True, text=True)
                    output = result.stdout
                    for line in output.split('\n'):
                        if line.startswith('yes:'):
                            return line.split(':', 1)[1].strip()
                except:
                    pass
                
                # Método 3: iw
                try:
                    result = subprocess.run(['iw', 'dev'], capture_output=True, text=True)
                    output = result.stdout
                    
                    # Buscar interfaz conectada
                    interface_match = re.search(r'Interface (\w+)', output)
                    if interface_match:
                        interface = interface_match.group(1)
                        result2 = subprocess.run(['iw', interface, 'link'], 
                                                capture_output=True, text=True)
                        ssid_match = re.search(r'SSID: (.+)', result2.stdout)
                        if ssid_match:
                            return ssid_match.group(1).strip()
                except:
                    pass
        
        except Exception as e:
            print(f"Error obteniendo nombre WiFi: {e}")
        
        return "WiFi-Desconocida"
    
    def get_network_range(self, ip, gateway):
        """Determinar el rango de red"""
        try:
            # Extraer los primeros 3 octetos para redes /24 comunes
            ip_parts = ip.split('.')
            gateway_parts = gateway.split('.')
            
            # Si IP y gateway comparten los primeros 3 octetos, usar ese rango
            if ip_parts[:3] == gateway_parts[:3]:
                return '.'.join(ip_parts[:3]) + '.'
            
            # Caso especial para redes /16
            if ip_parts[:2] == gateway_parts[:2]:
                return '.'.join(ip_parts[:2]) + '.'
            
            # Fallback: usar los primeros 3 octetos de la IP local
            return '.'.join(ip_parts[:3]) + '.'
            
        except:
            return "192.168.1."
    
    def get_public_ip_info(self):
        """Obtener información de IP pública"""
        try:
            # Obtener IP pública
            response = requests.get('https://api.ipify.org?format=json', timeout=10)
            ip_data = response.json()
            public_ip = ip_data['ip']
            
            # Obtener información geográfica y de ISP
            response = requests.get(f'https://ipapi.co/{public_ip}/json/', timeout=10)
            geo_data = response.json()
            
            return {
                'public_ip': public_ip,
                'city': geo_data.get('city', 'Ciudad-Desconocida'),
                'country': geo_data.get('country_name', 'País-Desconocido'),
                'isp': geo_data.get('org', 'ISP-Desconocido'),
                'timezone': geo_data.get('timezone', 'UTC'),
                'latitude': geo_data.get('latitude'),
                'longitude': geo_data.get('longitude')
            }
        
        except Exception as e:
            print(f"Error obteniendo información pública: {e}")
            return {
                'public_ip': 'Desconocida',
                'city': 'Ciudad-Desconocida',
                'country': 'País-Desconocido',
                'isp': 'ISP-Desconocido',
                'timezone': 'UTC',
                'latitude': None,
                'longitude': None
            }
    
    def get_network_interfaces(self):
        """Obtener información de interfaces de red"""
        interfaces = {}
        try:
            for interface_name in psutil.net_if_addrs():
                interface_info = psutil.net_if_addrs()[interface_name]
                for addr in interface_info:
                    if addr.family == socket.AF_INET:  # IPv4
                        interfaces[interface_name] = {
                            'ip': addr.address,
                            'netmask': addr.netmask,
                            'broadcast': addr.broadcast
                        }
                        break
        except Exception as e:
            print(f"Error obteniendo interfaces: {e}")
        
        return interfaces
    
    def detect_all_info(self):
        """Detectar toda la información de la red"""
        print("🔍 Detectando información de tu red WiFi...")
        print("=" * 50)
        
        # Información local
        local_ip = self.get_local_ip()
        gateway_ip = self.get_gateway_ip()
        wifi_name = self.get_wifi_name()
        network_range = self.get_network_range(local_ip, gateway_ip)
        
        print(f"📡 Nombre WiFi: {wifi_name}")
        print(f"🏠 IP Local: {local_ip}")
        print(f"🌐 Gateway: {gateway_ip}")
        print(f"📊 Rango de Red: {network_range}x")
        
        # Información pública
        print("\n🌍 Obteniendo información pública...")
        public_info = self.get_public_ip_info()
        
        print(f"🔗 IP Pública: {public_info['public_ip']}")
        print(f"🏙️ Ciudad: {public_info['city']}")
        print(f"🏢 ISP: {public_info['isp']}")
        print(f"🕐 Zona Horaria: {public_info['timezone']}")
        
        # Interfaces de red
        print("\n🔌 Interfaces de red:")
        interfaces = self.get_network_interfaces()
        for name, info in interfaces.items():
            print(f"  {name}: {info['ip']}")
        
        # Compilar información final
        self.wifi_info = {
            'expectedIP': network_range,
            'expectedGateway': gateway_ip,
            'wifiName': wifi_name,
            'expectedISP': public_info['isp'].split()[0] if public_info['isp'] != 'ISP-Desconocido' else 'Tu-ISP',
            'expectedCity': public_info['city'],
            'local_ip': local_ip,
            'public_ip': public_info['public_ip'],
            'country': public_info['country'],
            'full_isp': public_info['isp'],
            'coordinates': {
                'lat': public_info['latitude'],
                'lng': public_info['longitude']
            },
            'interfaces': interfaces
        }
        
        return self.wifi_info
    
    def generate_config_code(self):
        """Generar código de configuración para la página web"""
        config_js = f"""
// Configuración automática generada para tu WiFi
const AUTHORIZED_WIFI = {{
    expectedIP: '{self.wifi_info['expectedIP']}',
    expectedGateway: '{self.wifi_info['expectedGateway']}',
    wifiName: '{self.wifi_info['wifiName']}',
    allowedMAC: null  // Opcional: MAC del router
}};

const expectedISP = '{self.wifi_info['expectedISP']}';
const expectedCity = '{self.wifi_info['expectedCity']}';

// Información adicional detectada:
// IP Local: {self.wifi_info['local_ip']}
// IP Pública: {self.wifi_info['public_ip']}
// ISP Completo: {self.wifi_info['full_isp']}
// País: {self.wifi_info['country']}
"""
        return config_js
    
    def save_config_file(self, filename='wifi_config.js'):
        """Guardar configuración en archivo"""
        config_code = self.generate_config_code()
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(config_code)
        
        print(f"\n💾 Configuración guardada en: {filename}")
        return filename
    
    def generate_html_with_config(self):
        """Generar página HTML con configuración automática"""
        # Aquí cargarías el HTML de la página anterior y reemplazarías los valores
        html_template = '''
        // Reemplaza estas líneas en tu página HTML:
        
        const AUTHORIZED_WIFI = {
            expectedIP: ''' + f"'{self.wifi_info['expectedIP']}'" + ''',
            expectedGateway: ''' + f"'{self.wifi_info['expectedGateway']}'" + ''',
            wifiName: ''' + f"'{self.wifi_info['wifiName']}'" + ''',
        };
        
        const expectedISP = ''' + f"'{self.wifi_info['expectedISP']}'" + ''';
        const expectedCity = ''' + f"'{self.wifi_info['expectedCity']}'" + ''';
        '''
        
        return html_template

def main():
    print("🚀 Detector de Información WiFi")
    print("================================")
    print("Este programa detecta automáticamente los datos de tu WiFi")
    print("para configurar la página de detección VPN.\n")
    
    detector = WiFiInfoDetector()
    
    try:
        # Detectar información
        wifi_info = detector.detect_all_info()
        
        print("\n" + "=" * 50)
        print("📋 RESUMEN DE CONFIGURACIÓN")
        print("=" * 50)
        
        print(f"WiFi Name: {wifi_info['wifiName']}")
        print(f"IP Range: {wifi_info['expectedIP']}x")
        print(f"Gateway: {wifi_info['expectedGateway']}")
        print(f"ISP: {wifi_info['expectedISP']}")
        print(f"City: {wifi_info['expectedCity']}")
        
        # Guardar configuración
        config_file = detector.save_config_file()
        
        # Mostrar código para copiar
        print("\n📄 CÓDIGO PARA TU PÁGINA WEB:")
        print("-" * 30)
        print(detector.generate_config_code())
        
        # Generar archivo JSON también
        json_file = 'wifi_info.json'
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(wifi_info, f, indent=2, ensure_ascii=False)
        
        print(f"📊 Información completa guardada en: {json_file}")
        
        print("\n✅ ¡Detección completada!")
        print("Ahora puedes usar estos valores en tu página de detección WiFi.")
        
        # Mostrar instrucciones
        print("\n📝 INSTRUCCIONES:")
        print("1. Copia el código de configuración mostrado arriba")
        print("2. Reemplaza las variables en tu página HTML")
        print("3. Guarda y prueba la página")
        print("4. La página ahora detectará específicamente tu WiFi")
        
    except KeyboardInterrupt:
        print("\n⏹️ Detección cancelada por el usuario")
    except Exception as e:
        print(f"\n❌ Error durante la detección: {e}")
        print("Asegúrate de estar conectado a WiFi y tener permisos de administrador")

if __name__ == "__main__":
    main()