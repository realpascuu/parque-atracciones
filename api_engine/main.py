from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import mysql.connector

import requests
from requests.exceptions import RequestException

# LLAMADA python3 main.py

API_KEY = "47fe4dc689d72a4666d016f08f81dbf3"
GRADOS_KELVIN = 273.15


# variables para conectar con BD
host_BD = 'localhost'
user_BD = 'admin'
passwd_BD = 'burguerking'
database_BD = 'parque'

# declaramos el API
app = Flask('server')
# Añadimos cabecera CORS
CORS(app)

def cadenaAPI(city):
    return "https://api.openweathermap.org/data/2.5/weather?q=" + city + "&appid=" + API_KEY

# CONVERSIÓN DE KELVIN A GRADOS CENTÍGRADOS
def convertirKelvinAGrados(kelvin):
    return kelvin - GRADOS_KELVIN

# LLAMADA A LA API, DEVUELVE LA TEMPERATURA DE LA CIUDAD
def conectarAPIWeather(city):
    cadenaBusqueda = cadenaAPI(city)
    try:
        respuesta = requests.get(cadenaBusqueda).json()
    except RequestException as e:
        print(e)
    
    return round(convertirKelvinAGrados(respuesta['main']['temp']), 1)


# ruta de ejemplo
@app.route('/')

def hello():
    return  jsonify({ 'message' : "Hello world!"})

# ruta para obtener las posiciones de las atracciones
@app.route('/atracciones')

def obtenerAtracciones():

# intentamos conectar con la BD
    try:
        mydb = mysql.connector.connect(
            host=host_BD,
            user=user_BD,
            passwd=passwd_BD,
            database=database_BD
        );
        mycursor = mydb.cursor()
        query = 'SELECT id, x, y, tiempo_espera FROM atraccion'
        mycursor.execute(query)
        data = mycursor.fetchall()
        resultado = []
        for atraccion in data:
            resultado.append({
                'id': atraccion[0],
                'x': atraccion[1],
                'y': atraccion[2],
                'tiempo_espera': atraccion[3]
                })
        return jsonify(resultado)
    except Exception as e:
        print("No se ha podido establecer conexión con BD en " + host_BD + ":3306")
        return jsonify([])
# ruta para obtener la posicion de los usuarios
@app.route('/usuarios')

def obtenerUsuarios():

# intentamos conectar con la BD
    try:
        mydb = mysql.connector.connect(
        host=host_BD,
        user=user_BD,
        passwd=passwd_BD,
        database=database_BD
        )
        mycursor = mydb.cursor()
        query = 'SELECT alias, x, y FROM usuarios WHERE x != -1'
        mycursor.execute(query)
        data = mycursor.fetchall()
        resultado = []
        for usuario in data:
            resultado.append({
                'alias': usuario[0],
                'x': usuario[1],
                'y': usuario[2]
                })
        return jsonify(resultado)
    except Exception as e:
        print("No se ha podido establecer conexión con BD en " + host_BD + ":3306")
        return jsonify([])
    

@app.route('/zona', methods=['PUT'])

def cambiarZona():
    request_data = request.get_json()

    zona = request_data['zona']
    ciudad = request_data['ciudad']
    
    block = False
    temp = conectarAPIWeather(ciudad)
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

        if block:
            return jsonify({'message': '¡Zona ' + zona + ' bloqueada!'})
        else:
            return jsonify({'message': '¡Zona ' + zona + ' no bloqueada!'})
    except Exception as e:
        print(e)
        return jsonify({'message': "No se ha podido establecer conexión con BD en " + host_BD + ":3306"})



if __name__ == '__main__':
    app.run(debug=True, port=3000, ssl_context=('./ssl/cert.pem', './ssl/key.pem'))