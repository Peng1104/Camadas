from enlace import enlace
from logFile import logFile
from time import sleep
from constantes import *
from os.path import isfile
from crc import Crc16, Calculator

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

# use uma das 3 opcoes para atribuir à variável a porta usada
SERIAL_PORT_NAME = "/dev/ttyACM0"            # Ubuntu (variacao de)
# SERIAL_PORT_NAME = "/dev/tty.usbmodem1411"   # Mac    (variacao de)
# SERIAL_PORT_NAME = "COM5"

# The handshake packet, concatenate with the archive id to send
HANDSHAKE_START = HANDSHAKE.to_bytes(length=1, byteorder='big') + \
    SERVER_ID.to_bytes(length=1, byteorder='big') + b'\x00' + b'\x01' + b'\x01'

# The end of the handshake packet
HANDSHAKE_END = bytes(4) + PACKET_END

class Cliente():

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
            crc = self.calcuateChecksum16(payload)

            head = DATA + b'\x00' + b'\x00' + total.to_bytes(length=1, byteorder='big') + (len(packets) + 1).to_bytes(
                length=1, byteorder='big') + int(len(payload)).to_bytes(length=1, byteorder='big') + int(0).to_bytes(length=2, byteorder='big') + crc

            packets.append(head + payload + PACKET_END)

        crc = self.calcuateChecksum16(data)

        head = DATA + b'\x00' + b'\x00' + total.to_bytes(length=1, byteorder='big') + (len(packets) + 1).to_bytes(
            length=1, byteorder='big') + int(len(data)).to_bytes(length=1, byteorder='big') + int(0).to_bytes(length=2, byteorder='big') + crc
        
        packets.append(head + data + PACKET_END)

        self.log(f"Data processing finished, to be send {len(packets)} packets")

        self.sendData(packets)

    def calcuateChecksum16(self, payload: bytes) -> bytes:
        calculator = Calculator(Crc16.CCITT, optimized=True)
        return calculator.checksum(payload).to_bytes(length=2, byteorder='big')  
    
    def sendPacket(self, packet: bytes, counter: int, total: int) -> bool:
        self.log(f"Sending packet {counter} of {total}")

        self.com.sendPacket(packet)  # Envia o pacote
        sleep(1.5)  # 1.5s para o servidor processar o pacote

        head, _, end = self.com.recivePacket()

        if head is None:
            return None

        type = head[0].to_bytes(length=1, byteorder='big')
        total = head[3]
        packetId = head[4]
        expected_counter = head[6]
        last_valid = head[7]

        if end != PACKET_END or packetId != 1 or total != 1:
            self.log("INVALID PACKET END")
            self.com.clearBuffer()
            return False

        if type == VALIDATION and last_valid == counter:
            self.log(f"Packet {counter} sent successfully")
            return True

        if type == TIMEOUT:
            self.log("Receiving timeout from server.")
            self.com.disable()
            return None

        if type == ERROR:
            self.log(
                f"Error, expected packet number: {expected_counter}, last valid packet: {last_valid}")
            return last_valid

        else:
            self.log("Invalid packet")
            self.com.clearBuffer()

        return False
    
    def sendData(self, packets) -> None:
        self.log("Sending data...")
        counter = 0
        while counter < len(packets):
            result = self.sendPacket(packets[counter], counter+1, len(packets))

            if result is None:
                self.log("-------------------------")
                self.log("Comunicação encerrada")
                self.log("-------------------------")
                self.com.disable()
                return

            if type(result) == int:
                counter = result

            elif result:
                counter += 1
        
        # A camada enlace possui uma camada inferior, TX possui um método para conhecermos o status da transmissão
        # O método não deve estar fincionando quando usado como abaixo. deve estar retornando zero. Tente entender como esse método funciona e faça-o funcionar.
        # print(f"Payload sended, {com.tx.getStatus()} bytes sended.")

        self.log("Todos os pacotes foram enviados com sucesso.")

        # Encerra comunicação
        self.log("-------------------------")
        self.log("Comunicação encerrada")
        self.log("-------------------------")
        self.com.disable()
    
    def is_alive(self) -> bool:
        return self.com.isEnabled()

if __name__ == "__main__":
    client_obj = Cliente(SERIAL_PORT_NAME)

    while client_obj.is_alive():
        client_obj.chooseFile()
