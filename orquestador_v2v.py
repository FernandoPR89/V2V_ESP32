import os
import sys
import traci
import serial
import time
import sumolib

PUERTO_COM = 'COM10' 
BAUD_RATE = 115200

# 1. ABRIR PUERTO Y ESPERAR EL HANDSHAKE
try:
    esp32_serial = serial.Serial(PUERTO_COM, BAUD_RATE, timeout=1.0)
    print(f"Puerto abierto. Esperando a que el ESP32-S3 (Nodo Edge) reinicie...")
    
    listo = False
    tiempo_inicio = time.time()
    
    while not listo and (time.time() - tiempo_inicio) < 10:
        linea = esp32_serial.readline().decode('utf-8', errors='ignore').strip()
        if "OK: NODO EDGE S3 LISTO" in linea:
            listo = True
            
    if not listo:
        sys.exit("Error: El ESP32 no respondió a tiempo.")
        
    print("\n¡Sincronización exitosa! Iniciando inyección del mapa en PSRAM...\n")
    
# --- NUEVA FUNCIÓN: INYECCIÓN DEL MAPA ---
    with open("matriz_sanfrancisco.txt", "r") as f:
        lineas_mapa = f.readlines()
        
    for i, linea in enumerate(lineas_mapa):
        trama = linea.strip() + "\n"
        esp32_serial.write(trama.encode('utf-8'))
        
        ack_recibido = False
        # Esperamos respuesta con límite de tiempo interno del puerto serial
        while not ack_recibido:
            linea_cruda = esp32_serial.readline()
            if linea_cruda:
                respuesta = linea_cruda.decode('utf-8', errors='ignore').strip()
                
                if respuesta == "ACK_MAPA" or respuesta == "MAPA_COMPLETO":
                    ack_recibido = True
                elif respuesta:
                    # ESTO ES VITAL: Si el ESP32 manda un error o texto diferente, lo imprimimos
                    print(f"[S3 EDGE]: {respuesta}")
                
        if i % 500 == 0:
            print(f"Progreso de carga: {i}/{len(lineas_mapa)} líneas inyectadas...")
            
    print("\n¡Mapa cargado exitosamente en el hardware Edge!")

    # --- NUEVO: ATRAPAR LOS LOGS DEL ALGORITMO GWO ---
    print("\n--- INICIALIZANDO ALGORITMO GWO ---")
    
    # Python escuchará indefinidamente hasta que el ESP32 termine sus cálculos
    optimizacion_lista = False
    while not optimizacion_lista:
        linea_cruda = esp32_serial.readline()
        if linea_cruda:
            linea_gwo = linea_cruda.decode('utf-8', errors='ignore').strip()
            if linea_gwo:
                print(f"[EDGE LOG]: {linea_gwo}")
                
                # Buscamos la frase exacta que imprime tu main.cpp al terminar
                if "Optimizacion finalizada" in linea_gwo:
                    optimizacion_lista = True
                
    print("-----------------------------------\n")
    print("Arrancando el Gemelo Digital en SUMO...")
    
except serial.SerialException:
    sys.exit(f"Error: No se pudo abrir el puerto {PUERTO_COM}.")

# 2. CONFIGURACIÓN DE SUMO
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Por favor, declara la variable 'SUMO_HOME'")

sumoCmd = ["sumo-gui", "-c", "Mapas/NobHill/simulacion_sf.sumocfg"] 


# --- NUEVA PREPARACIÓN DEL DICCIONARIO URBANO ---
print("Cargando base de datos topográfica en Python...")
ruta_red = r"C:\Users\Fernando\Documents\PHD\V2V_ESP32\Mapas\NobHill\sanfrancisco_v2v.net.xml"
red = sumolib.net.readNet(ruta_red)

# Reconstruimos el diccionario id-nodo idéntico al del extractor
nodo_a_id = {nodo.getID(): indice for indice, nodo in enumerate(red.getNodes())}
id_a_nodo = {indice: nodo.getID() for indice, nodo in enumerate(red.getNodes())}

# 3. EJECUCIÓN SINCRONIZADA
def extraer_y_enviar():
    traci.start(sumoCmd)
    paso = 0
    esp32_serial.timeout = 0.05 
    
    # Aumentamos a 5000 pasos (aprox 8 minutos de simulación)
    while paso < 5000:
        traci.simulationStep()
        vehiculos_activos = traci.vehicle.getIDList()
        
        for veh_id in vehiculos_activos[:5]:
            edge_id = traci.vehicle.getRoadID(veh_id)
            if edge_id.startswith(":"):
                continue
                
            co2 = traci.vehicle.getCO2Emission(veh_id)
            
            try:
                # 1. Nodos actuales
                edge = red.getEdge(edge_id)
                origen_id = nodo_a_id[edge.getFromNode().getID()]
                destino_id = nodo_a_id[edge.getToNode().getID()]
                
                # 2. NUEVO: Obtenemos el destino final real de la mente del conductor
                ruta_edges = traci.vehicle.getRoute(veh_id)
                edge_final = red.getEdge(ruta_edges[-1])
                destino_final_id = nodo_a_id[edge_final.getToNode().getID()]
                
                # 3. Trama con 4 datos: Vehículo, Origen, Destino_Actual, Destino_Final, CO2
                trama = f"{veh_id},{origen_id},{destino_id},{destino_final_id},{co2:.2f}\n"
                esp32_serial.write(trama.encode('utf-8'))
                
            except KeyError:
                continue
            
            # Interceptor de rutas
            while esp32_serial.in_waiting > 0:
                try:
                    respuesta = esp32_serial.readline().decode('utf-8', errors='ignore').strip()
                    if respuesta:
                        if respuesta.startswith("NUEVA_RUTA:"):
                            datos = respuesta.split(":")[1].split(",")
                            veh_target = datos[0]
                            ruta_nodos = datos[1:]
                            
                            if len(ruta_nodos) > 1:
                                calles_sumo = []
                                
                                # NUEVO: TraCI exige empezar por la calle donde estamos parados
                                calle_actual = traci.vehicle.getRoadID(veh_target)
                                calles_sumo.append(calle_actual)
                                
                                for j in range(len(ruta_nodos) - 1):
                                    n_origen = id_a_nodo[int(ruta_nodos[j])]
                                    n_destino = id_a_nodo[int(ruta_nodos[j+1])]
                                    
                                    for calle_saliente in red.getNode(n_origen).getOutgoing():
                                        if calle_saliente.getToNode().getID() == n_destino:
                                            calles_sumo.append(calle_saliente.getID())
                                            break
                                
                                if len(calles_sumo) > 1:
                                    print(f"\n[>>>] APLICANDO DESVÍO AL VEHÍCULO {veh_target} [<<<]")
                                    print(f"[>>>] RUTA: {calles_sumo} [<<<]\n") # <-- AGREGADO
                                    try:
                                        traci.vehicle.setRoute(veh_target, calles_sumo)
                                        print("[OK] TraCI aceptó la nueva ruta.")
                                    except Exception as e:
                                        print(f"[ERROR] TraCI rechazó la ruta: {e}")
                        else:
                            print(f"[MONITOR S3]: {respuesta}")
                except Exception as e:
                    print(f"[ERROR PYTHON]: {e}") # Para no estar ciegos ante errores de TraCI
            
        paso += 1
        
    traci.close()
    esp32_serial.close()

if __name__ == "__main__":
    extraer_y_enviar()