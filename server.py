from enlace import enlace
import time
from datetime import datetime
from os import getcwd
from os.path import basename, exists, isfile
from zipfile import ZipFile

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

# use uma das 3 opcoes para atribuir à variável a porta usada
SERIAL_PORT_NAME = "/dev/ttyACM1"            # Ubuntu (variacao de)
# SERIAL_PORT_NAME = "/dev/tty.usbmodem1411"   # Mac    (variacao de)
# SERIAL_PORT_NAME = "COM5"                    # Windows(variacao de)

LOG_FILE = getcwd() + "/logs/" + basename(__file__) + ".log"

if exists(LOG_FILE):
    if isfile(LOG_FILE):
        ZipFile(LOG_FILE + ".zip", "a").write(LOG_FILE)


def log(msg: str) -> None:
    msg = datetime.now().strftime('[%d/%m/%Y %H:%M:%S] ') + msg

    print(msg)

    with open(LOG_FILE, "a", encoding='utf-8') as file:
        file.write(msg)

# HEAD
# h0 – Tipo de mensagem
# h1 – Se tipo for handshake: número do servidor, se não 0
# h2 - 0
# h3 – Número total de pacotes do arquivo
# h4 – Número do pacote sendo enviado
# h5 – Se tipo for handshake: id do arquivo (crie um para cada arquivo). Se tipo for dados: tamanho do payload.
# h6 – Pacote solicitado para recomeço quando a erro no envio
# h7 – Ùltimo pacote recebido com sucesso
# h8h9 – CRC (Por ora deixe em branco. Fará parte do projeto 5).
# Payload 0 - 114 Bytes, the packet data.
# End of packet 4 Bytes (0xAA 0xBB 0xCC 0xDD)


PACKET_END = b'\xAA\xBB\xCC\xDD'

HANDSHAKE = b'\x01'     # Type 01 (Handshake)
SERVER_LIVRE = b'\x02'  # Type 02 (Handshake response)
DATA = b'\x03'          # Type 03 (Data)
VALIDATION = b'\x04'    # Type 04 (Validation)
TIMEOUT = b'\x05'       # Type 05 (Timeout)
ERROR = b'\x06'         # Type 06 (Error)

SERVER_ID = b'\x40'     # Server ID (64)

IDLE_PACKET = SERVER_LIVRE + b'\x00' + b'\x00' + b'\x01' + b'\x01' + \
    int(0).to_bytes(length=5, byteorder='big') + PACKET_END

TIMEOUT_PACKET = TIMEOUT + b'\x00' + b'\x00' + b'\x01' + b'\x01' + \
    int(0).to_bytes(length=5, byteorder='big') + PACKET_END


def handshake_confirmation(com: enlace) -> tuple[int, int]:
    # Wait for client to send handshake

    log("Waiting for handshake packet...")

    handshake = com.getData(10)

    # Reads the handshake packet
    type = int.from_bytes(handshake[0], byteorder='big')
    serverId = int.from_bytes(handshake[1], byteorder='big')
    totalPackets = int.from_bytes(handshake[3], byteorder='big')
    packetId = int.from_bytes(handshake[4], byteorder='big')
    archiveId = int.from_bytes(handshake[5], byteorder='big')

    end = com.getData(3)
    com.rx.clearBuffer()

    log("Packet received.")

    if type == HANDSHAKE and end == PACKET_END:
        log("Handshake packet received.")

        # Check if the handshake is valid and for this server
        if serverId == SERVER_ID and packetId == 0:
            log("Handshake packet is valid.")

            # Send handshake confirmation
            time.sleep(1)
            com.sendData(IDLE_PACKET)

            return archiveId, totalPackets
        else:
            log(f'Handshake for server {serverId}, received, ignoring...')

    return -1, -1


