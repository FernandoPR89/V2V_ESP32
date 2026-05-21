import os
import sys
import traci
import serial
import time

PUERTO_COM = 'COM9' 
BAUD_RATE = 115200

# 1. ABRIR PUERTO Y ESPERAR EL HANDSHAKE
try:
    # Aumentamos el timeout para la fase de conexión
    esp32_serial = serial.Serial(PUERTO_COM, BAUD_RATE, timeout=1.0)
    print(f"Puerto abierto. Esperando a que el ESP32-S3 (Nodo Edge) reinicie...")
    
    listo = False
    tiempo_inicio = time.time()
    
    # Python escuchará el puerto durante 10 segundos buscando el mensaje del setup() de C++
    while not listo and (time.time() - tiempo_inicio) < 10:
        linea = esp32_serial.readline().decode('utf-8', errors='ignore').strip()
        if linea:
            print(f"[BOOT S3]: {linea}")
            
        if "OK: NODO EDGE S3 LISTO" in linea:
            listo = True
            
    if not listo:
        sys.exit("Error: El ESP32 no respondió a tiempo. Verifica que el código de PlatformIO esté cargado.")
        
    print("\n¡Sincronización exitosa! Arrancando el Gemelo Digital en SUMO...\n")
    
except serial.SerialException:
    sys.exit(f"Error: No se pudo abrir el puerto {PUERTO_COM}.")

# 2. CONFIGURACIÓN DE SUMO
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Por favor, declara la variable 'SUMO_HOME'")

sumoCmd = ["sumo-gui", "-c", "Mapas/NobHill/simulacion_sf.sumocfg"] 

# 3. EJECUCIÓN SINCRONIZADA
def extraer_y_enviar():
    traci.start(sumoCmd)
    paso = 0
    
    # Reducimos el timeout del serial ahora que ya estamos conectados para no frenar la simulación
    esp32_serial.timeout = 0.05 
    
    while paso < 500:
        traci.simulationStep()
        vehiculos_activos = traci.vehicle.getIDList()
        
        for veh_id in vehiculos_activos[:5]:
            x, y = traci.vehicle.getPosition(veh_id)
            velocidad = traci.vehicle.getSpeed(veh_id)
            co2 = traci.vehicle.getCO2Emission(veh_id)
            
            trama = f"{veh_id},{x:.2f},{y:.2f},{velocidad:.2f},{co2:.2f}\n"
            esp32_serial.write(trama.encode('utf-8'))
            
            print(f"Enviado -> {trama.strip()}")
            
            # Leemos la confirmación (ACK) del microcontrolador
            while esp32_serial.in_waiting > 0:
                try:
                    respuesta = esp32_serial.readline().decode('utf-8', errors='ignore').strip()
                    if respuesta:
                        print(f"[MONITOR S3]: {respuesta}")
                except Exception:
                    pass
            
        paso += 1
        
    traci.close()
    esp32_serial.close()

if __name__ == "__main__":
    extraer_y_enviar()