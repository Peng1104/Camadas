#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################
# Camada Física da Computação
# Carareto
# 17/02/2018
#  Camada de Enlace
####################################################

# Threads
from threading import Thread

# Class


class TX:

    def __init__(self, fisica):
        self.fisica = fisica
        self.__buffer = []
        self.transLen = 0
        self.threadMutex = False
        self.threadStop = False

        thread = Thread(target=self.thread, args=())
        thread.start()

    def thread(self):
        while not self.threadStop:
            if self.getIsBussy():
                self.transLen = self.fisica.write(self.__buffer.pop(0))
                self.threadMutex = False

    def threadKill(self):
        self.threadStop = True

    def threadPause(self):
        self.threadMutex = False

    def threadResume(self):
        self.threadMutex = True

    def sendBuffer(self, data):
        self.transLen = 0
        self.__buffer.append(data)
        self.threadMutex = True

    def getBufferLen(self):
        return sum(len(x) for x in self.__buffer)

    def getStatus(self):
        return self.transLen

    def getIsBussy(self):
        return self.threadMutex or len(self.__buffer) > 0
