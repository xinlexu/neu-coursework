
# ================================================================================
# srft configurations shared by the server and client
# ================================================================================

SRFT_SERVER_PORT = 5050
SRFT_WINDOW_SIZE = 128
SRFT_TIMEOUT_INTERVAL = 0.1
SRFT_MAX_RETRIES = 10

# Fast Retransmission configuration
SRFT_DUP_ACK_THRESHOLD = 3

# Client-side ACK configuration
SRFT_ACK_BATCH_THRESHOLD = 32
SRFT_ACK_DELAY_INTERVAL = 0.08

SRFT_PSK = b"CM3HY-26VYW-6JRYC-X66GX-JVY2D-QC986-27D34"