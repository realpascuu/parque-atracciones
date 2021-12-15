async function llamadaAPI() {
    fetch('https://localhost:3000/atracciones').then(async(resp) => {
        var mensaje = await resp.json()
        mensaje.forEach((element) => {
            console.log(mensaje);
            var li = document.getElementById(element.x + '-' + element.y);
            li.innerHTML = element.tiempo_espera;
        })
    }).catch((error) => {
        console.log(error)
    });
}

document.addEventListener('DOMContentLoaded', async() => {
    var mapa = document.getElementById('mapa');
    for (var i = -1; i < 20; i++) {
        for (var j = -1; j < 20; j++) {
            var li = document.createElement('li');
            if (i == -1 && j != -1) {
                li.innerHTML = j;
            } else if (j == -1 && i != -1) {
                li.innerHTML = i;
            } else {
                li.id = i + '-' + j;
            }
            li.className = 'casilla';
            mapa.appendChild(li);
        }
    }
    await llamadaAPI();
});