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

# Threads
from threading import Thread

# Class


class TX:

    def __init__(self, fisica):
        self.fisica = fisica
        self.buffer = bytes(bytearray())
        self.transLen = 0
        self.empty = True
        self.threadMutex = False
        self.threadStop = False

        self.thread = Thread(target=self.thread, args=())
        self.thread.start()

    def thread(self):
        while not self.threadStop:
            if self.threadMutex:
                self.transLen = self.fisica.write(self.buffer)
                self.threadMutex = False

    def threadKill(self):
        self.threadStop = True

    def threadPause(self):
        self.threadMutex = False

    def threadResume(self):
        self.threadMutex = True

    def sendBuffer(self, data):
        self.transLen = 0
        self.buffer = data
        self.threadMutex = True

    def getBufferLen(self):
        return len(self.buffer)

    def getStatus(self):
        return self.transLen

    def getIsBussy(self):
        return self.threadMutex
