from common.Atraccion import Atraccion
from common.Coordenadas2D import Coordenadas2D
import common.Kafka as Kafka
import numpy as np
import threading
import sys
import random
from time import sleep
import signal

import requests
from requests.exceptions import RequestException

from common.Usuario import Usuario

import numpy as np
import asyncio
import mysql.connector
import grpc
import logging

sys.path.append(sys.path[0].split('api_engine')[0] + '/protosWait')

from protosWait import waitingTime_pb2, waitingTime_pb2_grpc 

'''import os 
os.environ['GRPC_TRACE'] = 'all' 
os.environ['GRPC_VERBOSITY'] = 'DEBUG' 
'''
# variables BD MySQL
host_BD = 'localhost'
user_BD = 'admin'
passwd_BD = 'burguerking'
database_BD = 'parque'

## variables globales
atracciones = []
contadorVisitantes = 0
usuariosDentro = []
mydb = None
""" 
ZONAS:
1. 0-9, 0-9 
2. 10-19, 0-9
3. 0-9, 10-19
4. 10-19, 10-19
 """
zonas = [0, 0, 0, 0]

## LLAMADA A ENGINE
LLAMADA_ENGINE = "python3 FWQ_Engine.py <host>:<port_kafka> <nummax_visitantes> <host>:<port_waitingserver>"

API_KEY = "47fe4dc689d72a4666d016f08f81dbf3"
GRADOS_KELVIN = 273.15

## DEFINE LA CADENA DE LLAMADA A LA API
def cadenaAPI(city):
    return "https://api.openweathermap.org/data/2.5/weather?q=" + city + "&appid=" + API_KEY

# CONVERSIÓN DE KELVIN A GRADOS CENTÍGRADOS
def convertirKelvinAGrados(kelvin):
    return kelvin - GRADOS_KELVIN

# LLAMADA A LA API, DEVUELVE LA TEMPERATURA DE LA CIUDAD
def conectarAPI(city):
    cadenaBusqueda = cadenaAPI(city)
    try:
        respuesta = requests.get(cadenaBusqueda).json()
    except RequestException as e:
        print(e)
    
    return round(convertirKelvinAGrados(respuesta['main']['temp']), 1)

def actualizarZona(zona, ciudad):
    block = False
    temp = conectarAPI(ciudad)
    if temp < 20 or temp > 30:
        block = True

    try:
        mydb = mysql.connector.connect(
        host=host_BD,
        user=user_BD,
        passwd=passwd_BD,
        database=database_BD
        )
        mycursor = mydb.cursor()
        query = 'UPDATE zonas SET block = ' + str(block) + ' WHERE zona = ' + str(zona) + ';'
        mycursor.execute(query)
        mydb.commit()

        return (True, block)
    except Exception as e:
        print(e)
        return (False, block)

def definirZona(x, y):
    if x < 10:
        if y < 10:
            return 1
        else:
            return 3
    else:
        if y < 10:
            return 2
        else:
            return 4

def actualizarZonas():
    global zonas

    while(True):
        mydb = mysql.connector.connect(
            host=host_BD,
            user=user_BD,
            passwd=passwd_BD,
            database=database_BD)

        query = 'SELECT * FROM zonas'
        try:
            mycursor = mydb.cursor()
            mycursor.execute(query)
            data = mycursor.fetchall()
            for i in range(4):
                zonas[i] = data[i][1]
        except Exception as e:
            print(e)
            print("No se puedo establecer conexión con MySql")
        sleep(1)

def updateUsuario(username, x, y):
    try:
        mydb = mysql.connector.connect(
        host=host_BD,
        user=user_BD,
        passwd=passwd_BD,
        database=database_BD
        )
        query = 'UPDATE usuarios SET x = ' + str(x) + ' , y = ' + str(y) + ' WHERE username = \'' + str(username) + '\''
        mycursor = mydb.cursor()
        mycursor.execute(query)

        mydb.commit()

        logging.info(mycursor.rowcount, " usuarios afectados")
    except Exception as e:
        print(e)
        print("No se pudo actualizar usuario")

def updateAtraccion(id, tiempoEspera, block):
    if block:
        tiempoEspera = -1
    query = 'UPDATE atraccion SET tiempo_espera = ' + str(tiempoEspera) + ' WHERE id = ' + str(id)
    try:
        mydb = mysql.connector.connect(
        host=host_BD,
        user=user_BD,
        passwd=passwd_BD,
        database=database_BD
        )
        mycursor = mydb.cursor()
        mycursor.execute(query)

        mydb.commit()
        logging.info(mycursor.rowcount, " atracciones afectadas")
    except Exception as e:
        print(e)
        print("No se pudo actualizar atracción")


