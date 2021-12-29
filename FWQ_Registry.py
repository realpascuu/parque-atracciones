from random import random
import sys
import mysql.connector
import random
import string


import asyncio
import logging
from time import sleep
import signal
import hashlib
from datetime import datetime
from concurrent import futures
import grpc
#import datatime
sys.path.append(sys.path[0].split('api_registry')[0] + '/protosRegistry')

from protosRegistry import register_pb2, register_pb2_grpc

host_BD = 'localhost'
user_BD = 'admin'
passwd_BD = 'burguerking'
database_BD = 'parque'

# Ejecución Registry
LLAMADA_REGISTRY = "python3 FWQ_Registry.py <puerto_escucha>"

_cleanup_coroutines = []


def registrarse(username, password, id, ip_cliente):
    try:
        mydb = mysql.connector.connect(
        host=host_BD,
        user=user_BD,
        passwd=passwd_BD,
        database=database_BD)

        mycursor = mydb.cursor()

        message = ""
        existe = False
        query = "SELECT username FROM `usuarios` WHERE username=" + "\"" + username + "\""
        mycursor.execute(query)
        data = mycursor.fetchall()
        if data:
            message = "El usuario ya existe"
            existe = True
            subirEvento(ip_cliente,"REGISTRO","ERROR: El usuario " + username + " ya existe") 
        if not existe:
            passHash,salt = obtenerHash(password)
            sql = "INSERT INTO usuarios(username, password, salt, alias) VALUES (%s, %s, %s, %s)"
            val = (username, passHash, salt, id)
            mycursor.execute(sql, val)

            mydb.commit()
            message = "REGISTRO EXITOSO!!"
            subirEvento(ip_cliente,"REGISTRO","INFO: Se ha registrado el usuario " + username) 

        return message
    except Exception as e:
        print(e)
        message = "No se ha podido establecer conexión con BD en " + host_BD + ":3306";
        return e

def login(username, password, ip_cliente):
    try:
        mydb = mysql.connector.connect(
        host=host_BD,
        user=user_BD,
        passwd=passwd_BD,
        database=database_BD)

        mycursor = mydb.cursor()
        
        message = ""
        existe = True
        query = "SELECT username, alias FROM usuarios WHERE username=" + "\"" + username + "\""
        mycursor.execute(query)
        data = mycursor.fetchall()
        if not data:
            existe = False
            subirEvento(ip_cliente,"LOGIN","INFO: Se ha logueado el usuario " + username) 
            message = "El usuario " + username + " no existe"
            usernameLog = username
            alias = username[0:2]
        else:
            usernameLog = data[0][0]
            alias = data[0][1]

        if existe:
            query = "SELECT password, salt FROM usuarios WHERE username=" + "\"" + username + "\""
            mycursor.execute(query)
            data = mycursor.fetchall()
            passwordBD = data[0][0]
            saltBD = data[0][1]
            if hashIgual(passwordBD, saltBD, password):
                message ="Autentificación exitosa!!"
                subirEvento(ip_cliente,"LOGIN","INFO: Se ha logueado el usuario " + username) 
            else:
                subirEvento(ip_cliente,"LOGIN","INFO: Se ha intentado loguear el usuario " + username + " con la contraseña incorrecta") 
                message = "Contraseña incorrecta"

        return (message, usernameLog, alias)
    except Exception as e:
        print(e)
        message = "No se ha podido establecer conexión con BD en " + host_BD + ":3306";
        return (message, "", "")


def actualizar(oldUsername, newUsername, password, ip_cliente):
    try:
        mydb = mysql.connector.connect(
        host=host_BD,
        user=user_BD,
        passwd=passwd_BD,
        database=database_BD)

        mycursor = mydb.cursor()
        
        message = ""
        newPassword, salt = obtenerHash(password)
        queryUser = "UPDATE `usuarios` SET `username`= " + "\'" + newUsername + "\'" + ", `password`= " + "\'" + newPassword + "\'" + ", `salt`= " + "\'" + salt + "\'" + " WHERE `usuarios`.`username` = " + "\'" + oldUsername + "\'"
        try:
            mycursor.execute(queryUser)
            mydb.commit()
            message = "USUARIO ACTUALIZADO!"
            subirEvento(ip_cliente,"ACTUALIZAR","INFO: Se ha actualizado el usuario " + oldUsername + " a " + newUsername) 
        except mysql.connector.Error as err:
            subirEvento(ip_cliente,"ACTUALIZAR","ERROR: No se puede actualizar el usuario: " + err)

        return message
    except Exception as e:
        logging.info(e)
        message = "No se ha podido establecer conexión con BD en " + host_BD + ":3306";
        return message
class Register(register_pb2_grpc.RegisterServicer):
    async def doRegister(self, request: register_pb2.UserRequest, context: grpc.aio.ServicerContext) -> register_pb2.UserReply:
        subirEvento(ip_cliente(context),"REGISTRO","INFO: Se quiere registrar el usuario " + request.username + " con la contraseña " + request.password)      
        message = registrarse(request.username, request.password, request.id, ip_cliente(context))
        return register_pb2.UserReply(message=message)

