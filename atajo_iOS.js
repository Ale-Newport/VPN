// ATAJO DE iOS USANDO SHORTCUTS
// Copia este código en la app "Atajos" de iOS

// 1. Crear nuevo atajo llamado "VPN Test"
// 2. Agregar acción "Ejecutar JavaScript en página web"
// 3. Pegar este código:

// Configuración de tu servidor VPN
const VPN_CONFIG = {
    serverIP: "192.168.1.58",  // Cambia por la IP de tu servidor
    serverPort: 8080,
    serverKey: "QUbFiNSnGLphVVVgDD9CNuFjBxKBTMJzgdgbkib4X2c="
};

// Función principal del atajo
async function testVPNConnection() {
    console.log("🍎 Iniciando test VPN desde iOS...");
    
    try {
        // Test 1: Verificar conectividad básica
        console.log("📡 Probando conectividad...");
        
        const connectivityTest = await fetch('https://ale-newport.github.io/VPN/', {
            method: 'GET',
            timeout: 5000
        });
        
        if (connectivityTest.ok) {
            const ipData = await connectivityTest.json();
            console.log(`📍 Tu IP actual: ${ipData.origin}`);
            
            // Test 2: Probar página de detección WiFi
            const wifiPageURL = "http://tu-pagina-wifi.com"; // Cambia por tu URL
            console.log(`🔍 Probando acceso a página WiFi: ${wifiPageURL}`);
            
            try {
                const wifiPageResponse = await fetch(wifiPageURL, {
                    method: 'GET',
                    timeout: 10000
                });
                
                if (wifiPageResponse.ok) {
                    const pageContent = await wifiPageResponse.text();
                    
                    if (pageContent.includes('🎉 ¡Acceso autorizado desde WiFi X!')) {
                        console.log("✅ ¡VPN FUNCIONANDO! - Página detecta WiFi X");
                        return {
                            status: "success",
                            message: "VPN funcionando correctamente",
                            ip: ipData.origin,
                            wifiAccess: true
                        };
                    } else if (pageContent.includes('🚫 Acceso denegado')) {
                        console.log("❌ VPN no funcionando - Acceso denegado");
                        return {
                            status: "error",
                            message: "VPN no está funcionando",
                            ip: ipData.origin,
                            wifiAccess: false
                        };
                    } else {
                        console.log("⚠️ Página cargada pero sin mensaje claro");
                        return {
                            status: "warning",
                            message: "Estado incierto",
                            ip: ipData.origin,
                            wifiAccess: "unknown"
                        };
                    }
                } else {
                    console.log("❌ No se pudo cargar la página WiFi");
                    return {
                        status: "error",
                        message: "No se pudo acceder a página de verificación",
                        ip: ipData.origin,
                        wifiAccess: false
                    };
                }
            } catch (wifiError) {
                console.log(`❌ Error accediendo a página WiFi: ${wifiError.message}`);
                return {
                    status: "error",
                    message: `Error de conexión: ${wifiError.message}`,
                    ip: ipData.origin,
                    wifiAccess: false
                };
            }
            
        } else {
            console.log("❌ Sin conectividad a internet");
            return {
                status: "error",
                message: "Sin conectividad a internet",
                ip: "unknown",
                wifiAccess: false
            };
        }
        
    } catch (error) {
        console.log(`❌ Error general: ${error.message}`);
        return {
            status: "error",
            message: `Error: ${error.message}`,
            ip: "unknown",
            wifiAccess: false
        };
    }
}

// Función para mostrar resultado (sin alert en iOS Shortcuts)
function showResult(result) {
    let emoji = "❓";
    let title = "Estado VPN";
    
    switch (result.status) {
        case "success":
            emoji = "✅";
            title = "VPN Funcionando";
            break;
        case "error":
            emoji = "❌";
            title = "VPN con Problemas";
            break;
        case "warning":
            emoji = "⚠️";
            title = "Estado Incierto";
            break;
    }
    
    const message = `${emoji} ${title}\n\n` +
                   `📍 IP: ${result.ip}\n` +
                   `🔗 Acceso WiFi: ${result.wifiAccess}\n` +
                   `💬 ${result.message}`;
    
    // No usar alert() en iOS Shortcuts - solo logging
    console.log(message);
    return message;
}

// Ejecutar el test y completar el atajo
testVPNConnection().then(result => {
    const message = showResult(result);
    // OBLIGATORIO: complete() para que funcione en iOS Shortcuts
    complete(message);
}).catch(error => {
    const errorResult = {
        status: "error",
        message: `Error inesperado: ${error.message}`,
        ip: "unknown",
        wifiAccess: false
    };
    const message = showResult(errorResult);
    // OBLIGATORIO: complete() también para errores
    complete(message);
});

// INSTRUCCIONES PARA iOS SHORTCUTS:
/*
1. Abrir app "Atajos" en iOS
2. Tocar "+" para crear nuevo atajo
3. Buscar "Ejecutar JavaScript en página web"
4. Pegar este código completo
5. Cambiar VPN_CONFIG con tus datos reales
6. Guardar atajo como "Test VPN"
7. Ejecutar desde widget o Siri: "Hey Siri, Test VPN"

OPCIONAL - Agregar más acciones al atajo:
- "Hablar texto" para anunciar resultado
- "Enviar mensaje" para notificar resultado
- "Agregar a nota" para guardar log
*/