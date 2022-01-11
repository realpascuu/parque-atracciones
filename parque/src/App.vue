<template>
<div>
    <div class="titulo">
        <p>Parque de atracciones</p>
    </div>
    <div class="subtitulo">
        <p>Bloqueo de zonas parque</p>
    </div>
    <div class="padre">
        <div class="glosario-zonas">
            <p><span class="square zona-1"></span> Zona 1</p>
            <p><span class="square zona-2"></span> Zona 2</p>
            <p><span class="square zona-3"></span> Zona 3</p>
            <p><span class="square zona-4"></span> Zona 4</p>
        </div>
    </div>
    <div class="padre">
        <div class="formulario">
            <input id="ciudad" v-model="ciudad" class="city espacio-formulario" placeholder="Ciudad">
            <select id="zona" v-model="this.zona" name="zona" class="espacio-formulario boton">
                <option>1</option>
                <option>2</option>
                <option>3</option>
                <option>4</option>
            </select>
            <button @click="eventBloquearZona()" id="envioZona" type="button" class="espacio-formulario boton">Enviar</button>
        </div>
    </div>
    <div class="padre">
        <div class="formulario" id="info-zona">
            <div @click="cerrarInfo()" class="close">x</div>
            <div class="" id="info-zona-content">

            </div>
        </div>
    </div>
    <div @click="cerrarPopup($event)" class="popup-wrapper" id="popup-wrapper">
        <div class="popup">
            <div @click="cerrarPopup($event)" class="popup-close">x</div>
            <div class="popup-content" id="popup-content">
            </div>
        </div>
    </div>
    <div class="subtitulo">
        <p>Estado del mapa</p>
    </div>
    <div class="padre">
        <ul class="mapa" id="mapa">
        </ul>
    </div>
</div>
</template>

<script>

export default {
  name: 'App',
  data() {
    return {
      zona: 1,
      ciudad: '',
      cadenaAPI: 'https://192.168.56.1:3000',
      intervalId: ''
    }
  },
  methods: {
    changePopup(cadena, mensaje) {
        const popup = document.getElementById('popup-wrapper')
        const popup_content = document.getElementById('popup-content')
        popup.style.display = cadena;
        popup_content.innerHTML = mensaje;
    },

    continuarIntervalo() {
        return setInterval(async() => {
                var content = await Promise.all(
                    [this.getAtracciones(), this.getUsuarios()]
                );

                for (var i = 0; i < 20; i++) {
                    for (var j = 0; j < 20; j++) {
                        var casilla = document.getElementById(i + '-' + j);
                        var atraccion = this.encontrarPosicion(content[0], i, j);
                        var usuario = this.encontrarPosicion(content[1], i, j);
                        if (casilla.classList.contains('atraccion'))
                            casilla.classList.remove('atraccion')
                        if (casilla.classList.contains('usuario'))
                            casilla.classList.remove('usuario')
                        if (atraccion) {
                            casilla.innerHTML = atraccion.tiempo_espera;
                            casilla.classList.add('atraccion')
                        } else if (usuario) {
                            casilla.innerHTML = usuario.alias;
                            casilla.classList.add('usuario')
                        } else {
                            casilla.innerHTML = '';
                        }
                    }
                }
        }, 2000)
    },

    async  getAtracciones() {
      return fetch(this.cadenaAPI + '/atracciones').then(async(resp) => {
          var atracciones = await resp.json()
          return atracciones
      }).catch(() => {
          clearInterval(this.intervalId)
          this.changePopup('block', 'Error al obtener atracciones');
          return []
      });
    },

    async getUsuarios() {
      return fetch(this.cadenaAPI + '/usuarios').then(async(resp) => {
          return await resp.json()
      }).catch(() => {
          clearInterval(this.intervalId)
          this.changePopup('block', 'Error al obtener usuarios');
          return []
      });
    },

    async blockZona(zona, city) {
      return fetch(this.cadenaAPI + '/zona/'+ zona, {
          method: 'PUT',
          mode: 'cors',
          headers: {
              'Content-Type': 'application/json'
          },
          body: JSON.stringify({
              ciudad: city
          })
      }).then(async(resp) => {
          var mensaje = await resp.json();
          const mensajeInfo = document.getElementById('info-zona-content')
          mensajeInfo.innerHTML = mensaje.message
          const infoZona = document.getElementById('info-zona')
        infoZona.style.display = 'block'
      }).catch(() => {
          this.changePopup('block', 'Error al bloquear una zona');
          return 'No se pudo actualizar'
      });
    },

    encontrarPosicion(array, x, y) {
        var elemento = array.find((element) => element.x == x && element.y == y);
        return elemento;
    },
    async eventBloquearZona() {
      console.log(this.zona, this.ciudad)
      console.log(await this.blockZona(this.zona, this.ciudad));
    },
    cerrarPopup(event) {
      if (event.target.className === 'popup-wrapper') {
        this.changePopup('none');
      } else if(event.target.className == 'popup-close') {
        this.changePopup('none');
      }
      this.intervalId = this.continuarIntervalo()
    },
    cerrarInfo() {
        const infoZona = document.getElementById('info-zona')
        infoZona.style.display = 'none'
    }
  },
  mounted: function() {
    var mapa = document.getElementById('mapa')
    for (var i = -1; i < 20; i++) {
        for (var j = -1; j < 20; j++) {
            var li = document.createElement('li');
            if (i == -1 && j != -1) {
                li.innerHTML = j;
                li.className = 'borde';
            } else if (i == -1 && j == -1) {
                li.className = 'fuera';
            } else if (j == -1 && i != -1) {
                li.innerHTML = i;
                li.className = 'borde';
            } else {
                li.id = i + '-' + j;

                li.className = 'casilla';
            }

            // zona 1
            if(j == 9 && i < 10 && i > -1) {
                li.classList.add('zona-1-derecha')
            }


            if(i == 9 && j < 10 && j > -1) {
                li.classList.add('zona-1-abajo')
            }

            // zona 2
            if(i == 10 && j < 10 && j > -1) {
                li.classList.add('zona-2-arriba')
            }

            if(j == 9 && i > 9) {
                li.classList.add('zona-2-derecha')
            }

            //zona 3
            if(j == 10 && i < 10 && i > -1) {
                li.classList.add('zona-3-izquierda')
            }


            if(i == 9 && j > 9) {
                li.classList.add('zona-3-abajo')
            }

            // zona 4
            if(j == 10 && i > 9) {
                li.classList.add('zona-4-izquierda')
            }


            if(i == 10 && j > 9) {
                li.classList.add('zona-4-arriba')
            }

            mapa.appendChild(li);
        }
    }
    this.intervalId = this.continuarIntervalo()
  }
}
</script>

