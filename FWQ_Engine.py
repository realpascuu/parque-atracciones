from common.Atraccion import Atraccion
from common.Coordenadas2D import Coordenadas2D
import common.Kafka as Kafka
import numpy as np
import threading
import sys
import random
from time import sleep
import signal

import array

sys.path.insert(0, './protosWait')

import numpy as np
import asyncio
import logging
import mysql.connector
import grpc

from protosWait import waitingTime_pb2, waitingTime_pb2_grpc 

host_BD = '192.168.25.1'
user_BD = 'admin'
passwd_BD = 'burguerking'
database_BD = 'parque'

atracciones = []
contadorVisitantes = 0
usuariosDentro = []
## LLAMADA A ENGINE
LLAMADA_ENGINE = "python3 FWQ_Engine.py <host>:<port_kafka> <nummax_visitantes> <host>:<port_waitingserver>"

async def run(host, port):
    async with grpc.aio.insecure_channel(str(host) + ':' + str(port)) as channel:
        global atracciones
        stub = waitingTime_pb2_grpc.WaitingTimeStub(channel)
        
        atraccionesNumpy = np.zeros((len(atracciones),5), dtype=np.int64)

        for x in range(0, len(atracciones)):
            atraccionesNumpy[x, 0] = atracciones[x].id
            atraccionesNumpy[x, 1] = atracciones[x].timec
            atraccionesNumpy[x, 2] = atracciones[x].nvisitors
            atraccionesNumpy[x, 3] = atracciones[x].coordenadas.x
            atraccionesNumpy[x, 4] = atracciones[x].coordenadas.y

        byteatraccion = atraccionesNumpy.tobytes()
        (m, n) = atraccionesNumpy.shape
        conexion = False
        while conexion == False:
            try: 
                user = await stub.giveTime(waitingTime_pb2.EngineRequest(atracciones=byteatraccion, numFilas=m))
                conexion = True
            except Exception as e:
                print("No se ha podido establecer conexión con Servidor Tiempos espera en " + str(host) + ':' + str(port))
                sleep(5)

        atraUpdate = np.frombuffer(user.atracciones, dtype=np.int64).reshape(user.numFilas, 2)
        return atraUpdate

def enviarMapa(mapa):
    producerMapa.send(Kafka.TOPIC_MAPA, value=mapa)

def dibujarAtracciones(mapa, atracciones):
    for atraccion in atracciones:
        mapa[atraccion.coordenadas.x, atraccion.coordenadas.y] = atraccion.tiempoEspera

def comunicarTiempoEspera(mapa, host, port):
    global atracciones
    while True:
        sleep(random.randint(3,8))
        # HARÍA COMUNICACIÓN CON TIEMPO DE ESPERA
        updateAtrac = asyncio.run(run(host, port))
        # almacenarlos en atracciones
        for upAtr in updateAtrac:
            for atraccion in atracciones:
                if upAtr[0] ==  atraccion.id:
                    atraccion.tiempoEspera = upAtr[1]
                    continue
            
        dibujarAtracciones(mapa, atracciones)
        if 'producerMapa' in globals():
            enviarMapa(mapa)

def entradaUsuario(usuario):
    global contadorVisitantes
    print("Bienvenido " + usuario['username'] + "!")
    usuario['x'] = random.randint(0, 19)
    usuario['y'] = random.randint(0, 19)
    contadorVisitantes += 1
    mapa[usuario['x'], usuario['y']] = usuario['alias']
    producerEntrada.send(topic=Kafka.TOPIC_PASEN, value=usuario)

# sacamos usuario de lista de usuarios dentro del parque
def sacarUsuario(usuariosDentro, username):
    for i in range(0, len(usuariosDentro)):
        if usuariosDentro[i]['username'] == username:
            usuariosDentro.pop(i)
            break

# buscamos usuario en lista de usuarios dentro del parque
def buscarUsuario(usuariosDentro, username):
    for i in range(0, len(usuariosDentro)):
        if usuariosDentro[i]['username'] == username:
            return True
    
    return False

def colaEntrada(mapa):
    global contadorVisitantes
    usuariosCola = []
    global usuariosDentro

    for message in consumerEntrada:
        usuario = message.value
        if 'salida' in usuario.keys():
            if buscarUsuario(usuariosDentro, usuario['username']):
                # eliminar usuario del mapa
                for i in range(0,20):
                    for j in range(0, 20):
                        if mapa[i, j] == usuario['alias']:
                            mapa[i, j] = '.'
                print("Hasta pronto " + message.value['username'] + "!")
                # restamos contador porque se ha ido uno y eliminamos
                contadorVisitantes -= 1
                sacarUsuario(usuariosDentro, usuario['username'])
            else:
                # saca usuario en caso de que esté en la cola
                sacarUsuario(usuariosCola, usuario['username'])
            # meter usuarios de la cola hasta que no hayan más o no quepan 
            while (not len(usuariosCola) == 0) and contadorVisitantes < max_visitantes:
                entradaUsuario(usuariosCola[0])
                usuariosDentro.append(usuariosCola[0])
                usuariosCola.pop(0)
        # detectar duplicados de usuarios
        elif not 'salida' in usuario.keys() and buscarUsuario(usuariosDentro, usuario['username']):
            print(usuario['username'] + " ya está dentro!!")
        # usuario cabe y aún no está dentro
        elif not 'salida' in usuario.keys() and contadorVisitantes < max_visitantes and usuario['x'] == -1:
            entradaUsuario(usuario)
            usuariosDentro.append(usuario)
        # usuario no cabe y aún no está dentro
        elif not 'salida' in usuario.keys() and contadorVisitantes >= max_visitantes and usuario['x'] == -1:
            if not buscarUsuario(usuariosCola, usuario['username']):
                usuariosCola.append(usuario)
                # manda mensaje de que está dentro de la cola
                usuarioCola = {
                    'alias': usuario['alias'],
                    'username' : usuario['username'],
                    'x' : usuario['x'],
                    'y' : usuario['y'],
                    'cola' : 'Estás el número ' + str(len(usuariosCola)) + ' en la cola!'
                }
                producerEntrada.send(topic=Kafka.TOPIC_PASEN, value=usuarioCola)
        # mostrar usuarios dentro y en cola
        logging.info("Usuarios dentro: ")
        logging.info(usuariosDentro)
        logging.info("Usuarios en cola: ")
        logging.info(usuariosCola)
        # aceptar mensaje como leído
        consumerEntrada.commit()

