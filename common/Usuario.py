from common.Coordenadas2D import Coordenadas2D

class Usuario:
    def __init__(self, username, alias) -> None:
        self.username = username
        self.alias = alias
        self.coordenadas = Coordenadas2D(-1,-1)
        self.atraccion = None
    pass