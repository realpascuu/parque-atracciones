import logging
from time import sleep
from common.Coordenadas2D import Coordenadas2D
import common.Kafka as Kafka
import threading
from numpy import *
import random
import signal

import sys

sys.path.insert(0, './protosRegistry')

import asyncio
import logging
from getpass import getpass
import grpc
from protosRegistry import register_pb2, register_pb2_grpc

from common.Usuario import Usuario

## LLAMADA A Visitor
## python3 FWQ_Visitor.py host:port_registry host:port_kafka

## FUNCIÓN PARA ESTABLECER CONEXIÓN GRPC
async def run(host, port):   
    async with grpc.aio.insecure_channel(host + ':' + port) as channel:
        
        print("BIENVENIDO AL PARQUE DE ATRACCIONES")    
        seguir = True
        while seguir:
            print("""MENÚ ------------------------
            1. Registro
            2. Inicio Sesión
            3. Editar usuario
            4. Salir
                """)
            op = input("¿Que quieres hacer? ")
            if op != "1" and op != "2" and op != "3":
                print('''Introduce 1 para registrarte\nIntroduce 2 para iniciar sesión''')

            if op == "1":
                stub = register_pb2_grpc.RegisterStub(channel)
                print("----------REGISTRO----------")
                password = ""
                password2 = "a"
                nuevoUsername = input("Introduce usuario: ")
                while(password != password2):                    
                    password = getpass("Introduce contraseña: ")
                    password2 = getpass("Vuelve a introducir la contraseña: ")
                    if (password != password2):
                        print("Error! Las contraseñas no coinciden")
                nuevoAlias = nuevoUsername[0:2]

                registro = await stub.doRegister(register_pb2.UserRequest(username=nuevoUsername, password=password, id=nuevoAlias))
                print(registro.message)
            elif op == "2":
                
                print("-------------LOGIN-------------")
                posibleUsername = input("Introduce usuario: ")
                password = getpass("Introduce contraseña: ")

                stub = register_pb2_grpc.LoginStub(channel)
                login = await stub.doLogin(register_pb2.UserPedido(username=posibleUsername, password=password))
                
                if not login.message == "Contraseña incorrecta":
                    return login
            elif op == "3":
                print("-------------EDITAR USUARIO-------------")
                loginUsername = input("Introduce usuario: ")
                password = getpass("Introduce contraseña: ")
            
                login = await stub.doLogin(register_pb2.UserPedido(username=loginUsername, password=password))
                print(login.message)
                if login.message !="El usuario " + loginUsername + " no existe":
                    opUpdate = input("Quieres modificar tus datos? (y/n) ")
                    if opUpdate == 'y':
                        stubUpdate = register_pb2_grpc.UpdateStub(channel)
                        newUser = input("Introduce usuario nuevo: ")
                        newPass = input("Introduce nueva contraseña: ")
                        update = await stubUpdate.doUpdate(register_pb2.UserToChange(oldUsername=loginUsername,newUsername=newUser,password=newPass))
                        print(update.message)
            else:
                exit()

def buscarAtraccion(usuario, mapa):
    encontrado = False
    (x1, y1) = (-1, -1)

    while encontrado == False:
        # Coordenada random por donde empieza a buscar
        i = random.randint(0, 19)
        # Busca por el submapa
        for x in range(i,19):
            for y in range(i,19):
                try:
                    # Probar si lo que se encuentra en el mapa es una atracción
                    if int(mapa[x,y]) <= 60:
                        # Atracción tiene tiempo de espera menos de 60
                        (x1,y1) = (x,y) 
                        encontrado = True
                        break
                except:
                    continue
    # Comprobar si es la primera vez que el usuario busca una atraccion
    if usuario.atraccion is None:
        usuario.atraccion = Coordenadas2D(x1,y1)
    else:
        (usuario.atraccion.x, usuario.atraccion.y) = (x1, y1)

def movimientoLineal(coordUsuario, coordAtraccion):
    movimiento = -1
    if abs(coordUsuario - coordAtraccion) < 19 - abs(coordUsuario - coordAtraccion):
        movimiento = 1

    if coordUsuario - coordAtraccion > 0:
        movimiento *= -1

    return coordUsuario + 1 * movimiento

