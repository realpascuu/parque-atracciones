function changePopup(cadena) {
    const popup = document.getElementById('popup-wrapper');
    popup.style.display = cadena;
}

async function getAtracciones() {
    return fetch('https://localhost:3000/atracciones').then(async(resp) => {
        var atracciones = await resp.json()
        return atracciones
    }).catch((error) => {
        changePopup('block');
        return []
    });
}

async function getUsuarios() {
    return fetch('https://localhost:3000/usuarios').then(async(resp) => {
        return await resp.json()
    }).catch((error) => {
        changePopup('block');
        return []
    });
}

async function blockZona(zona, city) {
    return fetch('https://localhost:3000/zona', {
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
    }).catch((error) => {
        changePopup('block');
        return 'No se pudo actualizar'
    });
}

function encontrarPosicion(array, x, y) {
    var elemento = array.find((element) => element.x == x && element.y == y);
    return elemento;
}

document.addEventListener('DOMContentLoaded', () => {
    var mapa = document.getElementById('mapa');
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

    setInterval(async() => {
        var content = await Promise.all(
            [getAtracciones(), getUsuarios()]
        );

        for (var i = 0; i < 20; i++) {
            for (var j = 0; j < 20; j++) {
                var casilla = document.getElementById(i + '-' + j);
                var atraccion = encontrarPosicion(content[0], i, j);
                var usuario = encontrarPosicion(content[1], i, j);
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
    }, 1500);
});

var boton = document.getElementById("envioZona");
boton.addEventListener('click', async() => {
    var city = document.getElementById('city').value;
    var zona = document.getElementById('zona').value;
    console.log(await blockZona(zona, city));
});

var closePopup = document.querySelector('.popup-close');
closePopup.addEventListener('click', () => {
    changePopup('none');
});

const popup = document.getElementById('popup-wrapper');
popup.addEventListener('click', e => {
    if (e.target.className === 'popup-wrapper') {
        changePopup('none');
    }
});