# Tener en cuenta los movimientos circulares
def limitesMapa(x):
    if x >= 20:
        return 0
    elif x <= -1:
        return 19
    else:
        return x

def obtieneMovimiento(mapa):
    global contadorVisitantes
    global usuariosDentro

    for message in consumerMov:
        ## OBTIENE EL NUEVO MAPA
        usuario = message.value
        # En caso de fallo de engine, vuelve a obtener los usuarios que se encontraban dentro del parque
        if not buscarUsuario(usuariosDentro, usuario['username']):
            usuariosDentro.append(usuario)
            contadorVisitantes += 1
        # eliminar alias en el mapa
        for i in range(0,20):
            for j in range(0, 20):
                if mapa[i, j] == usuario['alias']:
                    mapa[i, j] = '.'
        # añadir en el mapa el movimiento actual
        mapa[usuario['x'], usuario['y']] = usuario['alias']
        # actualizar datos de colas de espera
        dibujarAtracciones(mapa, atracciones)
        ## ENVÍA EL MAPA A LOS USUARIOS
        enviarMapa(mapa)
        consumerMov.commit()

def signal_handler(signal, frame):
    # Controlar control + C 
    print("Apagando Engine...")
    sleep(1)
    sys.exit(0)

def consultaBD():
    global atracciones
    conexion = False
    while conexion == False:
        try:
            mydb = mysql.connector.connect(
                host=host_BD,
                user=user_BD,
                passwd=passwd_BD,
                database=database_BD)

            conexion = True
            mycursor = mydb.cursor()
            
            query = "SELECT * FROM `atraccion`"

            mycursor.execute(query)
            data = mycursor.fetchall()

            for x in data:
                atracciones.append(Atraccion(x[0], x[1], x[2], Coordenadas2D(x[3], x[4])))
        except Exception as e:
            print(e)
            sleep(5)

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    #logging.basicConfig(level=logging.INFO)
    try:
        if len(sys.argv) != 4:
            raise Exception
        # Host y puerto servidor kafka
        broker_kafka = sys.argv[1].split(":")
        host_broker = broker_kafka[0]
        port_broker = broker_kafka[1]

        # Número máximo de visitantes
        max_visitantes = int(sys.argv[2])

        # Host y puerto servidor tiempos espera
        tiempos_espera = sys.argv[3].split(":")
        host_tiempos = tiempos_espera[0]
        port_tiempos = tiempos_espera[1]
    except Exception:
        print(LLAMADA_ENGINE)
        exit()

    # CARGAR MAPA DE LA BD (HACER LO SIGUIENTE)
    # 1 Carga atracciones de la BD
    hiloConsultaBD = threading.Thread(
        target=consultaBD,
        name="mysql"
    )
    hiloConsultaBD.start()
    
    # Mapa vacío
    mapa = np.full((20,20), str('.'), np.dtype('U3'))
    ## COMUNICACIÓN CON EL SERVIDOR DE TIEMPOS DE ESPERA
    hiloTiemposEspera = threading.Thread(
            target=comunicarTiempoEspera,
            args=(mapa, host_tiempos, port_tiempos, ),
            name="espera"
        )
    #hiloTiemposEspera.daemon = True
    hiloTiemposEspera.start()

    # DEFINIR CONSUMIDOR KAFKA
    consumerMov = Kafka.definirConsumidorJSON(host_broker, port_broker, Kafka.TOPIC_MOVIMIENTO, 'latest', 'engine_movimiento')
    consumerEntrada = Kafka.definirConsumidorJSON(host_broker, port_broker, Kafka.TOPIC_INTENTO_ENTRADA, 'earliest', 'engine_entrada')
    # DEFINIR PRODUCTOR KAFKA
    producerEntrada = Kafka.definirProductorJSON(host_broker, port_broker)
    producerMapa = Kafka.definirProductorBytes(host_broker, port_broker)

    ## COMUNICARSE CON LA COLA DE ENTRADA DE VISITANTES
    hiloEntrada = threading.Thread(
        target=colaEntrada,
        args=(mapa, ),
        name="entrada"
    )
    #hiloEntrada.daemon = True
    hiloEntrada.start()

    hiloObtieneMovimiento = threading.Thread(
        target=obtieneMovimiento,
        args=(mapa, ),
        name="movimiento"
    )
    #hiloObtieneMovimiento.daemon = True
    hiloObtieneMovimiento.start()
    