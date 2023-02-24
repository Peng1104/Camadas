from enlace import enlace

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

# use uma das 3 opcoes para atribuir à variável a porta usada
SERIAL_PORT_NAME = "/dev/ttyACM0"            # Ubuntu (variacao de)
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

def confirmHandshake(com: enlace)-> bool:
    # Wait for client to send handshake
    handshake, _ = com.getData(12)

    # Reads the handshake packet
    payloadSize = int.to_bytes(handshake[:1])
    packetNumber = int.to_bytes(handshake[2:7])
    totalPackets = int.to_bytes(handshake[8:13])
    end = com.getData(3)
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
    if len(data)+1 != packetNumber:
        print(f"Packet {packetNumber} is not valid.")

        # Send error packet to client
        com.sendData(int(len(packetNumber).to_bytes(byteorder='big')).to_bytes(length=2, byteorder='big') + int(1).to_bytes(
            length=5, byteorder='big') + int(1).to_bytes(length=5, byteorder='big') + packetNumber.to_bytes(byteorder='big')+ PACKET_END)

        return False
    else:
        print(f"Packet {packetNumber} is valid.")

        # Send confirmation packet to client
        com.sendData(CONFIRMATION_PACKET)

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

        head = com.getData(12)  #Wait for packet head

        # Reads the head
        payloadSize = int.to_bytes(head[:1])
        recivedPacketNumber = int.to_bytes(head[2:7])
        totalPackets = int.to_bytes(head[8:13])            #Must read the first packet to get it

        # Reads payload data

        data = b''

        payload = com.getData(payloadSize)

        if not validatePacket(com, recivedPacketNumber, payload):
            return

        data += payload

        while len(data) <= totalPackets:

            payloadSize = int.to_bytes(head[:1])
            recivedPacketNumber = int.to_bytes(head[2:7])
            totalPackets = int.to_bytes(head[8:13])

            payload = com.getData(payloadSize)

            if not validatePacket(com, recivedPacketNumber, payload):
                return

            data += payload

        print("Data received length: ", len(data))

        print("Data received: ", data)

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