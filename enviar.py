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
SERIAL_PORT_NAME = "COM3"                    # Windows(variacao de)

# HEAD format PayloadSize 2 Byte + 5 Byte PacketNumber + 5 Bytes TotalPackets
# Payload 0 - 50 Bytes, the packet data.
# # End of packet 3 Bytes (0xDD 0xEE 0xFF)

PACKET_END = b'\xDD\xEE\xFF'

HANDSHAKE = int(0).to_bytes(length=2, byteorder='big') + int(1).to_bytes(
            length=5, byteorder='big') + int(1).to_bytes(length=5, byteorder='big') + PACKET_END

def sendHandshake(com):
    com.sendData(HANDSHAKE)

    print("Waiting response...")

    counter = 0

    while com.rx.getIsEmpty() and counter < 11:
        time.sleep(0.5)
        counter += 1
    
    if counter >= 10:
        print("Servidor Inativo. Tentar novamente? (S/N)")
        
        if input().lower() == 's':
            return sendHandshake(com)
        else:
            com.disable()
            print("Conexão encerrada.")
            return False
    else:
        com.rx.clearBuffer()
        print("Handshake realizado com sucesso.")
        return True

def main():
    try:
        # Ativa comunicacao. Inicia os threads e a comunicação seiral

        com = enlace(SERIAL_PORT_NAME)
        com.enable()

        if not sendHandshake(com):
            return
        
        print("Data creation start")

        with open("img/projeto3.png", "rb") as file:
            data = file.read()

        total = len(data) // 50 + 1

        packets = []

        while len(data) > 50:
            payload = data[:50]
            data = data[50:]

            head = int(50).to_bytes(length=2, byteorder='big') + int(len(packets) + 1).to_bytes(
                length=5, byteorder='big') + total.to_bytes(length=5, byteorder='big')

            packets.append(head + payload + PACKET_END)

        head = int(len(data)).to_bytes(length=2, byteorder='big') + int(len(packets) + 1).to_bytes(
            length=5, byteorder='big') + total.to_bytes(length=5, byteorder='big')

        packets.append(head + data + PACKET_END)

        print(f"Data processing finished, to be send {len(packets)} packets")

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
            print(
                f"Foi confirmado {amount} enviados, esperado era {len(selected)}")

        else:
            print(
                f"Foi confirmado o recebimento de todos os {amount} commands")

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