def datosParaEnviarPorCanal(atracciones):
    atraccionesNumpy = np.zeros((len(atracciones),5), dtype=np.int64)

    for x in range(0, len(atracciones)):
        atraccionesNumpy[x, 0] = atracciones[x].id
        atraccionesNumpy[x, 1] = atracciones[x].timec
        atraccionesNumpy[x, 2] = atracciones[x].nvisitors
        atraccionesNumpy[x, 3] = atracciones[x].coordenadas.x
        atraccionesNumpy[x, 4] = atracciones[x].coordenadas.y
    return atraccionesNumpy

async def run(host, port):
    with open('clavesTimeServer/server.crt', 'rb') as f:
        trusted_certs = f.read()
    
    cert_cn = "tiempoespera.org"
    options = (('grpc.ssl_target_name_override', cert_cn),('grpc.default_authority', cert_cn),)
    credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs, private_key=None, certificate_chain=None)
    async with grpc.aio.secure_channel(host + ':' + port, credentials, options) as channel:
        global atracciones
        stub = waitingTime_pb2_grpc.WaitingTimeStub(channel)
        
        # cambiar datos para poder pasarlos en bytes
        atraccionesNumpy = datosParaEnviarPorCanal(atracciones)
        byteatraccion = atraccionesNumpy.tobytes()
        (m, n) = atraccionesNumpy.shape
        conexion = False
        while conexion == False:
            try:
                # intentar conexión con Registry 
                user = await stub.giveTime(waitingTime_pb2.EngineRequest(atracciones=byteatraccion, numFilas=m))
                # Conexión realizada
                conexion = True
            except Exception as e:
                # error conexión con Servidor
                print(e)
                print("No se ha podido establecer conexión con Servidor Tiempos espera en " + str(host) + ':' + str(port))
                sleep(5)
        # Transfromar datos
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
        # COMUNICACIÓN CON TIEMPO DE ESPERA
        updateAtrac = asyncio.run(run(host, port))
        # almacenarlos en atracciones [0]=ID, [1]=TIEMPOS_ESPERA
        for upAtr in updateAtrac:
            for atraccion in atracciones:
                atraccion.block = zonas[definirZona(atraccion.coordenadas.x, atraccion.coordenadas.y) - 1]
                if upAtr[0] ==  atraccion.id:
                    if not atraccion.block:
                        atraccion.tiempoEspera = upAtr[1]
                    else: 
                        atraccion.tiempoEspera = -1
                updateAtraccion(atraccion.id, atraccion.tiempoEspera, atraccion.block)
                continue
            
        dibujarAtracciones(mapa, atracciones)
        # soluciona error que el hilo se adelante e intente enviar mapa cuando no se ha producido el producer
        if 'producerMapa' in globals():
            enviarMapa(mapa)

def entradaUsuario(usuario):
    global contadorVisitantes
    global zonas
    print('Bienvenido ' + usuario['username'] + '!')
    # entrada aleatoria usuario no entrando en posición no accesible
    posCorrecta = False
    while(not posCorrecta):
        usuario['x'] = random.randint(0, 19)
        usuario['y'] = random.randint(0, 19)
        zona = definirZona(usuario['x'], usuario['y'])
        posCorrecta = not zonas[zona - 1]

    contadorVisitantes += 1
    updateUsuario(usuario['username'], usuario['x'], usuario['y'])
    # añadimos usuario en el mapa pintado
    mapa[usuario['x'], usuario['y']] = usuario['alias']
    # envío de mapa
    producerEntrada.send(topic=Kafka.TOPIC_PASEN, value=usuario)

# sacamos usuario de lista de usuarios dentro del parque
def sacarUsuario(usuariosDentro, username):
    if len(usuariosDentro) > 0:
        for i in range(len(usuariosDentro)):
            if usuariosDentro[i]['username'] == username:
                usuariosDentro.pop(i)
                break

# buscamos usuario en lista de usuarios dentro del parque
def buscarUsuario(usuariosDentro, username):
    if len(usuariosDentro) > 0:
        for i in range(len(usuariosDentro)):
            if usuariosDentro[i]['username'] == username:
                return True
        
    return False

