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

sys.path.insert(0, './protosWait')

import numpy as np
import asyncio
import mysql.connector
import grpc
import logging

from protosWait import waitingTime_pb2, waitingTime_pb2_grpc 

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
zonas = []
## LLAMADA A ENGINE
LLAMADA_ENGINE = "python3 FWQ_Engine.py <host>:<port_kafka> <nummax_visitantes> <host>:<port_waitingserver>"

API_KEY = "47fe4dc689d72a4666d016f08f81dbf3"
CITYS_NAME = ['Callosa de Segura', 'Buenos Aires', 'Brasilia', 'El Cairo', 'Jeddah']
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

def updateUsuario(username, x, y):
    global mydb
    try:
        query = 'UPDATE usuarios SET x = ' + str(x) + ' , y = ' + str(y) + ' WHERE username = \'' + str(username) + '\''
        mycursor = mydb.cursor()
        mycursor.execute(query)

        mydb.commit()

        logging.info(mycursor.rowcount, " usuarios afectados")
    except Exception:
        print("No se puedo establecer conexión con MySql")

def updateAtraccion(id, tiempoEspera):
    global mydb
    query = 'UPDATE atraccion SET tiempo_espera = ' + str(tiempoEspera) + ' WHERE id = ' + str(id)
    try:
        mycursor = mydb.cursor()
        mycursor.execute(query)

        mydb.commit()
        logging.info(mycursor.rowcount, " atracciones afectadas")
    except Exception:
        print("No se puedo establecer conexión con MySql")


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
    async with grpc.aio.insecure_channel(str(host) + ':' + str(port)) as channel:
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
                if upAtr[0] ==  atraccion.id and not atraccion.block:
                    atraccion.tiempoEspera = upAtr[1]
                    updateAtraccion(atraccion.id, atraccion.tiempoEspera)
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
        print(usuariosCola)
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
                print(len(usuariosCola), contadorVisitantes)
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
        print("mov")
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

def consultaAtracciones(atracciones):
    global mydb
    global zonas
    query = "SELECT * FROM `atraccion`"
    mycursor = mydb.cursor()

    mycursor.execute(query)
    data = mycursor.fetchall()

    for x in data:
        atracciones.append(Atraccion(x[0], x[1], x[2], Coordenadas2D(x[3], x[4]), -1))
        zona = definirZona(atracciones[-1].coordenadas.x, atracciones[-1].coordenadas.y)
        atracciones[-1].block = zonas[zona - 1]
        if atracciones[-1].block:
            updateAtraccion(atracciones[-1].id, -1)
        

def consultaUsuarios(usuariosDentro):
    global mydb
    query = "SELECT username, alias, x, y FROM `usuarios`"

    mycursor = mydb.cursor()
    mycursor.execute(query)
    data = mycursor.fetchall()

    # consulta si hay alguno aún dentro del mapa
    for x in data:
        if x[2] != -1:
            usuario = {
                'alias': x[1],
                'username' : x[0],
                'x' : x[2],
                'y' : x[3]
            }
            usuariosDentro.append(usuario)

def consultaBD():
    global atracciones
    global usuariosDentro
    global mydb
    conexion = False
    while conexion == False:
        try:
            mydb = mysql.connector.connect(
                host=host_BD,
                user=user_BD,
                passwd=passwd_BD,
                database=database_BD)

            conexion = True
            consultaAtracciones(atracciones)
            consultaUsuarios(usuariosDentro)
        except Exception as e:
            print(e)
            sleep(5)

# definir temperaturas de las cuatro zonas del parque para ver si son accesibles
def zonasParque():
    global zonas
    for i in range(4):
        j = random.randint(0, len(CITYS_NAME)-1)
        resultado = conectarAPI(CITYS_NAME[j])
        zonas.append(not(resultado >= 20 and resultado <= 30))


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

    # conectar con API WEATHER para saber las zonas que están block o no
    zonasParque()
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
    