from flask import Flask, jsonify, request
from flask_cors import CORS, cross_origin
import mysql.connector
import sys

sys.path.append('..')
from FWQ_Registry import actualizar


app = Flask('server')

CORS(app)

# ruta de ejemplo
@app.route('/')

def hello():
    return  jsonify({ 'message' : "Hello world!"})




if __name__ == '__main__':
    app.run(debug=True, port=5005, ssl_context=('./ssl/cert.pem', './ssl/key.pem'))