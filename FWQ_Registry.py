import sys
import mysql.connector

sys.path.insert(0, './protosRegistry')

import asyncio
import logging
from time import sleep
import signal

import grpc
from protosRegistry import register_pb2, register_pb2_grpc

from concurrent import futures

host_BD = 'localhost'
user_BD = 'admin'
passwd_BD = 'burguerking'
database_BD = 'parque'

# Ejecución Registry
# python3 FWQ_Registry.py puerto

class Register(register_pb2_grpc.RegisterServicer):
    async def doRegister(self, request: register_pb2.UserRequest, context: grpc.aio.ServicerContext) -> register_pb2.UserReply:
        logging.info('Se quiere registrar el usuario ' + request.username + ' con la contraseña ' + request.password)
      

        mydb = mysql.connector.connect(
        host=host_BD,
        user=user_BD,
        passwd=passwd_BD,
        database=database_BD)

        mycursor = mydb.cursor()

        message = ""
        existe = False
        query = "SELECT username FROM `usuarios` WHERE username=" + "\"" + request.username + "\""
        mycursor.execute(query)
        data = mycursor.fetchall()
        if data:
            message = "El usuario ya existe"
            existe = True

        if not existe:
            sql = "INSERT INTO usuarios(username, password, alias) VALUES (%s, %s, %s)"
            val = (request.username, request.password, request.id)
            mycursor.execute(sql, val)

            mydb.commit()
            message = "REGISTRO EXITOSO!!"
            logging.info("Se ha registrado el usuario " + request.username)

        return register_pb2.UserReply(message=message)

class Login(register_pb2_grpc.LoginServicer):
    async def doLogin(self, request: register_pb2.UserPedido, context: grpc.aio.ServicerContext) -> register_pb2.UserRespuesta:
        logging.info("Se quiere loguear el usuario " + request.username)

        mydb = mysql.connector.connect(
        host=host_BD,
        user=user_BD,
        passwd=passwd_BD,
        database=database_BD)

        mycursor = mydb.cursor()
        
        message = ""
        existe = True
        query = "SELECT username, alias FROM usuarios WHERE username=" + "\"" + request.username + "\""
        mycursor.execute(query)
        data = mycursor.fetchall()
        if not data:
            existe = False
            message = "El usuario " + request.username + " no existe"
            usernameLog = request.username
            alias = request.username[0:2]
        else:
            logging.info("Usuario correcto")
            usernameLog = data[0][0]
            alias = data[0][1]

        if existe:
            query = "SELECT password FROM usuarios WHERE username=" + "\"" + request.username + "\""
            mycursor.execute(query)
            data = mycursor.fetchall()
            data = data[0][0]
            
            if data==request.password:
                message ="Autentificación exitosa!!"
                logging.info("Se ha iniciado sesión con el usuario " + request.username)
            else:
                message = "Contraseña incorrecta"

        return register_pb2.UserRespuesta(message=message, username=usernameLog, alias=alias)

class Update(register_pb2_grpc.UpdateServicer):
    async def doUpdate(self, request: register_pb2.UserToChange, context: grpc.aio.ServicerContext) -> register_pb2.UserUpdate:
        logging.info("Se quiere modificar el usuario " + request.oldUsername)

        mydb = mysql.connector.connect(
        host=host_BD,
        user=user_BD,
        passwd=passwd_BD,
        database=database_BD)

        mycursor = mydb.cursor()
        
        message = ""
        queryUser = "UPDATE `usuarios` SET `username`= " + "\'" + request.newUsername + "\'" + ", `password`= " + "\'" + request.password + "\'" + " WHERE `usuarios`.`username` = " + "\'" + request.oldUsername + "\'"
        try:
            mycursor.execute(queryUser)
            # essage = "Usuario actualizado correctamente"
        except mysql.connector.Error as err:
            logging.info("Error: No se puede actualizar el usuario")
            message = "Error: No se puede actualizar el usuario"

        return register_pb2.UserUpdate(message=message)

async def serve(port) -> None:
    server = grpc.aio.server()
    register_pb2_grpc.add_RegisterServicer_to_server(Register(), server)
    register_pb2_grpc.add_LoginServicer_to_server(Login(), server)
    register_pb2_grpc.add_UpdateServicer_to_server(Update(), server)
    listen_addr = '[::]:' + port
    server.add_insecure_port(listen_addr)
    logging.info("Starting server on %s", listen_addr)
    await server.start()
    await server.wait_for_termination() 
    
def signal_handler(signal, frame):
    # Controlar control + C 
    print("Apagando Registry...")
    #server.stop()
    sleep(1)
    exit()


if __name__ == '__main__':
    port = sys.argv[1]
    logging.basicConfig(level=logging.INFO)
    signal.signal(signal.SIGINT, signal_handler)
    asyncio.run(serve(port))
