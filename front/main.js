function changePopup(cadena) {
    const popup = document.getElementById('popup-wrapper');
    popup.style.display = cadena;
}

async function llamadaAPI() {
    fetch('https://localhost:3000/atracciones').then(async(resp) => {
        var mensaje = await resp.json()
        mensaje.forEach((element) => {
            console.log(mensaje);
            var li = document.getElementById(element.x + '-' + element.y);
            li.innerHTML = element.tiempo_espera;
        })
    }).catch((error) => {
        changePopup('block');
    });
}

document.addEventListener('DOMContentLoaded', async() => {
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
    await llamadaAPI();
});

var boton = document.getElementById("envioZona");
boton.addEventListener('click', () => {
    var city = document.getElementById('city').value;
    var zona = document.getElementById('zona').value;
    console.log(city, zona);
    changePopup('block');
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