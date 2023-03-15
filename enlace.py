#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#####################################################
# Camada Física da Computação
# Carareto
# 17/02/2018
#  Camada de Enlace
####################################################

from constantes import *

# Importa pacote de tempo para usar sleep
from time import sleep

# Importa formato de dados
from numpy import asarray

# Interface Física
from interfaceFisica import fisica

# enlace Tx e Rx
from enlaceRx import RX
from enlaceTx import TX

# The log file
from logFile import logFile


class enlace():

    def __init__(self, log_file: logFile, serial_port_name: str) -> None:
        self.__enabled = False
        self.__log_file = log_file

        self.log("Iniciando interface fisica...")
        self.fisica = fisica(serial_port_name)

        self.log("Iniciando interface de transmissão...")
        self.rx = RX(self.fisica)

        self.log("Iniciando interface de recepção...")
        self.tx = TX(self.fisica)

        self.__last_packet = None
        self.clearBuffer()
        self.__enabled = True

    def log(self, message: str) -> None:
        self.__log_file.log(message)

    def isEnabled(self) -> bool:
        return self.__enabled

    def disable(self) -> None:
        self.__enabled = False
        self.log("Desabilitando a comunicação...")

        try:
            self.rx.threadKill()
            self.tx.threadKill()
            sleep(1)  # Espera a thread morrer
            self.fisica.close()

        except Exception as e:
            self.log(
                f"An error as occurred while disabling the communication.\n{e}")

    def clearBuffer(self) -> None:
        self.rx.clearBuffer()

    def sendData(self, data: bytes) -> None:
        if data is not None:
            self.log(f"Sending {len(data)} bytes...")

            if data[0].to_bytes(length=1, byteorder='big') == DATA:
                self.log(f"Data: {data[:HEAD_SIZE]} ... {data[-END_SIZE:]}")

            else:
                self.log(f"Data: {data}")

            self.__last_packet = data
            self.tx.sendBuffer(asarray(data))
        else:
            self.__last_packet = None

    def readPacket(self, retry: bool = True) -> tuple[bytes, bytes, bytes]:
        time_out_time = 0

        while self.rx.getBufferLen() < MIN_PACKET_SIZE:
            sleep(CHECK_DELAY)
            time_out_time += CHECK_DELAY

            if time_out_time >= 20:
                if retry:
                    self.log("Sending timeout packet...")
                    self.sendData(TIMEOUT_PACKET)
                return None, None, None

            if retry and time_out_time % 5 == 0:
                self.log(
                    f"Sending last packet again ({time_out_time // 5})...")
                self.sendData(self.__last_packet)

        head = self.rx.getNData(HEAD_SIZE)
        payload = None

        if head[0].to_bytes(length=1, byteorder='big') == DATA:
            payload = self.rx.getNData(head[5])

        end = self.rx.getNData(END_SIZE)

        return head, payload, end

    def getData(self, amount: int) -> bytes:
        while self.rx.getBufferLen() < amount:
            sleep(0.5)
        return self.rx.getNData(amount)
