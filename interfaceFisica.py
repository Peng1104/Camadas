#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#####################################################
# Carareto
# 17/02/2018
####################################################

# Importa pacote de comunicação serial
import serial

# importa pacote para conversão binário ascii
import binascii

#################################
# Interface com a camada física #
#################################


class fisica():

    def __init__(self, serial_port_name: str) -> None:
        self.name = serial_port_name

        # Configurações da porta serial
        baudrate = 115200  # 9600
        bytesize = serial.EIGHTBITS
        parity = serial.PARITY_NONE
        stop = serial.STOPBITS_ONE
        timeout = 0.1

        self.port = serial.Serial(
            serial_port_name, baudrate, bytesize, parity, stop, timeout)

        self.rxRemain = b''

    def close(self) -> None:
        self.port.close()

    def flush(self):
        self.port.flushInput()
        self.port.flushOutput()

    def encode(self, data):
        return binascii.hexlify(data)

    def decode(self, data):
        # RX ASCII data after reception
        return binascii.unhexlify(data)

    def write(self, txBuffer):
        """ Write data to serial port

        This command takes a buffer and format
        it before transmit. This is necessary
        because the pyserial and arduino uses
        Software flow control between both
        sides of communication.
        """
        nTx = self.port.write(self.encode(txBuffer))
        self.port.flush()
        return (nTx/2)

    def read(self, nBytes : int) -> tuple:
        """ Read nBytes from the UART com port

        Nem toda a leitura retorna múltiplo de 2
        devemos verificar isso para evitar que a funcao
        self.decode seja chamada com números ímpares.
        """
        rxBuffer = self.port.read(nBytes)
        rxBufferConcat = self.rxRemain + rxBuffer
        nValid = (len(rxBufferConcat)//2)*2
        rxBufferValid = rxBufferConcat[0:nValid]
        self.rxRemain = rxBufferConcat[nValid:]
        try:
            """ As vezes acontece erros na decodificacao
            fora do ambiente linux, isso tenta corrigir
            em parte esses erros. Melhorar futuramente."""
            "muitas vezes um flush no inicio resolve!"
            rxBufferDecoded = self.decode(rxBufferValid)
            nRx = len(rxBuffer)
            return (rxBufferDecoded, nRx)
        except:
            print("[ERRO] interfaceFisica, read, decode. buffer : {}".format(
                rxBufferValid))
            return (b"", 0)
