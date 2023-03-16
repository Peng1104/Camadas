from enlace import enlace
from logFile import logFile
from time import sleep
from constantes import *
from os.path import isfile

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

# use uma das 3 opcoes para atribuir à variável a porta usada
SERIAL_PORT_NAME = "/dev/ttyACM0"            # Ubuntu (variacao de)
# SERIAL_PORT_NAME = "/dev/tty.usbmodem1411"   # Mac    (variacao de)
# SERIAL_PORT_NAME = "COM5"

class cliente():

    def __init__(self, serial_port_name: str) -> None:
        self.com = enlace(logFile("Cliente", False), serial_port_name)

    
    def log(self, message : str) -> None:
        self.com.log(message)

    def chooseFile(self) -> None:
        self.log("Escolha um arquivo para enviar...")
        file = input("Arquivo: ")
        self.log(f"Arquivo escolhido: {file}")

        if not isfile(file):
            self.log("Arquivo não encontrado.")
            return
        
        self.sendHandshake(file)

    def sendHandshake(self, file_path: str) -> None:
        self.log(f"Sending handshake... for file {file_path}")
        
        extension = file_path.split('.')[-1]
        archiveId = get_archiveId(extension)

        if archiveId == -1:
            self.log(f"Error: Invalid file extension, {extension}")

            if input("Tentar novamente? (S/N)").lower() == 's':
                return self.chooseFile()

            self.log("-------------------------")
            self.log("Comunication ended.")
            self.log("-------------------------")
            return
        
        self.com.sendPacket(HANDSHAKE_START +
                archiveId.to_bytes(length=1, byteorder='big') + HANDSHAKE_END)
        
        self.log("Waiting response...")

        head, _, end = self.com.recivePacket(False)

        if head is None:
            self.log("Server is not responding. Try again? (S/N)")

            if input().lower() == 's':
                return self.chooseFile()

            self.log("-------------------------")
            self.log("Comunication ended.")
            self.log("-------------------------")
            return

        type = head[0].to_bytes(length=1, byteorder='big')
        totalPackets = head[3]
        packetId = head[4]

        self.com.clearBuffer()

        if type == SERVER_LIVRE and totalPackets == 1 and packetId == 1 and end == PACKET_END:
            self.log("Server idle, ready to receive file.")
            return self.prepareData(file_path)

        self.log("Erro no handshake. Tentar novamente? (S/N)")

        if input().lower() == 's':
            return self.chooseFile()

        self.log("-------------------------")
        self.log("Comunication ended.")
        self.log("-------------------------")
        return


    def prepareData(self, file) -> None:
        with open(file, "rb") as f:
            data = f.read()

        total = len(data) // MAX_PAYLOAD_SIZE + 1

        self.log("Data creation start")

        packets = []

        while len(data) > MAX_PAYLOAD_SIZE:
            payload = data[:MAX_PAYLOAD_SIZE]
            data = data[MAX_PAYLOAD_SIZE:]

            head = DATA + b'\x00' + b'\x00' + total.to_bytes(length=1, byteorder='big') + (len(packets) + 1).to_bytes(
                length=1, byteorder='big') + int(len(payload)).to_bytes(length=1, byteorder='big') + int(0).to_bytes(length=4, byteorder='big')

            packets.append(head + payload + PACKET_END)

        head = DATA + b'\x00' + b'\x00' + total.to_bytes(length=1, byteorder='big') + (len(packets) + 1).to_bytes(
            length=1, byteorder='big') + int(len(data)).to_bytes(length=1, byteorder='big') + int(0).to_bytes(length=4, byteorder='big')

        packets.append(head + data + PACKET_END)

        self.log(f"Data processing finished, to be send {len(packets)} packets")

        self.sendData(packets)

    def sendData(self, packets) -> None:
        pass