from constantes import *
from enlace import enlace
from logFile import logFile

class Cliente():

    def __init__(self, serial_port_name: str):
        self.com = enlace(logFile("Cliente", False), serial_port_name)

    
    def log(self, msg : str) -> None:
        self.__logFile.log(msg)