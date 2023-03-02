from enlace import enlace
import time
from datetime import datetime
from os import getcwd
from os.path import basename

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

# use uma das 3 opcoes para atribuir à variável a porta usada
SERIAL_PORT_NAME = "/dev/ttyACM1"            # Ubuntu (variacao de)
# SERIAL_PORT_NAME = "/dev/tty.usbmodem1411"   # Mac    (variacao de)
# SERIAL_PORT_NAME = "COM5"                    # Windows(variacao de)

LOG_FILE = getcwd() + "/logs/" + basename(__file__) + ".log"

def log(msg : str) -> None:
    with open(LOG_FILE, "a", encoding='utf-8') as file:
        file.write(datetime.now().strftime('[%d/%m/%Y %H:%M:%S] ') + msg)
        print(msg)

# HEAD format h0 + h1 + h2 + h3 + h4 + h5 + h6 + h7 + h8 + h9
# h0 – Tipo de mensagem  # h1 – Se tipo for 1: número do servidor Qualquer outro tipo: livre # h2 – Livre # h3 – Número total de pacotes do arquivo
# h4 – Número do pacote sendo enviado # h5 – Se tipo for handshake: id do arquivo (crie um para cada arquivo). Se tipo for dados: tamanho do payload.
# h6 – Pacote solicitado para recomeço quando a erro no envio # h7 – Ùltimo pacote recebido com sucesso #h8 – h9 – CRC (Por ora deixe em branco. Fará parte do projeto 5).
# Payload 0 - 114 Bytes, the packet data.
# End of packet 4 Bytes (0xAA 0xBB 0xCC 0xDD)

PACKET_END = b'\xAA\xBB\xCC\xDD'

PACKET_TYPE1_HANDSHAKE = b'\x01'
PACKET_TYPE2_SERVER_LIVRE = b'\x02'
PACKET_TYPE3_DATA = b'\x03'
PACKET_TYPE4_VALIDATION = b'\x04'
PACKET_TYPE5_TIMEOUT = b'\x05'
PACKET_TYPE6_ERROR = b'\x06'

SERVER_ID = b'\x45'

HANDSHAKE = PACKET_TYPE1_HANDSHAKE + SERVER_ID + int(0).to_bytes(length=1, byteorder='big') + PACKET_END

CONFIRMATION_PACKET = int(0).to_bytes(length=2, byteorder='big') + int(1).to_bytes(
    length=5, byteorder='big') + int(1).to_bytes(length=5, byteorder='big') + PACKET_END


def confirmHandshake(com: enlace) -> bool:
    # Wait for client to send handshake

    print("Waiting for handshake...")  # DEBUG

    handshake, _ = com.getData(10)

    print("Handshake received.")  # DEBUG

    # Reads the handshake packet
    msgType = int.from_bytes(handshake[:1], byteorder='big')
    serverId = int.from_bytes(handshake[1:2], byteorder='big')
    totalPackets = int.from_bytes(handshake[2:3], byteorder='big')
    archiveId = int.from_bytes(handshake[4:5], byteorder='big')

    end, _ = com.getData(3)
    com.rx.clearBuffer()

    # Checks if the handshake is valid
    if msgType == 1 and serverId != SERVER_ID and totalPackets == 0 and end == PACKET_END:
        print("Handshake received is valid.")
        # Send handshake confirmation
        com.sendData(HANDSHAKE)
        return True
    return False


def validatePacket(com: enlace, packetNumber: int, data: list, end: bytes) -> bool:

    error = False

    if len(data) + 1 != packetNumber:
        print(
            f"Packet {len(data) + 1} is not valid, recived packet numer is {packetNumber}.")
        error = True

    # Checks if the packet is not valid
    if end != PACKET_END:
        print(
            f"Packet {len(data) + 1} is not valid, end of packet is not correct. Received: {end} expected: {PACKET_END}")
        com.rx.clearBuffer()
        error = True

    if error:
        payload = (len(data) + 1).to_bytes(length=5, byteorder='big')

        # Send error packet to client
        com.sendData(len(payload).to_bytes(length=2, byteorder='big') + int(1).to_bytes(
            length=5, byteorder='big') + int(1).to_bytes(length=5, byteorder='big') + payload + PACKET_END)

    else:
        print(f"Packet {packetNumber} is valid.")

        # Send confirmation packet to client
        com.sendData(CONFIRMATION_PACKET)
        time.sleep(0.5)

        return True


def main():
    try:
        # Ativa comunicacao. Inicia os threads e a comunicação seiral
        com = enlace(SERIAL_PORT_NAME)
        com.enable()

        # Wait for handshake confirmation
        if not confirmHandshake(com):
            return

        # Read first packet (Especial Case)

        head, _ = com.getData(12)  # Wait for packet head

        # Reads the head
        payloadSize = int.from_bytes(head[:2], byteorder='big')
        totalPackets = int.from_bytes(head[2:7], byteorder='big')
        # Must read the first packet to get it
        recivedPacketNumber = int.from_bytes(head[7:], byteorder='big')

        print(f'Payload Size: {payloadSize}')

        # Reads payload data

        data = []

        payload, _ = com.getData(payloadSize)

        end, _ = com.getData(3)

        if not validatePacket(com, recivedPacketNumber, data, end):
            return

        data.append(payload)

        while len(data) < totalPackets:
            print(f"Reading {len(data) + 1} of {totalPackets}.")  # DEBUG

            head, _ = com.getData(12)

            payloadSize = int.from_bytes(head[:2], byteorder='big')
            totalPackets = int.from_bytes(head[2:7], byteorder='big')
            recivedPacketNumber = int.from_bytes(head[7:], byteorder='big')

            payload, _ = com.getData(payloadSize)

            end, _ = com.getData(3)

            if not validatePacket(com, recivedPacketNumber, data, end):
                continue

            data.append(payload)

        data = b''.join(data)

        print(f"{len(data)} of data received, writing to file...")

        with open("img/received.png", "wb") as file:
            file.write(data)

        print("File written.")

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
