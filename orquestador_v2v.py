import os
import sys
import traci
import serial
import time

# --- CONFIGURACIÓN DEL PUERTO SERIAL ---
PUERTO_COM = 'COM9' 
BAUD_RATE = 115200

try:
    esp32_serial = serial.Serial(PUERTO_COM, BAUD_RATE, timeout=0.1)
    
    # --- LA MAGIA CONTRA EL RESET ---
    # Esto evita que el ESP32 se reinicie al conectar Python
    esp32_serial.setDTR(False)
    esp32_serial.setRTS(False)
    
    time.sleep(2) 
    print(f"Conectado exitosamente al ESP32-S3 en el puerto {PUERTO_COM}")
except serial.SerialException:
    sys.exit(f"Error: No se pudo abrir el puerto {PUERTO_COM}. Verifica la conexión USB.")

if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Por favor, declara la variable 'SUMO_HOME'")

# Si prefieres ver los carritos moverse mientras envías datos, 
# cambia "sumo" por "sumo-gui"
sumoCmd = ["sumo-gui", "-c", "Mapas/NobHill/simulacion_sf.sumocfg"] 

def extraer_y_enviar():
    traci.start(sumoCmd)
    paso = 0
    
    while paso < 500:
        traci.simulationStep()
        vehiculos_activos = traci.vehicle.getIDList()
        
        for veh_id in vehiculos_activos[:5]:
            x, y = traci.vehicle.getPosition(veh_id)
            velocidad = traci.vehicle.getSpeed(veh_id)
            co2 = traci.vehicle.getCO2Emission(veh_id)
            
            trama = f"{veh_id},{x:.2f},{y:.2f},{velocidad:.2f},{co2:.2f}\n"
            esp32_serial.write(trama.encode('utf-8'))
            
            # 1. Recuperamos el print para ver qué envía Python
            print(f"Enviado -> {trama.strip()}")
            
            time.sleep(0.01) 
            
            while esp32_serial.in_waiting > 0:
                try:
                    # 2. Ignoramos errores de decodificación por si llega basura serial
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