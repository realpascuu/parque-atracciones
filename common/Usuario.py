from common.Coordenadas2D import Coordenadas2D

class Usuario:
    def __init__(self, username, alias, coordenadas) -> None:
        self.username = username
        self.alias = alias
        self.coordenadas = coordenadas
        self.atraccion = None
    pass