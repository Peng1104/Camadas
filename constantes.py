# CRC
from crc import Calculator, Crc16

# voce deverá descomentar e configurar a porta com através da qual ira fazer comunicaçao
#   para saber a sua porta, execute no terminal :
#   python -m serial.tools.list_ports
# se estiver usando windows, o gerenciador de dispositivos informa a porta

# The time to wait between buffer checks, in seconds
CHECK_DELAY = 0.5

# Retry sending the packet again in seconds, server side
SERVER_RETRY_DELAY = 5*60 

# The max amount of time to wait for a packet, if not received a timeout packet is sent, in seconds
TIMEOUT_TIME = 20

# The server ID
SERVER_ID = 64  # 0x40

# HEAD
# h0 – Tipo de mensagem
# h1 – Server / Client ID (para quem é o pacote)
# h2 - Handshake/Data -> ID do cliente que está enviando o pacote, else 0x00
# h3 – Handshake/Data -> Número total de pacotes do arquivo, else 0x01
# h4 – Número do pacote sendo enviado, Handshake -> 0x00
# h5 – Handshake -> archiveID, Dada -> payload size, else 0x00
# h6 – Error -> Qual pacote que deu erro, else 0x00
# h7 – Ùltimo pacote recebido com sucesso, else 0x00
# h8h9 – CRC do payload, else 0x0000

HEAD_SIZE = 10

MAX_PAYLOAD_SIZE = 114

# The packet end
PACKET_END = b'\xAA\xBB\xCC\xDD'

END_SIZE = len(PACKET_END)

MIN_PACKET_SIZE = HEAD_SIZE + END_SIZE

# The CRC calculator
CALCULATOR = Calculator(Crc16.CCITT, optimized=True)

# The packets types

HANDSHAKE = b'\x01'     # Type 01 (Handshake)
SERVER_LIVRE = b'\x02'  # Type 02 (Handshake response)
DATA = b'\x03'          # Type 03 (Data)
VALIDATION = b'\x04'    # Type 04 (Validation)
TIMEOUT = 5             # Type 05 (Timeout)
ERROR = b'\x06'         # Type 06 (Error)

# Fixed end for informations packtes.
FIXED_END = + b'\x01' + b'\x01' + bytes(5) + PACKET_END

# Extentions to archiveID mapping
__EXTENTIONS = {"txt": 1, "png": 2, "jpg": 3, "zip": 4, "mp3": 5,
                "mp4": 6, "pdf": 7, "docx": 8, "pptx": 9, "xlsx": 10}


def get_archiveId(extention: str) -> int:
    return __EXTENTIONS[extention]


def get_extention(archiveId: int) -> str:
    result = [k for k, v in __EXTENTIONS.items() if v == archiveId]

    if len(result) == 0:
        return None

    return result[0]
