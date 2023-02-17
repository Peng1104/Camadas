from enlace import enlace
from random import choices, randint
import numpy as np
import time

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

# use uma das 3 opcoes para atribuir à variável a porta usada
SERIAL_PORT_NAME = "/dev/ttyACM0"            # Ubuntu (variacao de)
# SERIAL_PORT_NAME = "/dev/tty.usbmodem1411"   # Mac    (variacao de)
# SERIAL_PORT_NAME = "COM3"                    # Windows(variacao de)


def main():
    try:
        # Ativa comunicacao. Inicia os threads e a comunicação seiral

        com = enlace(SERIAL_PORT_NAME)
        com.enable()

        # Envia o byte de sacrifício

        print("Sending sacrifice byte...")

        time.sleep(.2)
        com.sendData(b'00')
        time.sleep(1)

        # Lista de comandos

        print("Payload creation start")

        commands = {b'\x11\x00\x00\x00\x00': 1, b'\x11\x00\x00\xAA\x00': 2, b'\x11\xAA\x00\x00': 3,
                    b'\x11\x00\xAA\x00': 4, b'\x11\x00\x00\xAA': 5, b'\x11\x00\xAA': 6, b'\x11\xAA\x00': 7,
                    b'\x11\x00' : 8, b'\x11\xFF' : 9}
        
        selected = choices(list(commands.keys()), k=randint(10, 30))

        print(f"{len(selected)} commands selected.")
        print(f"Selected order = {[commands[key] for key in selected]}")

        payload = b''.join(selected)

        print(f"Payload finished, data size: {len(payload)}")

        print("Header creation start")

        header = b'\x01' + len(selected).to_bytes(length=2, byteorder='big') + \
            b'\xDD' + len(payload).to_bytes(length=2, byteorder='big') + b'\xDD'

        print("Sending header...")

        com.sendData(np.asarray(header))

        time.sleep(0.5)

        print(f"Header sended, {com.tx.getStatus()} bytes sended.")

        time.sleep(0.5)

        print("Sending data...")

        # as array apenas como boa pratica para casos de ter uma outra forma de dados
        com.sendData(np.asarray(payload))

        time.sleep(0.5)

        # A camada enlace possui uma camada inferior, TX possui um método para conhecermos o status da transmissão
        # O método não deve estar fincionando quando usado como abaixo. deve estar retornando zero. Tente entender como esse método funciona e faça-o funcionar.
        print(f"Payload sended, {com.tx.getStatus()} bytes sended.")

        time.sleep(0.5)

        # Esperando Byte de sacrifício...

        print("Waiting response...")

        counter = 0

        while com.rx.getIsEmpty() and counter < 11:
            time.sleep(0.5)
            counter += 1
        
        if counter >= 11:
            print("Time out")
            com.disable()
            return

        amount = b''

        while True:
            byte = com.getData(1)[0][0]
            
            if byte == 1:
                print("Header start index received")
                continue

            elif byte == 221:
                print("Header end index received")
                amount = int.from_bytes(amount, byteorder='big')
                break
            
            else:
                amount += byte.to_bytes(length=2, byteorder='big')
        
        if len(selected) != amount:
            print(f"Foi confirmado {amount} enviados, esperado era {len(selected)}")
        
        else:
            print(f"Foi confirmado o recebimento de todos os {amount} commands")

        # Encerra comunicação
        print("-------------------------")
        print("Comunicação encerrada")
        print("-------------------------")
        com.disable()

    except Exception as e:
        print("Error ->")
        print(e)
        com.disable()

    # so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    main()
