from time import sleep

from werkzeug.wrappers import request
from common.Coordenadas2D import Coordenadas2D
import common.Kafka as Kafka
import threading
from numpy import *
import random
import signal
import hashlib
import sys
import requests
import json

sys.path.insert(0, './protosRegistry')

import asyncio
from getpass import getpass
import grpc
from protosRegistry import register_pb2, register_pb2_grpc

from common.Usuario import Usuario

# no permitir warnings provenientes de la conexión con la api(al hacerla nosotros confiamos en ella) 
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

## LLAMADA A Visitor
LLAMADA_VISITOR = "python3 FWQ_Visitor.py <host>:<port_registry> <host>:<port_kafka>"
URL_API_REGISTRY = 'https://localhost:5005'
class PasswordException(Exception):
    def __init__(self, mensaje):
        self.mensaje = mensaje
    pass

def menu():
    print("BIENVENIDO AL PARQUE DE ATRACCIONES")
    print("""------------- MENÚ ------------------------
    1. Registro (socket)
    2. Inicio Sesión (socket)
    3. Editar usuario (socket)
    4. Registro (https)
    5. Inicio Sesión (https)
    6. Editar usuario (https)
    0. Salir
        """)
    return input("¿Qué desea hacer? ")

def errorInput():
    print('VALOR INCORRECTO!')
    print('Introduce 1 para registrarte (socket)')
    print('Introduce 2 para iniciar sesión (socket)')
    print('Introduce 3 para editar usuario (socket)')
    print('Introduce 4 para registrarte (https)')
    print('Introduce 5 para iniciar sesión (https)')
    print('Introduce 6 para editar usuario (https)')

def crearPassword():
    password = getpass("Introduce contraseña: ")
    password2 = getpass("Vuelve a introducir la contraseña: ")
    if (password != password2):
        raise PasswordException("Error! Las contraseñas no coinciden")
    return password

async def registro(channel):
    stub = register_pb2_grpc.RegisterStub(channel)
    print("----------REGISTRO----------")
    nuevoUsername = input("Introduce usuario: ")
    # comprobar contraseña
    correcto = False
    while(not correcto):
        try:
            password = crearPassword()
            correcto = True
        except PasswordException as e:
            print(e.mensaje)

    nuevoAlias = nuevoUsername[0:2]
    try:
        registro = await stub.doRegister(register_pb2.UserRequest(username=nuevoUsername, password=password, id=nuevoAlias))
        print(registro.message)
    except Exception as e:
        raise e

async def tryLogin(channel):
    stub = register_pb2_grpc.LoginStub(channel)
    print("-------------LOGIN-------------")
    posibleUsername = input("Introduce usuario: ")
    password = getpass("Introduce contraseña: ")
    try:                    
        login = await stub.doLogin(register_pb2.UserPedido(username=posibleUsername, password=password))
        return login
    except Exception as e:
        raise e

async def editarUsuario(channel):
    print("-------------EDITAR USUARIO-------------")
    print("Necesitamos que confirmes tus credenciales para continuar...")
    try:
        login = await tryLogin(channel)
        print(login.message)
        if login.message == "Autentificación exitosa!!":
            opUpdate = input("Quieres modificar tus datos? (y/n) ")
            if opUpdate == 'y':
                stubUpdate = register_pb2_grpc.UpdateStub(channel)
                newUser = input("Introduce usuario nuevo: ")
                newPass = crearPassword()
               
                update = await stubUpdate.doUpdate(register_pb2.UserToChange(oldUsername=login.username,newUsername=newUser,password=newPass))
                print(update.message)
    except Exception as e:
        raise e
    except PasswordException as passExcept:
        print(passExcept.mensaje)
        print('No se pudo editar el usuario')

def loginAPI():
    print('------- LOGIN-------')
    posibleUsername = input("Introduce usuario: ")
    password = getpass("Introduce contraseña: ")
    auth_data = {
        'username' : posibleUsername,
        'password' : password
        }
    try:                    
        login = requests.post(URL_API_REGISTRY + '/login', json=auth_data, verify=False)
        return login.json()
    except requests.exceptions.ConnectionError as e:
        raise Exception('ERROR: Connection refused')
    except Exception as e:
        raise e


def editarUsuarioAPI():
    print("-------------EDITAR USUARIO-------------")
    print("Necesitamos que confirmes tus credenciales para continuar...")
    try:
        login = loginAPI()
        print(login['message'])
        if login['message'] == "Autentificación exitosa!!":
            opUpdate = input("Quieres modificar tus datos? (y/n) ")
            if opUpdate == 'y':
                newUser = input("Introduce usuario nuevo: ")
                newPass = crearPassword()
                update_data = {
                'username' : newUser,
                'password' : newPass
                }
                update =  requests.put(URL_API_REGISTRY + '/usuarios/' + login['username'], 
                                        json=update_data, verify=False)
                print(update.json()['message'])
    except PasswordException as passExcept:
        print(passExcept.mensaje)
        print('No se pudo editar el usuario')
    except requests.exceptions.ConnectionError as e:
        raise Exception('Connection refused')
    except Exception as e:
        raise e

