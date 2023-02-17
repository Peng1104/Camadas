#####################################################
# Camada Física da Computação
# Carareto
# 11/08/2022
# Aplicação
####################################################

# esta é a camada superior, de aplicação do seu software de comunicação serial UART.
# para acompanhar a execução e identificar erros, construa prints ao longo do código!

from enlace import *
from random import choices, randint
import time
import numpy as np

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

# use uma das 3 opcoes para atribuir à variável a porta usada
# SERIAL_PORT_NAME = "/dev/ttyACM0"            # Ubuntu (variacao de)
# SERIAL_PORT_NAME = "/dev/tty.usbmodem1411"   # Mac    (variacao de)
SERIAL_PORT_NAME   = "COM5"                    # Windows(variacao de)


def main():
    try:
        # declaramos um objeto do tipo enlace com o nome "com". Essa é a camada inferior à aplicação. Observe que um parametro
        # para declarar esse objeto é o nome da porta.
        com1 = enlace(SERIAL_PORT_NAME)

        # Ativa comunicacao. Inicia os threads e a comunicação seiral
        com1.enable()

        # Byte de sacrifício

        time.sleep(.2)
        com1.sendData(b'00')
        time.sleep(1)

        print("esperando 1 byte de sacrifício")
        rxBuffer, nRx = com1.getData(1)
        com1.rx.clearBuffer()
        time.sleep(.1) 

        # Lista de comandos

        print("Payload start")

        commands = [b'\x11\x00\x00\x00\x00', b'\x11\x00\x00\xAA\x00', b'\x11\xAA\x00\x00',
                    b'\x11\x00\xAA\x00', b'\x11\x00\x00\xAA', b'\x11\x00\xAA', b'\x11\xAA\x00', b'\x11\x00', b'\x11\xFF']

        selected = choices(commands, k=randint(10, 30))

        payload = b''.join(selected)
        payloadLen = len(payload)

        print(f"Payload finished, data size: {payloadLen}")

        print("Header start")

        header = b'\x01' + payloadLen.to_bytes(byteorder='big') + b'\xDD'

        # aqui você deverá gerar os dados a serem transmitidos.
        # seus dados a serem transmitidos são um array bytes a serem transmitidos. Gere esta lista com o
        # nome de txBuffer. Esla sempre irá armazenar os dados a serem enviados.

        # txBuffer = imagem em bytes!
        #payload = open("./img/coracao.png", 'rb').read()
        #data = payload

        # faça aqui uma conferência do tamanho do seu txBuffer, ou seja, quantos bytes serão enviados.

        # finalmente vamos transmitir os todos. Para isso usamos a funçao sendData que é um método da camada enlace.
        # faça um print para avisar que a transmissão vai começar.
        # tente entender como o método send funciona!
        # Cuidado! Apenas trasmita arrays de bytes!

        print("Sending header...")
        
        com1.sendData(header)

        time.sleep(1)

        command = b''

        while True:
            rxBuffer, nRx = com1.getData(1)
            value = rxBuffer[0]

            if value == 1:
                print("Header received")
                continue
            if value == 221:
                break

            command += value.to_bytes(byteorder='big')
        
        txLen = int.from_bytes(command, byteorder='big')
        
        print(txLen)

        time.sleep(1)

        print("Sending data...")

        # as array apenas como boa pratica para casos de ter uma outra forma de dados
        com1.sendData(np.asarray(payload))

        print("Data sent")

        # A camada enlace possui uma camada inferior, TX possui um método para conhecermos o status da transmissão
        # O método não deve estar fincionando quando usado como abaixo. deve estar retornando zero. Tente entender como esse método funciona e faça-o funcionar.
        txSize = com1.tx.getStatus()
        print("Size sended = {}" .format(txSize))

        # Agora vamos iniciar a recepção dos dados. Se algo chegou ao RX, deve estar automaticamente guardado
        # Observe o que faz a rotina dentro do thread RX
        # print um aviso de que a recepção vai começar.

        # Será que todos os bytes enviados estão realmente guardadas? Será que conseguimos verificar?
        # Veja o que faz a funcao do enlaceRX  getBufferLen

        # acesso aos bytes recebidos
        rxBuffer, nRx = com1.getData(txLen)
        print("recebeu {} bytes" .format(len(rxBuffer)))

        #writter = open("img\Coracao2.png", "wb")
        #writter.write(rxBuffer)
        #writter.close()

        command = b''
        counter = 1

        for i in range(len(rxBuffer)):
            value = rxBuffer[i]

            if value == 17 and i > 0:
                print(f"Comando {commands.index(command) + 1} -> {command}")
                command = b''
                counter += 1
            
            command += value.to_bytes(byteorder='big')
             
        print(f"Comando {commands.index(command)} -> {command}")
        print(f"Foram recebidos {counter} comandos, de {len(selected)} enviados")

        # Encerra comunicação
        print("-------------------------")
        print("Comunicação encerrada")
        print("-------------------------")
        com1.disable()

    except Exception as e:
        print("Error ->")
        print(e)
        com1.disable()

    # so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    main()
