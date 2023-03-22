# Internal Objects
from enlace import enlace
from logFile import logFile
from client_connection_manager import ClientManager

# Threads
from threading import Thread
from time import sleep

# Configurations
from constantes import *

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

# use uma das 3 opcoes para atribuir à variável a porta usada
SERIAL_PORT_NAME = "/dev/ttyACM1"              # Ubuntu (variacao de)
# SERIAL_PORT_NAME = "/dev/tty.usbmodem1411"   # Mac    (variacao de)
# SERIAL_PORT_NAME = "COM5"

SERVER_RETRY_TIMER = 5  # Retry sending the packet again in seconds


class Server():

    def __init__(self, serial_port_name: str, server_retry_timer: int, serverId: int) -> None:
        self.com = enlace(logFile("Server", False),
                          server_retry_timer, serverId, serial_port_name)

        self.id = serverId

        self.managers = {}

    def log(self, message: str) -> None:
        self.com.log(message)

    def sendPacket(self, packet: bytes) -> None:
        self.com.sendPacket(packet)

    def wating_packet(self) -> None:
        self.log("Waiting for a packet...")

        head, payload, end = self.com.recivePacket(-1)

        if end != PACKET_END:
            self.log(
                f"Recived invalid Packet eof is {end}, expected {PACKET_END}")
            return

        type = head[0].to_bytes(1, 'big')

        if type == HANDSHAKE:
            self.handle_handshake(head)

        else:
            senderId = head[2]
            manager = self.managers[senderId]

            if manager is None:
                self.log(f"Client {senderId} not connected, ignoring...")
                return

            manager.handle_packet(head, payload)

    def handle_handshake(self, handshake: bytes) -> None:
        packetId = handshake[4]

        # Not a handshake packet
        if packetId != 0:
            self.log(
                f"Invalid handshake packet, recived packetId = {packetId} ignoring...")
            return

        clientId = handshake[2]
        amount_of_data_packets = handshake[3]
        archiveId = handshake[5]

        self.log(
            f"Received handshake from client {clientId} for file type {archiveId}, expecting {amount_of_data_packets} of data packets.")

        if self.managers[clientId] is not None:
            self.log(f"Client {clientId} already connected, ignoring...")
            return

        self.managers[clientId] = ClientManager(
            self, clientId, amount_of_data_packets, archiveId)

        sleep(1)

        self.sendPacket(SERVER_LIVRE + clientId.to_bytes(1, 'big') +
                        self.id.to_bytes(1, 'big') + FIXED_END)

    def clearBuffer(self) -> None:
        self.com.clearBuffer()

    def end(self) -> None:
        self.com.disable()

    def is_alive(self) -> bool:
        return self.com.isEnabled()


def server_therad(server: Server) -> None:
    while server.is_alive():
        server.handle_handshake()


if __name__ == "__main__":
    server = Server(SERIAL_PORT_NAME, SERVER_RETRY_TIMER, SERVER_ID)

    thread = Thread(target=server_therad, args=(server), name="Server Thread")
    thread.start()

    command = input("Para parar o servidor escreva stop").lower()

    while command != "stop":
        if command == "clear":
            server.clearBuffer()

        command = input("Para parar o servidor escreva stop").lower()

    server.end()