def registroAPI():
    print("----------REGISTRO----------")
    nuevoUsername = input("Introduce usuario: ")
    # comprobar contraseña
    correcto = False
    while(not correcto):
        try:
            password = crearPassword()
            correcto = True
        except PasswordException as e:
            print(e.mensaje)

    nuevoAlias = nuevoUsername[0:2]
    try:
        registry_data = {
            'username': nuevoUsername,
            'password': password 
        }
        registro = requests.post(URL_API_REGISTRY + '/usuarios', 
                                json=registry_data, verify=False)
        print(registro.json()['message'])
    except requests.exceptions.ConnectionError as e:
        raise Exception('Connection refused')
    except Exception as e:
        raise e
## FUNCIÓN PARA ESTABLECER CONEXIÓN GRPC
async def run(host, port):   
    with open('clavesRegistro/server.crt', 'rb') as f:
        trusted_certs = f.read()
    credentials = grpc.ssl_channel_credentials(root_certificates=trusted_certs)
    async with grpc.aio.secure_channel(host + ':' + port, credentials) as channel:    
        seguir = True
        # sigue bucle hasta que se hace login o se quiere salir de la app
        while seguir:
            op = menu()
            try:    
                if int(op) == 1:
                    # REGISTRO
                    await registro(channel)
                elif int(op) == 2:
                    # LOGIN
                    login = await tryLogin(channel)
                    print(login.message)
                    if login.message == "Autentificación exitosa!!":
                        return login
                elif int(op) == 3:
                    # EDITAR USUARIO
                    await editarUsuario(channel)
                elif int(op) == 4:
                    # REGISTRO
                    registroAPI()
                elif int(op) == 5:
                    # LOGIN
                    login = loginAPI()
                    print(login)
                    if login['message'] == "Autentificación exitosa!!":
                        response = type('', (), {})
                        response.username = login['username']
                        response.alias = login['alias']
                        return response
                elif int(op) == 6:
                    # EDITAR USUARIO
                    editarUsuarioAPI()
                elif int(op) == 0:
                    # SALIR
                    exit()
                # caso de un número distinto a los del menú
                else:
                    errorInput()    
            # caso de una cadena
            except ValueError:
                errorInput()
            except Exception as e:
                print(e)
          
def buscarAtraccion(usuario, mapa):
    encontrado = False
    (x1, y1) = (-1, -1)

    while encontrado == False:
        # Coordenada random por donde empieza a buscar
        i = random.randint(0, 19)
        # Busca por el submapa
        for x in range(i,20):
            for y in range(i,20):
                try:
                    # Probar si lo que se encuentra en el mapa es una atracción
                    if int(mapa[x,y]) >= 0 and int(mapa[x,y]) <= 60:
                        # Atracción tiene tiempo de espera menos de 60
                        (x1,y1) = (x,y) 
                        encontrado = True
                        break
                except:
                    # Posición distinta a atracción, no interesa
                    continue
    # Comprobar si es la primera vez que el usuario busca una atraccion
    if usuario.atraccion is None:
        usuario.atraccion = Coordenadas2D(x1,y1)
    else:
        (usuario.atraccion.x, usuario.atraccion.y) = (x1, y1)

# Cuidar el movimiento circular por el mapa
def limitesMapa(x):
    if x >= 20:
        return 0
    elif x <= -1:
        return 19
    else:
        return x

def movimientoLineal(coordUsuario, coordAtraccion):
    movimiento = -1
    # Calcular movimento más cercano, hacia el objetivo o por detrás
    if abs(coordUsuario - coordAtraccion) < 19 - abs(coordUsuario - coordAtraccion):
        movimiento = 1

    if coordUsuario - coordAtraccion > 0:
        movimiento *= -1

    return limitesMapa(coordUsuario + 1 * movimiento)

def movimientoUsuario(usuario):
    # Movimiento lineal
    if usuario.coordenadas.x == usuario.atraccion.x:
        usuario.coordenadas.y = movimientoLineal(usuario.coordenadas.y, usuario.atraccion.y)
    elif usuario.coordenadas.y == usuario.atraccion.y:
        usuario.coordenadas.x = movimientoLineal(usuario.coordenadas.x, usuario.atraccion.x)
    ## MOVIMIENTO DIAGONAL
    else:
        (a1, a2) = (usuario.atraccion.x - usuario.coordenadas.x, usuario.atraccion.y - usuario.coordenadas.y)
        (movimientoX, movimientoY) = (-1,-1)
        if a1 > 0:
            movimientoX = 1
        if a2 > 0:
            movimientoY = 1

        finalX = limitesMapa(usuario.coordenadas.x + movimientoX)
        finalY = limitesMapa(usuario.coordenadas.y + movimientoY)
        (usuario.coordenadas.x, usuario.coordenadas.y) = (finalX, finalY)

def enviarDatos(usuario, topic):
    datos = {
        'alias' : usuario.alias,
        'username' : usuario.username,
        'x' : usuario.coordenadas.x,
        'y' : usuario.coordenadas.y
    }
    producer.send(topic, value=datos)

