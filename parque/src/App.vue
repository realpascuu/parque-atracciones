<template>
<div>
    <div class="titulo">
        <p>Parque de atracciones</p>
    </div>
    <div class="subtitulo">
        <p>Bloqueo de zonas parque</p>
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
    <div @click="cerrarPopup($event)" class="popup-wrapper" id="popup-wrapper">
        <div class="popup">
            <div @click="cerrarPopup($event)" class="popup-close">x</div>
            <div class="popup-content">
                Error al conectar con la API
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
      cadenaAPI: 'https://localhost:3000',
      intervalId: ''
    }
  },
  methods: {
    changePopup(cadena) {
        const popup = document.getElementById('popup-wrapper')
        popup.style.display = cadena;
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
        }, 1500)
    },

    async  getAtracciones() {
      return fetch(this.cadenaAPI + '/atracciones').then(async(resp) => {
          var atracciones = await resp.json()
          return atracciones
      }).catch(() => {
          clearInterval(this.intervalId)
          this.changePopup('block');
          return []
      });
    },

    async getUsuarios() {
      return fetch(this.cadenaAPI + '/usuarios').then(async(resp) => {
          return await resp.json()
      }).catch(() => {
          clearInterval(this.intervalId)
          this.changePopup('block');
          return []
      });
    },

    async blockZona(zona, city) {
      return fetch(this.cadenaAPI + '/zona', {
          method: 'PUT',
          mode: 'cors',
          headers: {
              'Content-Type': 'application/json'
          },
          body: JSON.stringify({
              zona: zona,
              ciudad: city
          })
      }).then(async(resp) => {
          var mensaje = await resp.json();
          return mensaje.message
      }).catch(() => {
          this.changePopup('block');
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
    justify-content: center;
    padding: 1em;
    background-color: rgba(238, 233, 233, 0.33);
    border: 1px solid black;
    width: 500px;
    box-shadow: 2px 2px 5px rgb(145, 144, 144);
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
</style>