def movimientoUsuario(usuario):
    # Movimiento lineal
    if usuario.coordenadas.x == usuario.atraccion.x:
        usuario.coordenadas.y = movimientoLineal(usuario.coordenadas.y, usuario.atraccion.y)
    elif usuario.coordenadas.y == usuario.coordenadas.y:
        usuario.coordenadas.x = movimientoLineal(usuario.coordenadas.x, usuario.atraccion.x)
    ## MOVIMIENTO DIAGONAL
    else:
        (a1, a2) = (usuario.atraccion.x - usuario.coordenadas.x, usuario.atraccion.y - usuario.coordenadas.y)
        (movimientoX, movimientoY) = (-1,-1)
        if a1 > 0:
            movimientoX = 1
        if a2 > 0:
            movimientoY = 1

        (usuario.coordenadas.x, usuario.coordenadas.y) = (usuario.coordenadas.x + movimientoX, usuario.coordenadas.y + movimientoY)

def enviarDatos(usuario, topic):
    datos = {
        'alias' : usuario.alias,
        'username' : usuario.username,
        'x' : usuario.coordenadas.x,
        'y' : usuario.coordenadas.y
    }
    producer.send(topic, value=datos)

def enviarDatosSalida(usuario, topic):
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
        logging.info("Voy a entrar!")
        if usuarioDentro['username'] == usuario.username:
            usuario.coordenadas.x = usuarioDentro['x']
            usuario.coordenadas.y = usuarioDentro['y']
            break

def leerMapa(usuario, mapa):
    for message in consumerMapa:
        mapa = message.value
        if usuario.atraccion is None or (usuario.atraccion.x, usuario.atraccion.y) == (usuario.coordenadas.x, usuario.coordenadas.y) or int(mapa[usuario.atraccion.x, usuario.atraccion.y]) > 60:
            buscarAtraccion(usuario, mapa)
        for x in mapa:
            for y in x:
                # Obtener donde ubica el engine al visitante
                if usuario.coordenadas is None and y == usuario.alias:
                    usuario.coordenadas = Coordenadas2D(x,y)
                print(y, end=" ")
            print()
        print()

def enadenarMovimientos(usuario):
    while True:
        sleep(5)
        if not usuario.atraccion is None:
            movimientoUsuario(usuario)
        enviarDatos(usuario, Kafka.TOPIC_MOVIMIENTO)

def signal_handlerRegistry(signal, frame):
    # Controlar control + C
    print("CHAO CHAO CHAO")
    exit()

def signal_handler(signal, frame):
    # Controlar control + C 
    enviarDatosSalida(usuario, Kafka.TOPIC_INTENTO_ENTRADA)
    print("CHAO CHAO CHAO")
    exit()

def arrancarConexionRegistry(host, port):
    return asyncio.run(run(host, port))

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handlerRegistry)
    # Host y puerto Registry
    registry = sys.argv[1].split(":")
    host_registry = registry[0]
    port_registry = registry[1]

    # Host y puerto servidor kafka
    broker_kafka = sys.argv[2].split(":")
    host_broker = broker_kafka[0]
    port_broker = broker_kafka[1]
    ## Comprobación de que el usuario está en la BD
    logging.basicConfig()
    datosLogin = arrancarConexionRegistry(host_registry, port_registry)
    
    username = datosLogin.username
    alias = datosLogin.alias
    #hiloLogin.join()

    signal.signal(signal.SIGINT, signal_handler)
    ## INICIO DE SESIÓN CORRECTO
    usuario = Usuario(username, alias)
    # DEFINIR CONSUMIDOR Y PRODUCTOR KAFKA ENTRADA 
    producer = Kafka.definirProductorJSON(host_broker, port_broker)
    consumerEntrada = Kafka.definirConsumidorJSON(host_broker, port_broker, Kafka.TOPIC_PASEN)
    hiloEntrada = threading.Thread(
        target=leerEntrada,
        args=(usuario, )
    )
    hiloEntrada.daemon = True
    hiloEntrada.start()
    while hiloEntrada.is_alive():
        sleep(4)
        enviarDatos(usuario, Kafka.TOPIC_INTENTO_ENTRADA)

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
    sleep(3)
    
    hiloMovimiento = threading.Thread(
        target=enadenarMovimientos,
        args=(usuario, )
    )
    hiloMovimiento.daemon = True
    hiloMovimiento.start()

    while True:
        salida = input()
        if salida == "exit":
            enviarDatosSalida(usuario, Kafka.TOPIC_INTENTO_ENTRADA)
            print("CHAO CHAO CHAO")
            exit()