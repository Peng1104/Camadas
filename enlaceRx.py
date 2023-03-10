#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################
# Camada Física da Computação
# Carareto
# 17/02/2018
#  Camada de Enlace
####################################################

# Importa pacote de tempo
import time

# Thread
from threading import Thread

# Class


class RX(object):

    def __init__(self, fisica):
        self.fisica = fisica
        self.buffer = bytes(bytearray())
        self.threadStop = False
        self.threadMutex = True
        self.READLEN = 1024

        self.thread = Thread(target=self.thread, args=())
        self.thread.start()

    def thread(self):
        while not self.threadStop:
            if self.threadMutex == True:
                rxTemp, nRx = self.fisica.read(self.READLEN)
                if nRx > 0:
                    self.buffer += rxTemp
                time.sleep(0.01)

    def threadKill(self):
        self.threadStop = True

    def threadPause(self):
        self.threadMutex = False

    def threadResume(self):
        self.threadMutex = True

    def getIsEmpty(self):
        return self.getBufferLen() == 0

    def getBufferLen(self):
        return len(self.buffer)

    def getAllBuffer(self, len):
        self.threadPause()
        b = self.buffer[:]
        self.clearBuffer()
        self.threadResume()
        return b

    def getBuffer(self, nData):
        self.threadPause()
        b = self.buffer[0:nData]
        self.buffer = self.buffer[nData:]
        self.threadResume()
        return b

    def getNData(self, amount : int) -> bytes:
        while self.getBufferLen() < amount:
            time.sleep(0.05)
        return self.getBuffer(amount)

    def clearBuffer(self) -> None:
        self.buffer = b""
