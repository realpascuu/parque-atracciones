from time import sleep
import common.Kafka as Kafka
import sys
import random
import signal

# Ejecución sensor
LLAMADA_SENSOR = "python3 FWQ_Sensor.py <host_broker>:<port_broker> <idAtraccion>"

def enviarDatos(idAtraccion, cola):
    datos = {
        'id' : idAtraccion,
        'cola' : cola
    }
    producer.send(Kafka.TOPIC_TIEMPO_ESPERA, value=datos)

def signal_handler(signal, frame):
    # Controlar control + C 
    print("Apagando Sensor...")
    sleep(1)
    exit()


################ MAIN ##################

# Recuperar host y puerto de el servidor kafka

signal.signal(signal.SIGINT, signal_handler)
try:
    if len(sys.argv) != 3:
        raise Exception

    broker_kafka = sys.argv[1].split(":")
    host = broker_kafka[0]
    port = broker_kafka[1]
    # Recuperar id de la atracción
    idAtraccion = int(sys.argv[2])
except Exception:
    print(LLAMADA_SENSOR)
    exit()
# Definir productor kafka
producer = Kafka.definirProductorJSON(host, port)

while True:
    numero = random.randint(0,60)
    enviarDatos(idAtraccion, numero)
    sleep(8)