def getNextData(com: enlace, expected: int, counter: int, head: bytes) -> bytes:
    type = int.from_bytes(head[0], byteorder='big')
    total = int.from_bytes(head[3], byteorder='big')
    packetNumber = int.from_bytes(head[4], byteorder='big')
    payloadSize = int.from_bytes(head[5], byteorder='big')
    lastValid = int.from_bytes(head[7], byteorder='big')

    if type == DATA:
        if total == expected:
            if lastValid == counter and packetNumber == counter + 1:
                log(f"Packet {packetNumber} of {total} received.")

                payload = com.getData(payloadSize)

                end = com.getData(4)

                if end == PACKET_END:
                    log(f"Packet {packetNumber} of {total} is valid.")
                    return payload

                else:
                    log(f"Packet {packetNumber} of {total} is not valid, end of packet is not valid.")
                    com.rx.clearBuffer()

            else:
                log(
                    f"Invalid packet, expected packet number {counter + 1}, but received {packetNumber}.")
                com.rx.clearBuffer()

        else:
            log(f"Invalid packet, expected {expected} packets, received {total}.")
            com.rx.clearBuffer()

    else:
        log(f"Invalid packet type {type} recived, ignoring...")
        com.rx.clearBuffer()

    return None


def main():
    try:
        # Ativa comunicacao. Inicia os threads e a comunicação seiral
        com = enlace(SERIAL_PORT_NAME)
        com.enable()

        archiveId = -1

        # Wait for handshake confirmation
        while archiveId < 0:
            archiveId, totalPackets = handshake_confirmation(com)

        data = b''

        packetCounter = 0
        timer = 0

        while packetCounter < totalPackets:
            while com.rx.getBufferLen() < 14:
                time.sleep(1)
                timer += 1

                if timer % 2 == 0 and timer < 20:
                    log("Reenviando pacote de confirmação.")

                    validation_packet = VALIDATION + b'\x00' + b'\x00' + b'\x01' + b'\x01' + \
                        b'\x00' + b'\x00' + packetCounter.to_bytes(length=1, byteorder='big') + \
                        int(0).to_bytes(length=2, byteorder='big') + PACKET_END

                    com.sendData(validation_packet)

            if timer >= 20:
                log("Time out, sending timeout packet.")

                com.sendData(TIMEOUT_PACKET)

                com.disable()
                print("Conexão encerrada.")
                return

            timer = 0

            nextData = getNextData(
                com, totalPackets, packetCounter, com.getData(10))

            if nextData is not None:
                data += nextData
                packetCounter += 1

                log(
                    f"Sending validation for packet {packetCounter} of {totalPackets}.")

                validation_packet = VALIDATION + b'\x00' + b'\x00' + b'\x01' + b'\x01' + \
                    b'\x00' + b'\x00' + packetCounter.to_bytes(length=1, byteorder='big') + \
                    int(0).to_bytes(length=2, byteorder='big') + PACKET_END

                com.sendData(validation_packet)

            else:
                log(f"Sending error for packet {packetCounter + 1} of {totalPackets}.")

                error_packet = ERROR + b'\x00' + b'\x00' + b'\x01' + b'\x01' + \
                    b'\x00' + (packetCounter + 1).to_bytes(length=1, byteorder='big') + \
                    packetCounter.to_bytes(length=1, byteorder='big') + \
                    int(0).to_bytes(length=2, byteorder='big') + PACKET_END

                com.sendData(error_packet)

        log(f"Writting file with {len(data)} bytes.")

        match archiveId:
            case 1:
                extention = ".txt"
            case 2:
                extention = ".png"
            case 3:
                extention = ".jpg"
            case 4:
                extention = ".zip"
            case 5:
                extention = ".mp3"
            case 6:
                extention = ".mp4"
            case 7:
                extention = ".pdf"
            case 8:
                extention = ".docx"
            case 9:
                extention = ".pptx"
            case 10:
                extention = ".xlsx"

        with open("data/recived" + extention, "wb") as file:
            file.write(data)

        log("File written.")

        # Encerra comunicação
        log("-------------------------")
        log("Comunication ended.")
        log("-------------------------")
        com.disable()

    except Exception as e:
        log("Error ->", e)
        com.disable()

    # so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    main()