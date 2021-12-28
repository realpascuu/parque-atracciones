import logging
from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import mysql.connector
import sys

sys.path.append('..')
from FWQ_Registry import actualizar, registrarse, login


app = Flask('server')

CORS(app)

# ruta de ejemplo
@app.route('/')

def hello():
    return  jsonify({ 'message' : "Hello world!" })

# ruta que hace el registro del usuario
@app.route('/usuarios', methods= ["POST"])
def crearUsuario():
    request_data = request.get_json()
    username = request_data['username']
    password = request_data['password']

    alias = username[0:2]

    message = registrarse(username, password, alias)
    return jsonify({ 'message': message})

# ruta que realiza la actualización del usuario
@app.route('/usuarios/<string:oldUsername>', methods=['PUT'])
def actualizarUsuario(oldUsername):
    request_data = request.get_json()
    newUsername = request_data['username']
    password = request_data['password']

    message = actualizar(oldUsername, newUsername, password)

    return jsonify({'message': message})

# ruta qye realiza el login de un usuario
@app.route('/login', methods=['POST'])
def loginUsuario():
    request_data = request.get_json()
    username = request_data['username']
    password = request_data['password']

    message, username, alias = login(username, password)

    return jsonify({
        'message': message,
        'username': username,
        'alias': alias
    })

if __name__ == '__main__':
    app.run(debug=True, port=5005, ssl_context=('./ssl/cert.pem', './ssl/key.pem'))