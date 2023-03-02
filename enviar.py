from enlace import enlace
import time

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

# use uma das 3 opcoes para atribuir à variável a porta usada
SERIAL_PORT_NAME = "/dev/ttyACM0"            # Ubuntu (variacao de)
# SERIAL_PORT_NAME = "/dev/tty.usbmodem1411"   # Mac    (variacao de)
#SERIAL_PORT_NAME = "COM3"                    # Windows(variacao de)

# HEAD format PayloadSize 2 Byte + 5 Byte TotalPackets + 5 Bytes PacketNumber
# Payload 0 - 50 Bytes, the packet data.
# # End of packet 3 Bytes (0xDD 0xEE 0xFF)

PACKET_END = b'\xDD\xEE\xFF'

HANDSHAKE = int(0).to_bytes(length=2, byteorder='big') + int(0).to_bytes(
    length=5, byteorder='big') + int(0).to_bytes(length=5, byteorder='big') + PACKET_END


def sendHandshake(com: enlace) -> bool:
    com.sendData(HANDSHAKE)

    print("Waiting response...")

    counter = 0

    while com.rx.getIsEmpty() and counter < 11:
        time.sleep(0.5)
        counter += 1

    if counter >= 10:
        print("Servidor Inativo. Tentar novamente? (S/N)")

        if input().lower() == 's':
            return sendHandshake(com)

        com.disable()
        print("Conexão encerrada.")
        return False

    head, _ = com.getData(12)

    payloadSize = int.from_bytes(head[:2], byteorder='big')
    totalPackets = int.from_bytes(head[2:7], byteorder='big')
    packetNumber = int.from_bytes(head[7:], byteorder='big')

    end, _ = com.getData(3)
    com.rx.clearBuffer()

    if payloadSize == 0 and totalPackets == 0 and packetNumber == 0 and end == PACKET_END:
        print("Handshake recebido com sucesso.")
        return True

    print("Erro no handshake. Tentar novamente? (S/N)")

    if input().lower() == 's':
        return sendHandshake(com)

    com.disable()
    print("Conexão encerrada.")
    return False


def sendPacket(packet: bytes, com: enlace, counter: int = 1) -> bool:
    com.sendData(packet)  # Envia o pacote
    time.sleep(0.5)  # 0.5s para o servidor processar o pacote

    response, _ = com.getData(12)  # Recebe a resposta do servidor

    payloadSize = int.from_bytes(response[:1], byteorder='big')

    responsePayload = b''

    if payloadSize > 0:
        responsePayload, _ = com.getData(payloadSize)

    end, _ = com.getData(3)

    if payloadSize == 0 and end == PACKET_END:
        print("Pacote recebido com sucesso.")
        return True

    print(
        f"Pacote rejeitado pelo servidor error code {int.from_bytes(responsePayload, byteorder='big')}. Tentando novamente...")

    if counter < 5:
        return sendPacket(packet, com, counter+1)

    print("Tentativas excedidas. Encerrando conexão.")
    com.disable()
    return False


def main():
    try:
        # Ativa comunicacao. Inicia os threads e a comunicação seiral

        com = enlace(SERIAL_PORT_NAME)
        com.enable()

        if not sendHandshake(com):
            return

        print("Data creation start")

        with open("img/coracao.png", "rb") as file:
            data = file.read()

        total = len(data) // 50 + 1

        packets = []

        while len(data) > 50:
            payload = data[:50]
            data = data[50:]

            head = len(payload).to_bytes(length=2, byteorder='big') + total.to_bytes(
                length=5, byteorder='big') + int(len(packets) + 1).to_bytes(length=5, byteorder='big')

            packets.append(head + payload + PACKET_END)

        head = int(len(data)).to_bytes(length=2, byteorder='big') + total.to_bytes(
            length=5, byteorder='big') + int(len(packets) + 1).to_bytes(length=5, byteorder='big')

        packets.append(head + data + PACKET_END)

        print(f"Data processing finished, to be send {len(packets)} packets")

        print("Sending data...")

        counter = 0

        while len(packets) > 0:
            counter += 1

            # if counter % 10 == 0:
            #     print("Sending fake packe with wrong packet number")
            #     head = int(0).to_bytes(length=2, byteorder='big') + total.to_bytes(
            #         length=5, byteorder='big') + (counter + 1).to_bytes(length=5, byteorder='big')
                
            #     sendPacket(head + PACKET_END, com)

            if counter % 5 == 0:
                print("Sending fake packet with wrong payload length")
                head = int(1).to_bytes(length=2, byteorder='big') + total.to_bytes(
                    length=5, byteorder='big') + (counter + 1).to_bytes(length=5, byteorder='big')
                
                payload = b'\x00\x00\00\x00'

                sendPacket(head + payload + PACKET_END, com)

            if sendPacket(packets.pop(0), com):
                print(
                    f"Packet {total - len(packets)}/{total} sended, {com.tx.getStatus()} bytes.")
            else:
                print(
                    f"Error while sending data, {total - len(packets)} packets sended")
                continue

        # A camada enlace possui uma camada inferior, TX possui um método para conhecermos o status da transmissão
        # O método não deve estar fincionando quando usado como abaixo. deve estar retornando zero. Tente entender como esse método funciona e faça-o funcionar.
        # print(f"Payload sended, {com.tx.getStatus()} bytes sended.")

        print("Todos os pacotes foram enviados com sucesso.")

        # Encerra comunicação
        print("-------------------------")
        print("Comunicação encerrada")
        print("-------------------------")
        com.disable()

    except Exception as e:
        print("Error ->")
        print(e)
        com.disable()

    # so roda o main quando for executado do terminal ... se for chamado dentro de outro modulo nao roda
if __name__ == "__main__":
    main()
