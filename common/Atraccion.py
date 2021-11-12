import common.Coordenadas2D

class Atraccion:
    def __init__(self, id, timec, nvisitors, coordenadas) -> None:
        self.id = id
        self.cola = 0
        self.timec = timec
        self.tiempoEspera = 0
        self.nvisitors = nvisitors
        self.coordenadas = coordenadas