class Login(register_pb2_grpc.LoginServicer):
    async def doLogin(self, request: register_pb2.UserPedido, context: grpc.aio.ServicerContext) -> register_pb2.UserRespuesta:
        subirEvento(ip_cliente(context),"LOGIN","INFO: Se quiere loguear el usuario" + request.username)        
        (message, usernameLog, alias) = login(request.username, request.password,ip_cliente(context))
        return register_pb2.UserRespuesta(message=message, username=usernameLog, alias=alias)

class Update(register_pb2_grpc.UpdateServicer):
    async def doUpdate(self, request: register_pb2.UserToChange, context: grpc.aio.ServicerContext) -> register_pb2.UserUpdate:
        subirEvento(ip_cliente(context),"ACTUALIZAR", "INFO: Se quiere modificar el usuario " + request.oldUsername)
        message = actualizar(request.oldUsername, request.newUsername, request.password, ip_cliente(context))
        return register_pb2.UserUpdate(message=message)


#Clase para interceptar la autentificación
class AuthInterceptor(grpc.ServerInterceptor):
    def __init__(self, key):
        self._valid_metadata = ('rpc-auth-header', key)

        def deny(_, context):
            context.abort(grpc.StatusCode.UNAUTHENTICATED, 'Invalid key')

        self._deny = grpc.unary_unary_rpc_method_handler(deny)

    def intercept_service(self, continuation, handler_call_details):
        meta = handler_call_details.invocation_metadata

        if meta and meta[0] == self._valid_metadata:
            return continuation(handler_call_details)
        else:
            return self._deny

def subirEvento(IP, accion, descripcion):
    mydb = mysql.connector.connect(
    host=host_BD,
    user=user_BD,
    passwd=passwd_BD,
    database=database_BD)

    mycursor = mydb.cursor()

    fecha = datetime.now()
    query = "INSERT INTO Eventos(fecha,IP,acción,descripción) VALUES (%s,%s,%s,%s)"
    val = (fecha,IP, accion, descripcion)

    mycursor.execute(query,val)
    mydb.commit()

def ip_cliente(context):
    ip_cliente = context.peer()
    if 'ipv6' in ip_cliente:
        indice1 = ip_cliente.index('[')
        indice2 = ip_cliente.index(']')
        ip_cliente = ip_cliente[indice1+1:indice2]
    if 'ipv4' in ip_cliente:
        ip_cliente = ip_cliente.split(':')[1]
    
    return ip_cliente

def obtenerHash(password):
    characters = string.ascii_letters + string.digits + string.punctuation
    salt = ''.join(random.choice(characters) for i in range(6))
    pepper = random.choice(string.ascii_letters)
    encodedPassword = (password+salt+pepper).encode()
    passHash = hashlib.sha256(encodedPassword).hexdigest()
    return (passHash, salt)

def hashIgual(passwordBD, saltBD, password):
    for i in range(256):
        pepper = chr(i)
        encodedPass = (password+saltBD+pepper).encode()
        passw = hashlib.sha256(encodedPass).hexdigest()
        if passw == passwordBD:            
            return True
    return False

async def serve(port) -> None:
    listen_addr = '[::]:' + port
    # abrimos la clave privada
    with open('clavesRegistro/server.key', 'rb') as f:
        private_key = f.read()
    # abrimos el certificado
    with open('clavesRegistro/server.crt', 'rb') as f:
        certificate_chain = f.read()
    server_credentials = grpc.ssl_server_credentials( ((private_key, certificate_chain,),))
    server = grpc.aio.server(futures.ThreadPoolExecutor(max_workers=10))
    register_pb2_grpc.add_RegisterServicer_to_server(Register(), server)
    register_pb2_grpc.add_LoginServicer_to_server(Login(), server)
    register_pb2_grpc.add_UpdateServicer_to_server(Update(), server)
    # obtenemos las credenciales
    
    server.add_secure_port(listen_addr, server_credentials)
       
    subirEvento(listen_addr, "SERVER", "Encendiendo servidor...")   
    logging.info("Starting server on %s", listen_addr)
    await server.start() 

# Módulo para apagar correctamente el registry
    async def server_apagado():
        subirEvento(listen_addr,"SERVER", "Apagando servidor...")

    _cleanup_coroutines.append(server_apagado())
    await server.wait_for_termination()
    
def signal_handler(signal, frame):
    # Controlar control + C 
    sleep(1)
    exit()

if __name__ == '__main__':
    try:
        if len(sys.argv) != 2:
            raise Exception
        port = sys.argv[1]
    except Exception:
        print(LLAMADA_REGISTRY)
        exit()
    
    signal.signal(signal.SIGINT, signal_handler)

    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(serve(port))
    finally:
        loop.run_until_complete(*_cleanup_coroutines)
        loop.close()
