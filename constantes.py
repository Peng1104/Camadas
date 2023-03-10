# The packets types

HANDSHAKE = b'\x01'     # Type 01 (Handshake)
SERVER_LIVRE = b'\x02'  # Type 02 (Handshake response)
DATA = b'\x03'          # Type 03 (Data)
VALIDATION = b'\x04'    # Type 04 (Validation)
TIMEOUT = b'\x05'       # Type 05 (Timeout)
ERROR = b'\x06'         # Type 06 (Error)

# The packet end
PACKET_END = b'\xAA\xBB\xCC\xDD'

# The server ID
SERVER_ID = b'\x40'  # Server ID (64)

# The idle packet, sent when the server is idle and has received a handshake
IDLE_PACKET = SERVER_LIVRE + b'\x00' + b'\x00' + b'\x01' + b'\x01' + \
    int(0).to_bytes(length=5, byteorder='big') + PACKET_END

# The timeout packet
TIMEOUT_PACKET = TIMEOUT + b'\x00' + b'\x00' + b'\x01' + b'\x01' + \
    int(0).to_bytes(length=5, byteorder='big') + PACKET_END
