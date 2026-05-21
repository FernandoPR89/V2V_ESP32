import os
import sys
import sumolib

# Aseguramos la ruta de las herramientas de SUMO
if 'SUMO_HOME' in os.environ:
    tools = os.path.join(os.environ['SUMO_HOME'], 'tools')
    sys.path.append(tools)
else:
    sys.exit("Por favor, declara la variable 'SUMO_HOME'")

def extraer_matriz():
    # 1. Cargamos el mapa topográfico
    ruta_relativa = "Mapas/NobHill/sanfrancisco_v2v.net.xml" 
    
    # CONVERSIÓN A RUTA ABSOLUTA (Esto soluciona el error)
    archivo_red = os.path.abspath(ruta_relativa)
    
    if not os.path.exists(archivo_red):
        sys.exit(f"Error: No se encontró el archivo en la ruta absoluta:\n{archivo_red}")
        
    print(f"Analizando red: {archivo_red}...")
    
    red = sumolib.net.readNet(archivo_red)
    
    nodos = red.getNodes()
    aristas = red.getEdges()
    
    # 2. Diccionarios de traducción (Texto de SUMO -> Entero para C++)
    nodo_a_id = {}
    id_a_nodo = {}
    
    for indice, nodo in enumerate(nodos):
        texto_sumo = nodo.getID()
        nodo_a_id[texto_sumo] = indice
        id_a_nodo[indice] = texto_sumo
        
    num_nodos = len(nodos)
    print(f"Total de Intersecciones (Nodos): {num_nodos}")
    print(f"Total de Calles (Aristas): {len(aristas)}")
    
    # 3. Generamos la lista de adyacencia (Origen, Destino, Distancia)
    grafo_exportar = []
    
    for arista in aristas:
        origen_str = arista.getFromNode().getID()
        destino_str = arista.getToNode().getID()
        
        # Obtenemos la longitud física de la calle en metros
        distancia = arista.getLength() 
        
        origen_id = nodo_a_id[origen_str]
        destino_id = nodo_a_id[destino_str]
        
        # Formato limpio para transmitir por Serial: Origen,Destino,Distancia
        grafo_exportar.append(f"{origen_id},{destino_id},{distancia:.2f}")

    # 4. Guardamos el resultado en un archivo local temporalmente
    with open("matriz_sanfrancisco.txt", "w") as f:
        # La primera línea le dirá al ESP32 cuánta PSRAM reservar
        f.write(f"NODOS:{num_nodos}\n")
        f.write(f"ARISTAS:{len(grafo_exportar)}\n")
        for linea in grafo_exportar:
            f.write(f"{linea}\n")
            
    print("\n¡Extracción completada! Archivo 'matriz_sanfrancisco.txt' generado.")
    print(f"Memoria RAM estimada para C++ (Matriz Densa): {(num_nodos * num_nodos * 4) / 1024:.2f} KB")

if __name__ == "__main__":
    extraer_matriz()