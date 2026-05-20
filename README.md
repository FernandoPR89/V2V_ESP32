[ FASE 1: Formulación del Problema y Modelado ]
      |
      +---> Definición del G-CVRP (Green Vehicular Routing Problem).
      +---> Modelado matemático de emisiones (CO2) vs. Latencia V2V.
      |
      v
[ FASE 2: Diseño del Gemelo Digital (Digital Twin) ]
      |
      +---> Creación del escenario urbano complejo en SUMO.
      +---> Scripting en Python con TraCI para la extracción de estados.
      |
      v
[ FASE 3: Desarrollo de la Arquitectura HiL (Hardware-in-the-Loop) ]
      |
      +---> Programación del ESP32-S3 como pasarela Serial y Nodo Edge.
      +---> Configuración de la red ESP-NOW con los ESP32-C3.
      +---> Pruebas de sincronización y resolución de errores de comunicación.
      |
      v
[ FASE 4: Implementación y Sintonización de Metaheurísticas ]
      |
      +---> Codificación en C++/MicroPython de GA, GWO y MMAS en el S3.
      +---> Uso intensivo de la PSRAM para evitar desbordamientos.
      +---> Ajuste de hiperparámetros para balancear tiempo de cómputo y calidad.
      |
      v
[ FASE 5: Experimentación y Extracción de Métricas ]
      |
      +---> Ejecución de los 3 algoritmos bajo las mismas condiciones de tráfico.
      +---> Medición empírica en hardware (ms) del tiempo de convergencia.
      +---> Medición en SUMO de la reducción total de emisiones de CO2.
      |
      v
[ FASE 6: Análisis Comparativo y Conclusiones ]
      |
      +---> Evaluación del Trade-off: ¿Vale la pena el costo computacional 
            del MMAS por la reducción de CO2 lograda frente a GWO/GA?
      +---> Redacción del manuscrito y validación de robustez metodológica.