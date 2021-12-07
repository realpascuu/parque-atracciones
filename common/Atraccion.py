import common.Coordenadas2D

class Atraccion:
    def __init__(self, id, timec, nvisitors, coordenadas, tiempoEspera) -> None:
        self.id = id
        self.cola = 0
        self.timec = timec
        self.tiempoEspera = tiempoEspera
        self.nvisitors = nvisitors
        self.coordenadas = coordenadas