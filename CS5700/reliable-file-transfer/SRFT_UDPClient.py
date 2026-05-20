import argparse
import socket
import random
import time
import os

from srft_security import SecurityContext
from srft_state_machine import ClientState, CLIENT_STATE_HANDLERS
from srft_packet import SRFTPacket
from srft_config import (
    SRFT_PSK,
    SRFT_SERVER_PORT,
    SRFT_WINDOW_SIZE,
    SRFT_ACK_DELAY_INTERVAL,
)
from srft_socket import SRFTSocket, get_local_ip
from file_manager import ClientFileManager
from datetime import datetime, timedelta

class ClientRunner(): # client is single-threaded, no threading
    def __init__(self, srft_sk: SRFTSocket, filename: str, server_ip_port: tuple, psk: bytes = None) -> None:
        self.srft_sk = srft_sk
        self.server_ip_port = server_ip_port

        self.state = ClientState.CLIENT_INIT
        self.filename = filename
        self.outfile = f"received_{filename}"
        self.file_manager: ClientFileManager | None = None

        self.transfer_success: bool = False
        self.server_sha256: str | None = None
        self.local_sha256: str | None = None
        self.final_verification_passed: bool = False
        
        # really used for carrying the packet from WAIT => PROCESS
        self.pending_pkt: SRFTPacket | None = None  

        self.expected_seq: int = 1
        self.last_in_order: int = 0

        # Flow control
        self.ack_batch_count: int = 0       # 1. ACK when batch_count reaches threshold

        self.receiver_window_size: int = SRFT_WINDOW_SIZE
        self.ack_delay_interval: float = SRFT_ACK_DELAY_INTERVAL # 2. ACK when delay interval is reached
        self.ack_deadline: float | None = None

        self.transmit_started: bool = False
        self.retry_count: int = 0

        self.sec_ctx = SecurityContext(psk=psk or SRFT_PSK)

        # for immediate ACK on out-of-order -> in-order transition
        self.out_of_order: bool = False

        # Security & reporting counters
        self.start_time: float = time.time()
        self.end_time: float = 0.0
        self.security_enabled: bool = True
        self.handshake_success: bool = False
        self.num_packets_received_from_server: int = 0
        self.num_duplicate_packets: int = 0
        self.num_out_of_order_packets: int = 0
        self.num_checksum_error_packets: int = 0
        self.aead_auth_failures: int = 0
        self.replay_drops: int = 0


    def client_report(self) -> None:
        
        file_size = self.file_manager.get_file_size() if self.file_manager is not None else 0
        # Would need to send at least total_chunks + 2 extra(hello & finish)
        report_str =  f"=====================================================================================\n"
        report_str += f"CLIENT REPORT - {datetime.fromtimestamp(self.start_time).strftime('%m/%d/%Y %H:%M:%S')}\n"
        report_str += f"=====================================================================================\n"
        report_str += f"Name of the transferred file:                   {self.filename}\n"
        report_str += f"Security enabled (PSK + AEAD):                  {'Yes' if self.security_enabled else 'No'}\n"
        report_str += f"Handshake status:                               {'Success' if self.handshake_success else 'Fail'}\n"
        if self.handshake_success:
            report_str += f"Size of the transferred file:                   {file_size:,} bytes\n"
            report_str += f"Number of packets received from server:         {self.num_packets_received_from_server:,}\n"
            report_str += f"Number of duplicate packets:                    {self.num_duplicate_packets:,}\n"
            report_str += f"Number of out-of-order packets:                 {self.num_out_of_order_packets:,}\n"
            report_str += f"Number of checksum errors packets:              {self.num_checksum_error_packets:,}\n"
            report_str += f"Time duration of the file transfer:             {str(timedelta(seconds=int(self.end_time - self.start_time)))}\n"
            report_str += f"AEAD authentication failures:                   {self.aead_auth_failures:,}\n"
            report_str += f"Replay drops (duplicate/out-of-window packets): {self.replay_drops}\n"
            report_str += f"SHA-256 match:                                  {self.final_verification_passed}\n"
            if self.transfer_success:
                report_str += f"Received file MD5:                              {self.file_manager.get_md5sum()}\n"
        report_str += f"=====================================================================================\n\n"
        
        # Open report file to write, make directory if not exist
        source_dir = os.path.dirname(os.path.abspath(__file__))
        report_dir = os.path.join(source_dir, f"client_report.txt")

        # Open file for writing binary
        with open(report_dir, "a") as f:
            f.write(report_str)
        
        


    def run(self):
        while not self.state == ClientState.CLIENT_COMPLETE:
            try:
                # try to keep all state transition (change to self.state) within next_state
                CLIENT_STATE_HANDLERS[self.state](self)
            except Exception as e:
                print(f"error in ClientRunner for {self.filename}: {e}")
                break


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SRFT Client - Download files securely over UDP")
    parser.add_argument("filename", help="Name of the file to download from server")
    parser.add_argument("server_ip", help="IP address of the SRFT server")
    parser.add_argument("--psk", type=str, default=None, help="Override PSK (for wrong-PSK testing)")
    args = parser.parse_args()

    psk = args.psk.encode() if args.psk else None

    srft_sk = SRFTSocket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
    srft_sk.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)                 # handle IP header ourselves
    srft_sk.ip = get_local_ip()
    srft_sk.port = random.randint(31337, 65535) # ephemeral high number port for client

    client = ClientRunner(srft_sk, args.filename, (args.server_ip, SRFT_SERVER_PORT), psk=psk)
    try:
        client.run()
    except KeyboardInterrupt:
        pass
    finally:
        srft_sk.close()
