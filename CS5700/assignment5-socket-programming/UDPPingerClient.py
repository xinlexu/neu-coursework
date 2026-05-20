import time
from socket import *

server_name = '127.0.0.1'
server_port = 12000

#Create UDP socket
client_socket = socket(AF_INET, SOCK_DGRAM)
client_socket.settimeout(1.0)

#Send 10 pings
for sequence_num in range(1, 11):
    send_time = time.time()
    #Ping sequence_number time
    message = f'Ping {sequence_num} {send_time}'

    try:
        # Send message to server
        client_socket.sendto(message.encode(), (server_name, server_port))

        # Receive response
        response, server_address = client_socket.recvfrom(1024)

        # Calculate RTT
        rtt = time.time() - send_time
        print(f'Reply from {server_name}: {response.decode()} RTT={rtt:.6f} seconds')

    except timeout:
        print('Request timed out')

client_socket.close()