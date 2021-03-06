import common.Kafka as Kafka 
import sys
import numpy as np
from common.Atraccion import Atraccion
from common.Coordenadas2D import Coordenadas2D
import signal
from time import sleep
import threading

sys.path.insert(0, './protosWait')

import asyncio
import numpy as np
import logging
from common.Atraccion import Atraccion
import grpc
from protosWait import waitingTime_pb2, waitingTime_pb2_grpc

from concurrent import futures

# Ejeccución waiting server
LLAMADA_WAITING = "python3 FWQ_WaitingTimeServer.py <puerto_engine> <host_broker>:<port_broker>"

atracciones = []

_cleanup_coroutines = []
class WaitingTime(waitingTime_pb2_grpc.WaitingTimeServicer):
    async def giveTime(self, request: waitingTime_pb2.EngineRequest, context: grpc.aio.ServicerContext) -> waitingTime_pb2.TimeReply:
        atraccionesEngine = np.frombuffer(request.atracciones, dtype=np.int64).reshape(request.numFilas, 5)
        print('Calculando...')
        global atracciones
        datosEngine = []
        for x in atraccionesEngine:
            datosEngine.append(Atraccion(x[0],x[1],x[2], Coordenadas2D(x[3],x[4]), -1))

        datos = []
        
        for actAtraccion in datosEngine:
            for atraccion in atracciones:
                if atraccion.id == actAtraccion.id:
                    datos.append([atraccion.id, getTime(actAtraccion.timec, actAtraccion.nvisitors, atraccion.cola)])
        
        datosNumpy = np.array(datos, dtype=np.int64)
        m = datosNumpy.shape
        byteAtraccion = datosNumpy.tobytes()
        return waitingTime_pb2.TimeReply(atracciones=byteAtraccion, numFilas=m[0])

def obtieneInfo():
    global atracciones
    # Definir el consumidor
    consumer = Kafka.definirConsumidorJSON(host, port, Kafka.TOPIC_TIEMPO_ESPERA, 'earliest', 'waiting_server')
    while True:
        for message in consumer:
            exists = False
            for atraccion in atracciones:
                if atraccion.id == int(message.value['id']):
                    atraccion.cola = int(message.value['cola'])
                    exists = True
            if not exists:
                nuevaAtraccion = Atraccion(int(message.value['id']), -1, -1, Coordenadas2D(-1,-1), -1)
                nuevaAtraccion.cola = int(message.value['cola'])
                atracciones.append(nuevaAtraccion)
            consumer.commit()

async def serve(port) -> None:
    listen_addr = '[::]:' + port
    # abrimos la clave privada
    with open('clavesTimeServer/server.key', 'rb') as f:
        private_key = f.read()
    # abrimos el certificado
    with open('clavesTimeServer/server.crt', 'rb') as f:
        certificate_chain = f.read()
    server_credentials = grpc.ssl_server_credentials(((private_key, certificate_chain,),))
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    waitingTime_pb2_grpc.add_WaitingTimeServicer_to_server(WaitingTime(), server)
    
    server.add_secure_port(listen_addr, server_credentials)
    logging.info("Escuchando en %s", listen_addr)
    await server.start()

    async def server_apagado():
        logging.info("Cerrando...")

    _cleanup_coroutines.append(server_apagado)
    await server.wait_for_termination() 
    
def getTime(cycle_time,visitors,cola):
    if cola != 0:
        return (cycle_time*visitors/cola)
    else:
        return 0


def signal_handler(signal, frame):
    # Controlar control + C 
    print("Apagando Servidor de tiempos de espera...")
    sleep(1)
    exit()

def conexionEngine(port):
    try:
        asyncio.run(serve(port))
    finally:
        asyncio.run(*_cleanup_coroutines)


if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        if len(sys.argv) != 3:
            raise Exception
        # Obtener puerto a la escucha de gRPC con Engine
        listen_port = sys.argv[1]
        
        # Obtener host y puerto kafka
        broken_kafka = sys.argv[2].split(":")
        host = broken_kafka[0]
        port = broken_kafka[1]
    except Exception:
        print(LLAMADA_WAITING)
        exit()
    
    # Obtiene información de los sensores 
    hiloEngine = threading.Thread(
        target=conexionEngine,
        args=(listen_port, ),
        daemon=True
    )    
    hiloEngine.daemon = True
    hiloEngine.start()

    obtieneInfo()