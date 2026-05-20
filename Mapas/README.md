Para crear los archivos .net.xml a partir de los archivos .osm, se puede utilizar el siguiente comando:
## San Francisco
netconvert --osm-files SanFrancisco.osm -o sanfrancisco_v2v.net.xml --geometry.remove --ramps.guess --junctions.join --tls.guess-signals --osm.elevation
## Santa Fe CDMX
netconvert --osm-files SantaFe.osm -o santafe_v2v.net.xml --geometry.remove --ramps.guess --junctions.join --tls.guess-signals --osm.elevation
## Guanajuato
netconvert --osm-files Guanajuato.osm -o guanajuato_v2v.net.xml --geometry.remove --ramps.guess --junctions.join --tls.guess-signals --osm.elevation

Inyectar Tráfico Vehicular (randomTrips.py)
## San Francisco
python "%SUMO_HOME%\tools\randomTrips.py" -n sanfrancisco_v2v.net.xml -r rutas_sf.rou.xml -e 1000 -p 2.0 --additional-files vehiculos.add.xml --trip-attributes="type=\"coche_estandar\"" --validate
## Santa Fe CDMX
python "%SUMO_HOME%\tools\randomTrips.py" -n santafe_v2v.net.xml -r rutas_stfe.rou.xml -e 1000 -p 2.0 --additional-files vehiculos_stfe.add.xml --trip-attributes="type=\"coche_estandar\"" --validate
## Guanajuato
python "%SUMO_HOME%\tools\randomTrips.py" -n guanajuato_v2v.net.xml -r rutas_gto.rou.xml -e 1000 -p 2.0 --additional-files vehiculos_gto.add.xml --trip-attributes="type=\"coche_estandar\"" --validate


¿Qué hace este comando?
-n: Lee tu red de San Francisco.
-r: Genera un nuevo archivo llamado rutas_sf.rou.xml con los caminos que tomarán los vehículos.
-e 1000: Finaliza la inyección de vehículos en el segundo 1000 de simulación.
-p 2.0: Inserta un vehículo nuevo cada 2.0 segundos. (Si quieres más congestión para estresar a tus ESP32-S3 más adelante, baja este valor a 1.0).
--trip-attributes: Asegura que todos los vehículos utilicen el perfil de emisiones que creaste en el Paso 1.
--validate: valida que el vehiculo pueda circular por la red a traves de la implementacion del algoritmo Dijkstra. y de esta forma detectar posibles errores en la red.

Generar simulation_sf.sumocfg
Nota metodológica: El step-length a **0.1** es vital para una arquitectura V2V. Significa que SUMO actualizará la física de los autos cada 100 milisegundos, lo cual te dará una granularidad perfecta cuando empieces a leer la telemetría para enviarla a los nodos ESP32-C3.

