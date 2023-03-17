from enlace import enlace
from logFile import logFile
from time import sleep
from constantes import *
from crc import Crc16, Calculator

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

# use uma das 3 opcoes para atribuir à variável a porta usada
SERIAL_PORT_NAME = "/dev/ttyACM1"            # Ubuntu (variacao de)
# SERIAL_PORT_NAME = "/dev/tty.usbmodem1411"   # Mac    (variacao de)
# SERIAL_PORT_NAME = "COM5"


class Server():

    def __init__(self, serial_port_name: str) -> None:
        self.com = enlace(logFile("Server", False), serial_port_name)

    def log(self, message: str) -> None:
        self.com.log(message)

    def idle(self) -> None:
        self.log("Waiting for handshake packet...")

        handshake, _, end = self.com.recivePacket(False)

        # No handshake received
        if handshake is None:
            return

        self.com.clearBuffer()

        if end != PACKET_END:
            self.log(f"Invalid packet, eof is {end}, ignoring...")
            return

        type = handshake[0].to_bytes(length=1, byteorder='big')

        if type != HANDSHAKE:
            self.log(f"Received {type}, ignoring...")
            return

        total = handshake[3]
        packetId = handshake[4]

        # Not a handshake packet
        if packetId != 1 or total != 1:
            self.log("Invalid handshake packet, ignoring...")
            return

        serverId = handshake[1]

        # Check if the handshake is valid and for this server
        if serverId == SERVER_ID:
            archiveId = handshake[5]

            self.log(
                f"Received handshake for {archiveId}, sending confirmation...")

            sleep(1)

            self.com.sendPacket(IDLE_PACKET)
            self.recive_data(archiveId)

        else:
            self.log(
                f'Handshake for server {serverId}, received, ignoring...')

    def recive_data(self, archiveId: int) -> None:
        self.log(f"Waiting for first data packet for {archiveId}...")

        head, payload, end = self.com.recivePacket()

        # TIMEOUT
        if head is None:
            return

        # Corrupted packet
        if end != PACKET_END or not self.isCrcValid(head[8:], payload):
            self.send_error(1, 0)
            return self.recive_data(archiveId)

        type = head[0].to_bytes(length=1, byteorder='big')
        packetId = head[4]
        last = head[7]

        # Validade packet
        if type == DATA and packetId == 1 and last == 0:
            self.log("First data packet received.")
            self.send_validation(1)

            data = payload
            total = head[3]

            next = 2

            while next < total:
                timeout, payload = self.next_data_packet(next, total)

                if timeout:
                    return

                if payload is None:
                    self.send_error(next, next - 1)
                
                else:
                    data += payload
                    self.send_validation(next)
                    next += 1

            # Send validation for last packet
            self.send_validation(next)
            self.log("All packets received.")
            self.write_archive(archiveId, data)

        else:
            self.send_error(1, 0)
            return self.recive_data(archiveId)

    def write_archive(self, archiveId: int, data: bytes) -> None:
        self.log(f"Writting file with {len(data)} bytes.")

        extention = get_extention(archiveId)

        self.log(f"Writing data/recived.{extention}...")

        with open("data/recived." + extention, "wb") as file:
            file.write(data)

        self.log("File written.")

        # Encerra comunicação
        self.log("-------------------------")
        self.log("Comunication ended.")
        self.log("-------------------------")

    def isCrcValid(self, expectedCrc: bytes, payload: bytes) -> bool:
        calculator = Calculator(Crc16.CCITT, optimized=True)
        return calculator.verify(payload, int.from_bytes(expectedCrc, byteorder='big'))

    def next_data_packet(self, next: int, total: int) -> tuple[bool, bytes]:
        self.log(f"Waiting for packet {next} of {total}...")

        head, payload, end = self.com.recivePacket()

        # TIMEOUT
        if head is None:
            return True, None

        # Corrupted packet
        if end != PACKET_END:
            self.log(
                f"Packet {next} is not valid, end of packet is not valid. Expected {PACKET_END}, received {end}.")
            return False, None

        type = head[0].to_bytes(length=1, byteorder='big')

        if type != DATA:
            self.log(f"Invalid packet {type} recived, ignoring...")
            return False, None

        packet_total = head[3]

        if packet_total != total:
            self.log(f"Invalid packet total {packet_total}, expected {total}")
            return False, None

        packetId = head[4]

        if packetId != next:
            self.log(f"Invalid packet id {packetId}, expected {next}")
            return False, None
        
        crc = head[8:]

        if not self.isCrcValid(crc, payload):
            self.log(f"CRC is not valid for packet {packetId}, expected {crc}")
            return False, None
        
        self.log(f"Packet {packetId} of {total} received.")

        return False, payload

    def send_validation(self, packetId: int) -> None:
        self.log(f"Sending validation packet for packet {packetId}...")

        self.com.sendPacket(VALIDATION + b'\x00' + b'\x00' + b'\x01' + b'\x01' + b'\x00' + b'\x00' +
                            packetId.to_bytes(length=1, byteorder='big') +
                            int(0).to_bytes(length=2, byteorder='big') + PACKET_END)

    def send_error(self, packetId: int, last: int) -> None:
        self.com.clearBuffer()

        self.log(
            f"Sending error packet for packet {packetId}, last: {last}...")

        self.com.sendPacket(ERROR + b'\x00' + b'\x00' + b'\x01' + b'\x01' + b'\x00' +
                            packetId.to_bytes(length=1, byteorder='big') +
                            last.to_bytes(length=1, byteorder='big') +
                            int(0).to_bytes(length=2, byteorder='big') + PACKET_END)

    def end(self) -> None:
        self.com.disable()

    def is_alive(self) -> bool:
        return self.com.isEnabled()


if __name__ == "__main__":
    server_obj = Server(SERIAL_PORT_NAME)

    while server_obj.is_alive():
        server_obj.idle()