def enviarMensajeUsuarioCola(usuario, pos):
    usuarioCola = {
        'alias': usuario['alias'],
        'username' : usuario['username'],
        'x' : usuario['x'],
        'y' : usuario['y'],
        'cola' : 'Estás el número ' + str(pos) + ' en la cola!'
    }
    producerEntrada.send(topic=Kafka.TOPIC_PASEN, value=usuarioCola)

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
                print('Hasta pronto ' + message.value['username'] + '!')
                # sacar en bd
                updateUsuario(usuario['username'], -1 ,-1)
                # restamos contador porque se ha ido uno y eliminamos
                if contadorVisitantes > 0:
                    contadorVisitantes -= 1
                sacarUsuario(usuariosDentro, usuario['username'])

                # meter usuarios de la cola hasta que no hayan más o no quepan
                while (not len(usuariosCola) == 0) and contadorVisitantes < max_visitantes:
                    entradaUsuario(usuariosCola[0])
                    usuariosDentro.append(usuariosCola[0])
                    usuariosCola.pop(0)
            else:
                # saca usuario en caso de que esté en la cola
                updateUsuario(usuario['username'], -1 ,-1)
                sacarUsuario(usuariosCola, usuario['username'])
            # enviar mensaje de avance de cola
            i = 0
            for usuario in usuariosCola:
                i += 1
                enviarMensajeUsuarioCola(usuario, i)
        # detectar duplicados de usuarios
        elif buscarUsuario(usuariosDentro, usuario['username']):
            print(usuario['username'] + " ya está dentro!!")
        # usuario cabe y aún no está dentro
        elif contadorVisitantes < max_visitantes and usuario['x'] == -1:
            entradaUsuario(usuario)
            usuariosDentro.append(usuario)
        # usuario no cabe y aún no está dentro
        elif contadorVisitantes >= max_visitantes and usuario['x'] == -1:
            if not buscarUsuario(usuariosCola, usuario['username']):
                print('usuario en cola')
                usuariosCola.append(usuario)
                # manda mensaje de que está dentro de la cola
                enviarMensajeUsuarioCola(usuario, len(usuariosCola))
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
        # eliminar alias en el mapa
        for i in range(0,20):
            for j in range(0, 20):
                if mapa[i, j] == usuario['alias']:
                    mapa[i, j] = '.'
        # añadir en el mapa el movimiento actual
        mapa[usuario['x'], usuario['y']] = usuario['alias']
        # actualizamos en base de datos
        updateUsuario(usuario['username'], usuario['x'], usuario['y'])
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

def consultaAtracciones():
    global zonas
    try:
        mydb = mysql.connector.connect(
                    host=host_BD,
                    user=user_BD,
                    passwd=passwd_BD,
                    database=database_BD)

        query = 'SELECT id, x, y, tiempo_espera, timec, nvisitors FROM atraccion'
        mycursor = mydb.cursor()

        mycursor.execute(query)
        return mycursor.fetchall()
    except Exception as e:
        raise e

def consultaUsuarios():
    try:
        mydb = mysql.connector.connect(
                    host=host_BD,
                    user=user_BD,
                    passwd=passwd_BD,
                    database=database_BD)

        query = 'SELECT username, alias, x, y FROM usuarios WHERE x != -1'

        mycursor = mydb.cursor()
        mycursor.execute(query)
        return mycursor.fetchall()
    except Exception as e:
        raise e

def consultaBD():
    global atracciones
    global usuariosDentro
    conexion = False
    while conexion == False:
        try:
            # obtener valores actuales de las atracciones
            conAtracciones = consultaAtracciones()

            for x in conAtracciones:
                atracciones.append(Atraccion(x[0], x[4], x[5], Coordenadas2D(x[1], x[2]), x[3]))
                zona = definirZona(atracciones[-1].coordenadas.x, atracciones[-1].coordenadas.y)
                atracciones[-1].block = zonas[zona - 1]
                updateAtraccion(atracciones[-1].id, -1, atracciones[-1].block)

            # obtener valores de los usuarios
            conUsuarios = consultaUsuarios()
            # consulta si hay algún usuario aún dentro del mapa
            for x in conUsuarios:
                usuario = {
                    'alias': x[1],
                    'username' : x[0],
                    'x' : x[2],
                    'y' : x[3]
                }
                usuariosDentro.append(usuario)

            conexion = True
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

    # CARGAR ZONAS BLOQUEADAS
    hiloActualizarBloqueoZonas = threading.Thread(
        target=actualizarZonas,
        name="zonas"
    )
    hiloActualizarBloqueoZonas.start()

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