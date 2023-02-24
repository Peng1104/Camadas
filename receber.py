from enlace import enlace
import time

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

# use uma das 3 opcoes para atribuir à variável a porta usada
SERIAL_PORT_NAME = "/dev/ttyACM1"            # Ubuntu (variacao de)
# SERIAL_PORT_NAME = "/dev/tty.usbmodem1411"   # Mac    (variacao de)
#SERIAL_PORT_NAME = "COM5"                    # Windows(variacao de)

# HEAD format PayloadSize 2 Byte + 5 Byte PacketNumber + 5 Bytes TotalPackets
# Payload 0 - 50 Bytes, the packet data.
# # End of packet 3 Bytes (0xDD 0xEE 0xFF)

PACKET_END = b'\xDD\xEE\xFF'

HANDSHAKE = int(0).to_bytes(length=2, byteorder='big') + int(0).to_bytes(
    length=5, byteorder='big') + int(0).to_bytes(length=5, byteorder='big') + PACKET_END

CONFIRMATION_PACKET= int(0).to_bytes(length=2, byteorder='big') + int(1).to_bytes(
    length=5, byteorder='big') + int(1).to_bytes(length=5, byteorder='big') + PACKET_END

def confirmHandshake(com: enlace) -> bool:
    # Wait for client to send handshake

    print("Waiting for handshake...") # DEBUG

    handshake, _ = com.getData(12)

    print("Handshake received.") # DEBUG

    # Reads the handshake packet
    payloadSize = int.from_bytes(handshake[:1], byteorder='big')
    totalPackets = int.from_bytes(handshake[2:6], byteorder='big')
    packetNumber = int.from_bytes(handshake[7:], byteorder='big')

    end, _ = com.getData(3)
    com.rx.clearBuffer()

    # Checks if the handshake is valid
    if payloadSize == 0 and packetNumber == 0 and totalPackets == 0 and end == PACKET_END:
        print("Handshake received is valid.")
        # Send handshake confirmation
        com.sendData(HANDSHAKE)
        return True
    return False

def validatePacket(com: enlace, packetNumber: int, data: list) -> bool:

    # Checks if the packet is not valid
    if len(data) + 1 != packetNumber:
        print(f"Packet {packetNumber} is not valid.")

        payload = packetNumber.to_bytes(length=5, byteorder='big')

        # Send error packet to client
        com.sendData(len(payload).to_bytes(length=2, byteorder='big') + int(1).to_bytes(
            length=5, byteorder='big') + int(1).to_bytes(length=5, byteorder='big') + payload + PACKET_END)

        return False
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

        head, _ = com.getData(12)  #Wait for packet head

        # Reads the head
        payloadSize = int.from_bytes(head[:1], byteorder='big')
        totalPackets = int.from_bytes(head[2:6], byteorder='big')
        recivedPacketNumber = int.from_bytes(head[7:], byteorder='big')           #Must read the first packet to get it

        # Reads payload data

        data = []

        payload, _ = com.getData(payloadSize)

        if not validatePacket(com, recivedPacketNumber, data):
            return

        data.append(payload)

        while len(data) <= totalPackets:
            print(f"Reading {len(data) + 1} of {totalPackets}.") # DEBUG

            payloadSize = int.from_bytes(head[:1], byteorder='big') 
            recivedPacketNumber = int.from_bytes(head[2:6], byteorder='big') 
            totalPackets = int.from_bytes(head[7:], byteorder='big') 

            payload, _ = com.getData(payloadSize)

            if not validatePacket(com, recivedPacketNumber, data):
                return

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
