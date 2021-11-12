
from kafka import KafkaProducer
from kafka import KafkaConsumer
from json import dumps
from json import loads
import numpy as np
from time import sleep

# TOPICS DEL ZOOKEEPER
TOPIC_MOVIMIENTO = 'movimiento'
TOPIC_MAPA = 'mapa'
TOPIC_TIEMPO_ESPERA = 'tiempossensores'
TOPIC_INTENTO_ENTRADA = "colaentrada"
TOPIC_PASEN = "pasen"

# CONSUMIDOR JSON
def definirConsumidorJSON(host, port, topic):
    print("Conectando consumidor Kafka...")
    conexion = False
    while(conexion == False):
        try:
            consumidor = KafkaConsumer(
                topic,
                bootstrap_servers=[host + ':' + port],
                auto_offset_reset='latest',
                value_deserializer=lambda x:
                loads(x.decode('utf-8'))  
            )
            conexion = True
        except Exception as e:
            print("No se ha podido conectar Kafka en " + host + ":" + port)
            sleep(5)

    return consumidor

## PRODUCTOR JSON
def definirProductorJSON(host, port):
    print("Creando productor Kafka...")
    conexion = False
    while(conexion == False):
        try:
            productor =  KafkaProducer(
                bootstrap_servers=[host + ':' + port],
                value_serializer=lambda x:
                dumps(x).encode('utf-8')
            )
            conexion = True
        except Exception as e:
            print("No se ha podido conectar Kafka en " + host + ":" + port)
            sleep(5)

    return productor

# CONSUMIDOR EN BYTES
def definirConsumidorBytes(host, port, topic):
    print("Conectando consumidor Kafka...")
    conexion = False
    while(conexion == False):
        try:
            consumidor = KafkaConsumer(
                topic,
                bootstrap_servers=[host + ':' + port],
                auto_offset_reset='latest',
                value_deserializer=lambda x:
                np.frombuffer(x, dtype='U3').reshape(20,20)  
            )
            conexion = True
        except Exception as e:
            print("No se ha podido conectar Kafka en " + host + ":" + port)
            sleep(5)

    return consumidor

## PRODUCTOR EN BYTES
def definirProductorBytes(host, port):
    print("Creando productor Kafka...")
    conexion = False
    while(conexion == False):
        try:
            productor =  KafkaProducer(
                bootstrap_servers=[host + ':' + port],
                value_serializer=lambda x:
                x.tobytes()
            )
            conexion = True
        except Exception as e:
            print("No se ha podido conectar Kafka en " + host + ":" + port)
            sleep(5)
    
    return productor