from enlace import enlace
from logFile import logFile
from constantes import *
import time

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

# use uma das 3 opcoes para atribuir à variável a porta usada
SERIAL_PORT_NAME = "/dev/ttyACM1"            # Ubuntu (variacao de)
# SERIAL_PORT_NAME = "/dev/tty.usbmodem1411"   # Mac    (variacao de)
# SERIAL_PORT_NAME = "COM5"                    # Windows(variacao de)

LOG_FILE = logFile(__file__)


def log(msg: str) -> None:
    LOG_FILE.log(msg)

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


def handshake_confirmation(com: enlace) -> tuple[int, int]:
    # Wait for client to send handshake

    log("Waiting for handshake packet...")

    handshake = com.getData(10)

    # Reads the handshake packet
    type = handshake[0].to_bytes(length=1, byteorder='big')
    serverId = handshake[1]
    totalPackets = handshake[3]
    packetId = handshake[4]
    archiveId = handshake[5]

    end = com.getData(4)
    com.rx.clearBuffer()

    log("Packet received.")

    if type == HANDSHAKE and end == PACKET_END:
        log("Handshake packet received.")

        # Check if the handshake is valid and for this server
        if serverId == SERVER_ID and packetId == 1:
            log("Handshake packet is valid.")

            # Send handshake confirmation
            time.sleep(1)
            com.sendPacket(IDLE_PACKET)

            return archiveId, totalPackets
        else:
            log(f'Handshake for server {serverId}, received, ignoring...')

    return -1, -1


def getNextData(com: enlace, expected: int, counter: int, head: bytes) -> bytes:
    type = head[0].to_bytes(length=1, byteorder='big')
    total = head[3]
    packetNumber = head[4]
    payloadSize = head[5]

    if type == DATA:
        if total == expected:
            if packetNumber == counter + 1:
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

        archiveId = -1

        # Wait for handshake confirmation
        while archiveId < 0:
            archiveId, totalPackets = handshake_confirmation(com)

        data = b''

        packetCounter = 0
        timer = 0

        while packetCounter < totalPackets:
            while com.rx.getBufferLen() < 14:
                time.sleep(0.5)
                timer += 0.5

                if timer % 2 == 0 and timer < 20:
                    log(
                        f"Reenviando pacote de confirmação para o pacote {packetCounter}")

                    validation_packet = VALIDATION + b'\x00' + b'\x00' + b'\x01' + b'\x01' + \
                        b'\x00' + b'\x00' + packetCounter.to_bytes(length=1, byteorder='big') + \
                        int(0).to_bytes(length=2, byteorder='big') + PACKET_END

                    com.sendPacket(validation_packet)

            if timer >= 20:
                log("Time out, sending timeout packet.")

                com.sendPacket(TIMEOUT_PACKET)

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
                
                com.sendPacket(validation_packet)

            else:
                log(f"Sending error for packet {packetCounter + 1} of {totalPackets}.")

                error_packet = ERROR + b'\x00' + b'\x00' + b'\x01' + b'\x01' + \
                    b'\x00' + (packetCounter + 1).to_bytes(length=1, byteorder='big') + \
                    packetCounter.to_bytes(length=1, byteorder='big') + \
                    int(0).to_bytes(length=2, byteorder='big') + PACKET_END

                com.sendPacket(error_packet)

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
        print("Error ->", e)
        com.disable()


    # so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    main()
