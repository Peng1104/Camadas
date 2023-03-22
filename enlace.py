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

    def __init__(self, log_file: logFile, retry_timer : int, id : int, serial_port_name: str) -> None:
        self.__enabled = False
        self.__log_file = log_file
        self.__id = id
        self.__retry_timer = retry_timer

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
        if self.isEnabled():
            self.rx.clearBuffer()

    def sendPacket(self, packet: bytes, own: bool = True) -> None:
        if not self.isEnabled():
            return
        
        if own:
            self.__last_packet = packet

            if packet is None:
                return
        else:
            self.log("Passing packet trough...")

        if packet[0].to_bytes(1, 'big') == DATA:
            self.log(f"Data: {packet[:HEAD_SIZE]} ... {packet[-END_SIZE:]}")
            self.log(f"Sending {len(packet)} bytes...")

        else:
            self.log(f"Data: {packet}")
        
        self.tx.sendBuffer(asarray(packet))

    def recivePacket(self, senderId : int, retry: bool = True, timer : int = 0) -> tuple[bytes, bytes, bytes]:
        if not self.isEnabled():
            return None, None, None

        while self.rx.getBufferLen() < MIN_PACKET_SIZE:
            sleep(CHECK_DELAY)
            timer += CHECK_DELAY

            if timer >= TIMEOUT_TIME:
                if retry:
                    self.log("Sending timeout packet...")
                    self.sendPacket(TIMEOUT + senderId.to_bytes(1, 'big') + FIXED_END)
                return None, None, None

            if retry and timer % self.__retry_timer == 0:
                self.log(
                    f"Sending last packet again ({timer // self.__retry_timer})...")
                self.sendPacket(self.__last_packet)

        head = self.rx.getBuffer(HEAD_SIZE)

        ignore = not head[1] == self.__id

        payload = None

        # Check if type is data and get the payload of the packet
        if head[0].to_bytes(1, 'big') == DATA:
            payloadSize = head[5]

            # Check if the payload is complete, if not, clear the buffer
            if self.rx.getBufferLen() < payloadSize + END_SIZE:
                self.clearBuffer()

                if ignore:
                    return self.recivePacket(senderId, retry, timer)

                return head, None, None
            else:
                payload = self.rx.getBuffer(payloadSize)

        end = self.rx.getBuffer(END_SIZE)

        if ignore:
            self.sendPacket(head + payload + end, False)
            return self.recivePacket(senderId, retry, timer)

        return head, payload, end
