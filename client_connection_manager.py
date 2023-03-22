from server import Server

# Threads
from time import sleep
from threading import Thread, Condition

# Configurations
from constantes import *


class ClientManager():

    def __init__(self, server: Server, clientId: int, amount_of_data_packets: int, arquiveId: int) -> None:
        self.__server = server
        self.__clientId = clientId
        self.__total = amount_of_data_packets
        self.__last_packet = None
        self.__endThread = False
        self.__reset = False
        self.__arquive_type = arquiveId
        self.__data = b''
        self.__next = 1
        self.__timer = Condition()

        thread = Thread(target=self.timer, args=(),
                        name=f"Timer for client {clientId}")
        thread.start()

    def log(self, msg: str) -> None:
        self.__server.log(f"[Client {self.__clientId}] " + msg)

    def __sendPacket(self, packet: bytes) -> None:
        self.__last_packet = packet
        self.__server.sendPacket(packet)

    def timer(self) -> None:
        counter = 0

        while not self.__endThread:
            self.__timer.wait(SERVER_RETRY_DELAY)

            if self.__reset:
                counter = 0
            else:
                counter += 1

            if counter * SERVER_RETRY_DELAY >= TIMEOUT_TIME:
                self.__endThread = True

                self.log("Sending connection timeout packet...")
                self.__sendPacket(
                    TIMEOUT + self.__clientId.to_bytes(1, 'big')
                    + self.__server.id.to_bytes(1, 'big') + FIXED_END)

                del self.__server.managers[self.__clientId]

            elif counter > 0:
                self.log(f"Seding last packet again ({counter})...")
                self.__sendPacket(self.__last_packet)

    def __update(self, sucess: bool) -> None:
        if sucess:
            self.__send_validation()
            self.__next += 1
        else:
            self.__send_error()

        completed = self.__next == self.__total

        if completed:
            self.__endThread = True

        self.__timer.notify()
        sleep(0.5)
        self.__reset = False

        if completed:
            self.__write()

    def handle_packet(self, head: bytes, payload: bytes) -> None:
        self.__reset = True

        # Check if packet type is data
        if head[0].to_bytes(1, 'big') != DATA:
            self.log(
                f"Recived packet {head[0]}, ignoring...")

            return self.__update(False)

        packetId = head[4]

        if packetId != next:
            self.log(
                f"Recived packet {packetId}, but expected is {self.__next}.")

            return self.__update(False)

        total = head[3]

        if total != self.__total:
            self.log(
                f"Packet total from packet {packetId} is invalid.")
            self.log(f"Expected {self.__total}, received {total}.")

            return self.__update(False)

        if not CALCULATOR.verify(payload, int.from_bytes(head[8:], 'big')):
            self.log(
                f"Checksum from packet {packetId} is invalid.")
            self.log(
                f"Expected {head[8:]}, received {CALCULATOR.checksum(payload)}.")

            return self.__update(False)

        self.log(
            f"Packet {packetId} of {total} received.")

        self.__data += payload

        return self.__update(True)

    def __send_validation(self) -> None:
        self.log(f"Sending validation packet for packet {self.__next}...")

        self.__sendPacket(VALIDATION + self.__clientId.to_bytes(1, 'big') +
                          self.__server.id.to_bytes(1, 'big') +
                          + b'\x01' + b'\x01' + bytes(2) +
                          self.__next.to_bytes(1, 'big') +
                          bytes(2) + PACKET_END)

    def __send_error(self) -> None:
        self.log(
            f"Sending error packet for packet {self.__next}, last: {self.__next - 1}...")

        self.__sendPacket(ERROR + self.__clientId(1, 'big') +
                          self.__server.id.to_bytes(1, 'big')
                          + b'\x01' + b'\x01' + bytes(1) +
                          self.__next.to_bytes(1, 'big') + (self.__next - 1).to_bytes(1, 'big') +
                          bytes(2) + PACKET_END)

    def __write(self) -> None:
        self.log(f"Writting file with {len(self.__data)} bytes.")

        extention = get_extention(self.__arquive_type)

        self.log(f"Writing data/recived.{extention}...")

        with open(f"data/recived/{self.__clientId}." + extention, "wb") as file:
            file.write(self.__data)

        self.log("File written.")

        self.log("-------------------------")
        self.log("Comunication ended.")
        self.log("-------------------------")

        del self.__server.managers[self.__clientId]