<style>
body {
    min-width: 800px;
    background-color: rgba(238, 233, 233, 0.33);
}

.mapa {
    display: grid;
    grid-template-columns: repeat(21, 35px);
    grid-template-rows: repeat(21, 35px);
    border: 1px solid rgb(87, 85, 85);
    background-color: rgba(238, 233, 233, 0.33);
    padding: 0.4em;
    box-shadow: 2px 2px 5px rgb(145, 144, 144);
}

.padre {
    display: flex;
    justify-content: center;
}

li {
    display: flex;
    justify-content: center;
    align-items: center;
    list-style: none;
    font-family: "VT323";
    font-size: 1.5em;
    border: 1px solid #808080;
}

.titulo {
    text-transform: uppercase;
    font-family: Calisto MT, serif;
    color: rgb(44, 43, 43);
    font-size: 30px;
    text-align: center;
    word-spacing: 5px;
    letter-spacing: 5px;
}

.subtitulo {
    text-transform: capitalize;
    font-family: Lucida Bright, Georgia, serif;
    font-size: 14px;
    color: rgb(77, 74, 74);
    text-align: center;
    margin-top: 2em;
}

.borde {
    background: rgba(142, 142, 16, 0.551);
    border: 0px solid black;
}

.fuera {
    border: 0px solid black;
}

.formulario {
    display: flex;
    position: relative;
    justify-content: center;
    padding: 1em;
    background-color: rgba(238, 233, 233, 0.33);
    border: 1px solid black;
    width: 500px;
    box-shadow: 2px 2px 5px rgb(145, 144, 144);
}

.glosario-zonas {
    border: 1px solid black;
    background-color: rgba(238, 233, 233, 0.33);
    padding-left: 2em;
    padding-right: 2em;
    margin-bottom: 2em;
    box-shadow: 2px 2px 5px rgb(145, 144, 144);
    font-size: 10px;
}

.espacio-formulario {
    margin-left: 1em;
    margin-right: 1em;
}

.boton:hover {
    cursor: pointer;
    background-color: white;
}

.boton {
    background-color: rgb(213, 245, 126);
    border: 1px solid rgb(213, 245, 126);
    padding: 0.5em;
    padding-left: 1em;
    padding-right: 1em;
    border-radius: 0.25em;
    width: 15%;
}

.city {
    width: 40%;
}

.square {
    width: 7px;
    height: 7px;
    margin-right: 5px;
    display: inline-block;
}

.zona-1 {
    background-color: red;
}

.zona-2 {
    background-color: orange;
}

.zona-3 {
    background-color: blue;
}

.zona-4 {
    background-color: green;
}

.zona:hover {
    cursor: pointer;
}

.popup-wrapper {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.7);
}

.popup {
    font-family: Calisto MT, serif;
    text-align: center;
    display: flex;
    justify-content: center;
    width: 100%;
    max-width: 300px;
    background: white;
    margin: 10% auto;
    padding: 20px;
    position: relative;
    border-radius: 1em;
    height: 20%;
    max-height: 300px;
}

.popup-content {
    display: flex;
    justify-content: center;
    align-items: center;
}

.popup-close {
    font-family: monospace;
    position: absolute;
    color: grey;
    top: 10px;
    right: 15px;
    cursor: pointer;
    font-size: 1.5rem;
    padding: 0.2em;
}

.close {
    position: absolute;
    font-family: monospace;
    color: grey;
    cursor: pointer;
    font-size: 1rem;
    padding: 0.05em;
    top: 5px;
    right: 10px;
}

.close:hover {
    color: rgb(67, 67, 67);
}

#info-zona {
    background-color: rgba(28, 156, 211, 0.53);
    border: 1px solid rgba(28, 156, 211, 0.53);
    display: none;
    margin: 2em;
}

#info-zona-content {
    text-align: center;
    color: rgb(101, 101, 101);
    
}

.popup-close:hover {
    color: red;
}

.casilla {
    background-color: rgba(230, 230, 37, 0.522);
}

.atraccion {
    background-color: rgba(230, 111, 37, 0.522);
}

.usuario {
    background-color: rgba(37, 230, 66, 0.522);
}

.zona-1-derecha {
    border-right: 2px solid red;
}

.zona-1-abajo {
    border-bottom: 2px solid red;
}

.zona-2-derecha {
    border-right: 2px solid orange;
}

.zona-2-arriba {
    border-top: 2px solid orange;
}

.zona-3-izquierda {
    border-left: 2px solid blue;
}

.zona-3-abajo {
    border-bottom: 2px solid blue;
}

.zona-4-arriba {
    border-top: 2px solid rgb(8, 233, 8);
}

.zona-4-izquierda {
    border-left: 2px solid rgb(8, 233, 8);
}
</style>
