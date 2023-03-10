from constantes import *
from logFile import logFile

class Cliente():

    def __init__(self):
        self.__logFile = logFile("Cliente")

    
    def log(self, msg : str) -> None:
        self.__logFile.log(msg)