def enviarDatosSalida(usuario, topic):
    # Añadir key salida para que engine identifique la intención
    datos = {
        'alias' : usuario.alias,
        'username' : usuario.username,
        'x' : usuario.coordenadas.x,
        'y' : usuario.coordenadas.y,
        'salida' : True
    }
    producer.send(topic, value=datos)

def leerEntrada(usuario):
    for message in consumerEntrada:
        usuarioDentro = message.value
        # busca si el mensaje se trata de su posición en el mapa o de otro usuario
        if usuarioDentro['username'] == usuario.username:
            if 'cola' in usuarioDentro.keys():
                print(usuarioDentro['cola'])
            else:
                usuario.coordenadas.x = usuarioDentro['x']
                usuario.coordenadas.y = usuarioDentro['y']
                break
    consumerEntrada.close()

def leerMapa(usuario, mapa):
    for message in consumerMapa:
        mapa = message.value
        ## Dibujar mapa 
        print(end="    ")
        for i in range(0,20):
            if i < 10:
                print(i, end="  ")
            else:
                print(i, end=" ")
        print()
        for x in range(0,20):
            if x < 10:
                print(" " + str(x), end="  ")
            else:
                print(x, end="  ")
            for y in range(0,20):
                print(mapa[x, y], end="  ")
            print()
        print()

        # Ver si usuario tiene objetivo para moverse por el mapa, y si no, buscarlo
        if usuario.atraccion is None or (usuario.atraccion.x, usuario.atraccion.y) == (usuario.coordenadas.x, usuario.coordenadas.y) or int(mapa[usuario.atraccion.x, usuario.atraccion.y]) > 60:
            buscarAtraccion(usuario, mapa)

# Movimiento automatizado cada x segundos hacia la atracción escogida
def enadenarMovimientos(usuario):
    while True:
        sleep(5)
        if not usuario.atraccion is None:
            movimientoUsuario(usuario)
        enviarDatos(usuario, Kafka.TOPIC_MOVIMIENTO)

def signal_handler(signal, frame):
    # Controlar control + C
    if not usuario is None:
        enviarDatosSalida(usuario, Kafka.TOPIC_INTENTO_ENTRADA)
    sleep(2)
    print("CHAO CHAO CHAO")
    exit()

def arrancarConexionRegistry(host, port):
    return asyncio.run(run(host, port))

if __name__ == '__main__':
    usuario = None
    # Controlar que los argumentos tienen la estructura requerida
    try:
        # Controlar número de argumentos
        if len(sys.argv) != 3:
            raise Exception

        # Host y puerto Registry
        registry = sys.argv[1].split(":")
        host_registry = registry[0]
        port_registry = registry[1]

        # Host y puerto servidor kafka
        broker_kafka = sys.argv[2].split(":")
        host_broker = broker_kafka[0]
        port_broker = broker_kafka[1]
    except Exception:
        print(LLAMADA_VISITOR)
        exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    ## Comprobación de que el usuario está en la BD
    datosLogin = arrancarConexionRegistry(host_registry, port_registry)
    
    # datos recibidos del login
    username = datosLogin.username
    alias = datosLogin.alias

    ## INICIO DE SESIÓN CORRECTO
    usuario = Usuario(username, alias, Coordenadas2D(-1, -1))
    # DEFINIR CONSUMIDOR Y PRODUCTOR KAFKA ENTRADA 
    producer = Kafka.definirProductorJSON(host_broker, port_broker)
    consumerEntrada = Kafka.definirConsumidorJSON(host_broker, port_broker, Kafka.TOPIC_PASEN, 'latest', 'cola_visitor')
    
    # hilo que escucha la entrada que le proporciona ENGINE
    hiloEntrada = threading.Thread(
        target=leerEntrada,
        args=(usuario, )
    )
    hiloEntrada.daemon = True
    hiloEntrada.start()
    
    # informar del intento de entrada cada 5 seg
    enviarDatos(usuario, Kafka.TOPIC_INTENTO_ENTRADA)

    # esperar a que termine el hilo para continuar ejecución
    hiloEntrada.join()
    mapa = None
    # DEFINIR CONSUMIDOR KAFKA QUE RECIBE EL MAPA
    consumerMapa = Kafka.definirConsumidorBytes(host_broker, port_broker, Kafka.TOPIC_MAPA)
    ## Recibir si el usuario puede entrar al parque (Engine)
    hiloMapa = threading.Thread(
            target=leerMapa,
            args=(usuario, mapa)
    )
    hiloMapa.daemon = True
    hiloMapa.start()
    sleep(1)
    
    # hilo que se encarga del automatizado movimiento del usuario por el mapa
    hiloMovimiento = threading.Thread(
        target=enadenarMovimientos,
        args=(usuario, )
    )
    hiloMovimiento.daemon = True
    hiloMovimiento.start()

    # opción para el usuario de salir escribiendo palabra 'exit'
    while True:
        salida = input()
        if salida == "exit":
            enviarDatosSalida(usuario, Kafka.TOPIC_INTENTO_ENTRADA)
            sleep(2)
            print("CHAO CHAO CHAO")
            exit(0)