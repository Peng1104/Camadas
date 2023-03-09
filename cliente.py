from enlace import enlace
from datetime import datetime
from zipfile import ZipFile
import os
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

LOG_FILE = os.getcwd() + "/logs/" + os.path.basename(__file__)

if os.path.exists(LOG_FILE + ".log"):
    if os.path.isfile(LOG_FILE + ".log"):
        with open(LOG_FILE + ".log", "r") as file:
            last_line = file.readlines()[-1]

        fileName = last_line.split('] ')[0][1:].replace(
            '/', '-').replace(':', '.') + ".log"

        os.rename(LOG_FILE + ".log", fileName)
        ZipFile(LOG_FILE + ".zip", "a").write(fileName)
        os.remove(fileName)

LOG_FILE += ".log"


def log(msg: str) -> None:
    msg = datetime.now().strftime('[%d/%m/%Y %H:%M:%S] ') + msg

    print(msg)

    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

    with open(LOG_FILE, "a", encoding='utf-8') as file:
        file.write(msg)
        file.write(msg)


PACKET_END = b'\xAA\xBB\xCC\xDD'

HANDSHAKE = b'\x01'     # Type 01 (Handshake)
SERVER_LIVRE = b'\x02'  # Type 02 (Handshake response)
DATA = b'\x03'          # Type 03 (Data)
VALIDATION = b'\x04'    # Type 04 (Validation)
TIMEOUT = b'\x05'       # Type 05 (Timeout)
ERROR = b'\x06'         # Type 06 (Error)

SERVER_ID = b'\x40'     # Server ID (64)

TIMEOUT_PACKET = TIMEOUT + b'\x00' + b'\x00' + b'\x01' + b'\x01' + \
    int(0).to_bytes(length=5, byteorder='big') + PACKET_END

HANDSHAKE_START = HANDSHAKE + SERVER_ID + b'\x00'
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


def sendHandshake(com: enlace, file: str, total: int) -> bool:
    log(f"Sending handshake... for file {file}")

    extension = file.split('.')[-1]

    extensionID = get_extension_id(extension)

    if extensionID == -1:
        log(f"Error: Invalid file extension, {extension}")
        log("Tentar novamente? (S/N)")

        if input().lower() == 's':
            return sendHandshake(com, file, total)

        com.disable()
        log("Conexão encerrada.")
        return False

    com.sendData(HANDSHAKE_START + total.to_bytes(length=1, byteorder='big') + b'\x01'
                 + extensionID.to_bytes(length=1, byteorder='big') + HANDSHAKE_END)

    log("Waiting response...")

    counter = 0

    while com.rx.getIsEmpty() and counter < 11:
        time.sleep(0.5)
        counter += 1

    if counter >= 10:
        log("Servidor Inativo. Tentar novamente? (S/N)")

        if input().lower() == 's':
            return sendHandshake(com, file, total)

        com.disable()
        log("Conexão encerrada.")
        return False

    head = com.getData(10)

    type = head[0].to_bytes(length=1, byteorder='big')
    totalPackets = head[3]
    packetId = head[4]

    end = com.getData(4)
    com.rx.clearBuffer()

    if type == SERVER_LIVRE and totalPackets == 1 and packetId == 1 and end == PACKET_END:
        log("Handshake sent successfully")
        return True

    log("Erro no handshake. Tentar novamente? (S/N)")

    if input().lower() == 's':
        return sendHandshake(com, file, total)

    com.disable()
    log("Conexão encerrada.")
    return False


def sendPacket(packet: bytes, com: enlace, counter: int, total: int) -> bool:
    log(f"Sending packet {counter} of {total}")

    com.sendData(packet)  # Envia o pacote
    time.sleep(1.5)  # 1.5s para o servidor processar o pacote

    timeOutCounter = 0

    while com.rx.getBufferLen() < 14 and timeOutCounter < 5:
        time.sleep(3.5)

        log(f"Resending packet {counter} of {total}")

        com.sendData(packet)
        time.sleep(1.5)

        timeOutCounter += 1

    if timeOutCounter >= 4:
        log("Timeout")
        log("Sending timeout packet")
        com.sendData(TIMEOUT_PACKET)

        log("Ending connection.")
        com.disable()
        return None

    response = com.getData(10)  # Recebe a resposta do servidor

    type = response[0].to_bytes(length=1, byteorder='big')
    total = response[3]
    packetId = response[4]
    expected_counter = response[6]
    last_valid = response[7]

    end = com.getData(4)  # END

    if end != PACKET_END or packetId != 1 or total != 1:
        log("INVALID PACKET END")
        com.rx.clearBuffer()
        return False

    if type == VALIDATION and packetId == counter:
        log("Packet sent successfully")
        return True

    if type == TIMEOUT:
        log("Timeout. Ending connection.")
        com.disable()
        return None

    if type == ERROR:
        log(
            f"Error, expected packet number: {expected_counter}, last valid packet: {last_valid}")
        return last_valid
    
    else:
        log("Invalid packet")
        com.rx.clearBuffer()

    return False


def main():
    try:
        # Ativa comunicacao. Inicia os threads e a comunicação seiral

        log("Escolha um arquivo para enviar:")
        file = input()
        log(f"Arquivo escolhido: {file}")

        if not os.path.isfile(file):
            log("Arquivo não encontrado.")
            return

        com = enlace(SERIAL_PORT_NAME)
        com.enable()

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
