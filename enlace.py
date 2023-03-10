#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################
# Camada Física da Computação
# Carareto
# 17/02/2018
#  Camada de Enlace
####################################################

# Importa pacote de tempo para usar sleep
from time import sleep

# Importa formato de dados
from numpy import asarray

# Interface Física
from interfaceFisica import fisica

# enlace Tx e Rx
from enlaceRx import RX
from enlaceTx import TX


class enlace():

    def __init__(self, serial_port_name: str) -> None:
        self.fisica = fisica(serial_port_name)
        self.rx = RX(self.fisica)
        self.tx = TX(self.fisica)

    def disable(self) -> None:
        self.rx.threadKill()
        self.tx.threadKill()
        sleep(1)
        self.fisica.close()

    def sendData(self, data : bytes) -> None:
        self.tx.sendBuffer(asarray(data))

    def clearBuffer(self) -> None:
        self.rx.clearBuffer()

    def getData(self, amount : int) -> bytes:
        return self.rx.getNData(amount)
