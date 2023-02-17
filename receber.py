from enlace import enlace
import numpy as np
import time

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

# use uma das 3 opcoes para atribuir à variável a porta usada
# SERIAL_PORT_NAME = "/dev/ttyACM0"            # Ubuntu (variacao de)
# SERIAL_PORT_NAME = "/dev/tty.usbmodem1411"   # Mac    (variacao de)
SERIAL_PORT_NAME = "COM5"                    # Windows(variacao de)


def main():
    try:
        # Ativa comunicacao. Inicia os threads e a comunicação seiral

        com = enlace(SERIAL_PORT_NAME)
        com.enable()

        # Byte de sacrifício

        print("Esperando receber o byte de sacrifício para limpar o buffer.")

        rxBuffer, nRx = com.getData(1)
        com.rx.clearBuffer()
        
        print("Byte de sacrifício recebido.", "Buffer limpo.")
        print("Esperando header...")

        time.sleep(1.5)

        amount = b''
        payloadSize = b''

        while True:
            byte = com.getData(1)[0][0]

            if type(amount) == int:
                if byte == 221:
                    print("Header end index received")
                    payloadSize = int.from_bytes(payloadSize, byteorder='big')
                    break

                payloadSize += byte.to_bytes(byteorder='big')
            
            elif byte == 1:
                print("Header start index received")

            elif byte == 221:
                print("Header separator index received")
                amount = int.from_bytes(amount, byteorder='big')
            
            else:
                amount += byte.to_bytes(byteorder='big')
        
        print(f"Expenting {amount} commands.")

        time.sleep(1)

        print(f"Reading {payloadSize} bytes of data...")

        # Agora vamos iniciar a recepção dos dados. Se algo chegou ao RX, deve estar automaticamente guardado
        # Observe o que faz a rotina dentro do thread RX
        # print um aviso de que a recepção vai começar.

        # Será que todos os bytes enviados estão realmente guardadas? Será que conseguimos verificar?
        # Veja o que faz a funcao do enlaceRX  getBufferLen

        # acesso aos bytes recebidos
        rxBuffer, nRx = com.getData(payloadSize)
        print(f"Recebidos {nRx} bytes.")

        # Lista de comandos possíveis
        commands = [b'\x00\x00\x00\x00', b'\x00\x00\xAA\x00', b'\xAA\x00\x00',
                    b'\x00\xAA\x00', b'\x00\x00\xAA', b'\x00\xAA', b'\xAA\x00', b'\x00', b'\xFF']

        command = b''
        counter = 1

        for n in range(1, nRx):
            byte = rxBuffer[n]

            if byte == 17:
                print(f"Command {commands.index(command) + 1} recived", f"Value = {command}")
                command = b''
                counter += 1
            
            else:
                command += byte.to_bytes(byteorder='big')
        
        print(f"Command {commands.index(command) + 1} recived", f"Value = {command}")

        print(f"{counter} commands recived, expected {amount} commands.")

        header = b'\x01' + counter.to_bytes(byteorder='big') + b'\xDD'

        print("Sending response header...")
        com.sendData(np.asarray(header))

        # Encerra comunicação
        print("-------------------------")
        print("Comunication ended.")
        print("-------------------------")
        com.disable()

    except Exception as e:
        print("Error ->", e)
        com.disable()

    # so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    main()