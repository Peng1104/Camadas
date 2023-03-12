from enlace import enlace
from logFile import logFile
from os.path import isfile
from constantes import *
import time

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

# use uma das 3 opcoes para atribuir à variável a porta usada
SERIAL_PORT_NAME = "/dev/ttyACM0"            # Ubuntu (variacao de)
# SERIAL_PORT_NAME = "/dev/tty.usbmodem1411"   # Mac    (variacao de)
# SERIAL_PORT_NAME = "COM3"                    # Windows(variacao de)

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

LOG_FILE = logFile(__file__)


def log(msg: str) -> None:
    LOG_FILE.log(msg)


HANDSHAKE_START = HANDSHAKE + \
    SERVER_ID.to_bytes(length=1, byteorder='big') + b'\x00' + b'\x01' + b'\x01'

HANDSHAKE_END = int(0).to_bytes(length=4, byteorder='big') + PACKET_END


def get_extension_id(extension: str) -> int:
    match extension:
        case "txt":
            return 1
        case "png":
            return 2
        case "jpg":
            return 3
        case "zip":
            return 4
        case "mp3":
            return 5
        case "mp4":
            return 6
        case "pdf":
            return 7
        case "docx":
            return 8
        case "pptx":
            return 9
        case "xlsx":
            return 10
        case _:
            return -1


def sendHandshake(com: enlace, file_path: str) -> bool:
    com.log(f"Sending handshake... for file {file_path}")

    extension = file_path.split('.')[-1]

    extensionID = get_extension_id(extension)

    if extensionID == -1:
        com.log(f"Error: Invalid file extension, {extension}")

        if input("Tentar novamente? (S/N)").lower() == 's':
            return sendHandshake(com, file_path)

        com.disable()
        log("Conexão encerrada.")
        return False

    com.sendData(HANDSHAKE_START +
                 extensionID.to_bytes(length=1, byteorder='big') + HANDSHAKE_END)

    com.log("Waiting response...")

    head, payload, end = com.readPacket()

    if head is None:
        com.log("Server is not responding. Try again? (S/N)")

        if input().lower() == 's':
            return sendHandshake(com, file_path)

        com.disable()
        return False

    type = head[0].to_bytes(length=1, byteorder='big')
    totalPackets = head[3]
    packetId = head[4]

    com.clearBuffer()

    if type == SERVER_LIVRE and totalPackets == 1 and packetId == 1 and end == PACKET_END:
        com.log("Server idle, ready to receive file.")
        return True

    com.log("Erro no handshake. Tentar novamente? (S/N)")

    if input().lower() == 's':
        return sendHandshake(com, file_path)

    com.disable()
    return False


def sendPacket(packet: bytes, com: enlace, counter: int, total: int):
    com.log(f"Sending packet {counter} of {total}")

    com.sendData(packet)  # Envia o pacote
    time.sleep(1.5)  # 1.5s para o servidor processar o pacote

    head, payload, end = com.readPacket()

    if head is None:
        return None

    type = head[0].to_bytes(length=1, byteorder='big')
    total = head[3]
    packetId = head[4]
    expected_counter = head[6]
    last_valid = head[7]

    if end != PACKET_END or packetId != 1 or total != 1:
        com.log("INVALID PACKET END")
        com.clearBuffer()
        return False

    if type == VALIDATION and last_valid == counter:
        com.log(f"Packet {counter} sent successfully")
        return True

    if type == TIMEOUT:
        com.log("Receiving timeout from server.")
        com.disable()
        return None

    if type == ERROR:
        com.log(
            f"Error, expected packet number: {expected_counter}, last valid packet: {last_valid}")
        return last_valid

    else:
        com.log("Invalid packet")
        com.clearBuffer()

    return False


def main():
    try:
        # Ativa comunicacao. Inicia os threads e a comunicação seiral

        log("Escolha um arquivo para enviar...")
        file = input("Arquivo: ")
        log(f"Arquivo escolhido: {file}")

        if not isfile(file):
            log("Arquivo não encontrado.")
            return

        com = enlace(LOG_FILE, SERIAL_PORT_NAME)

        with open(file, "rb") as f:
            data = f.read()

        total = len(data) // 114 + 1

        if not sendHandshake(com, file, total):
            return

        log("Data creation start")

        packets = []

        while len(data) > 114:
            payload = data[:114]
            data = data[114:]

            head = DATA + b'\x00' + b'\x00' + total.to_bytes(length=1, byteorder='big') + (len(packets) + 1).to_bytes(
                length=1, byteorder='big') + int(len(payload)).to_bytes(length=1, byteorder='big') + int(0).to_bytes(length=4, byteorder='big')

            packets.append(head + payload + PACKET_END)

        head = DATA + b'\x00' + b'\x00' + total.to_bytes(length=1, byteorder='big') + (len(packets) + 1).to_bytes(
            length=1, byteorder='big') + int(len(data)).to_bytes(length=1, byteorder='big') + int(0).to_bytes(length=4, byteorder='big')

        packets.append(head + data + PACKET_END)

        log(f"Data processing finished, to be send {len(packets)} packets")

        log("Sending data...")

        counter = 0
        total = len(packets)

        while counter < total:
            result = sendPacket(packets[counter], com, counter+1, total)

            if result is None:
                return

            if type(result) == int:
                counter = result

            elif result:
                counter += 1

        # A camada enlace possui uma camada inferior, TX possui um método para conhecermos o status da transmissão
        # O método não deve estar fincionando quando usado como abaixo. deve estar retornando zero. Tente entender como esse método funciona e faça-o funcionar.
        # print(f"Payload sended, {com.tx.getStatus()} bytes sended.")

        log("Todos os pacotes foram enviados com sucesso.")

        # Encerra comunicação
        log("-------------------------")
        log("Comunicação encerrada")
        log("-------------------------")
        com.disable()

    except Exception as e:
        log("Error ->")
        print(e)
        com.disable()

    # so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    main()
