# HEAD
# h0 – Tipo de mensagem
# h1 – Se tipo for handshake: número do servidor, se não 0
# h2 - 0
# h3 – Número total de pacotes do arquivo
# h4 – Número do pacote sendo enviado
# h5 – Se tipo for handshake: id do arquivo (crie um para cada arquivo).
# Se tipo for dados: tamanho do payload.
#
# h6 – Pacote solicitado para recomeço quando a erro no envio
# h7 – Ùltimo pacote recebido com sucesso
# h8h9 – CRC (Por ora deixe em branco. Fará parte do projeto 5).
# Payload 0 - 114 Bytes, the packet data.
# End of packet 4 Bytes (0xAA 0xBB 0xCC 0xDD)

# The time to wait between buffer checks, in seconds
CHECK_DELAY = 0.5

# The server ID
SERVER_ID = 64  # Server ID (64)

# Packet Sructure

# The packet end
PACKET_END = b'\xAA\xBB\xCC\xDD'

# Header size
HEAD_SIZE = 10

# The packet end size
END_SIZE = len(PACKET_END)

# The minimum packet size
MIN_PACKET_SIZE = HEAD_SIZE + END_SIZE

# The packets types

HANDSHAKE = b'\x01'     # Type 01 (Handshake)
SERVER_LIVRE = b'\x02'  # Type 02 (Handshake response)
DATA = b'\x03'          # Type 03 (Data)
VALIDATION = b'\x04'    # Type 04 (Validation)
TIMEOUT = b'\x05'       # Type 05 (Timeout)
ERROR = b'\x06'         # Type 06 (Error)

# Fixed packets

# The idle packet, send when the server is idle and has received a handshake
IDLE_PACKET = SERVER_LIVRE + b'\x00' + b'\x00' + b'\x01' + b'\x01' + \
    int(0).to_bytes(length=5, byteorder='big') + PACKET_END

# The timeout packet, send when the last received packet was over 20 seconds ago
TIMEOUT_PACKET = TIMEOUT + b'\x00' + b'\x00' + b'\x01' + b'\x01' + \
    int(0).to_bytes(length=5, byteorder='big') + PACKET_END
