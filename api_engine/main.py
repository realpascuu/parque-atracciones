from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import mysql.connector
import sys
sys.path.append("..")

from FWQ_Engine import actualizarZona, consultaAtracciones, consultaUsuarios
import requests
from requests.exceptions import RequestException

# LLAMADA python3 main.py


# variables para conectar con BD
host_BD = 'localhost'
user_BD = 'admin'
passwd_BD = 'burguerking'
database_BD = 'parque'

# declaramos el API
app = Flask('server')
# Añadimos cabecera CORS
CORS(app)

# ruta de ejemplo
@app.route('/')

def hello():
    return  jsonify({ 'message' : "Hello world!"})

# ruta para obtener las posiciones de las atracciones
@app.route('/atracciones')

def obtenerAtracciones():

# intentamos conectar con la BD
    try:
        data = consultaAtracciones()
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
        print(e)
        print("No se ha podido establecer conexión con BD en " + host_BD + ":3306")
        return jsonify([])
# ruta para obtener la posicion de los usuarios
@app.route('/usuarios')

def obtenerUsuarios():

# intentamos conectar con la BD
    try:
        data = consultaUsuarios()
        resultado = []
        for usuario in data:
            resultado.append({
                'alias': usuario[1],
                'x': usuario[2],
                'y': usuario[3]
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
    
    (resultado, block) = actualizarZona(zona, ciudad)

    if resultado:
        if block:
            return jsonify({'message': '¡Zona ' + zona + ' bloqueada!'})
        else:
            return jsonify({'message': '¡Zona ' + zona + ' no bloqueada!'})
    else:
        return {'message': "No se ha podido establecer conexión con BD en " + host_BD + ":3306"}


if __name__ == '__main__':
    app.run(debug=True, port=3000, ssl_context=('./ssl/cert.pem', './ssl/key.pem'))