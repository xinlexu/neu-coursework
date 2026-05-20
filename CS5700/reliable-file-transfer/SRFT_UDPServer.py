import argparse
import select
import sys
import threading
import queue
import os
import socket
import time
from srft_security import SecurityContext
from srft_state_machine import ServerState, SERVER_STATE_HANDLERS
from srft_packet import Opcode, SRFTPacket
from srft_config import SRFT_PSK, SRFT_SERVER_PORT
from srft_socket import SRFTSocket, get_local_ip
from file_manager import ServerFileManager
from datetime import timedelta, datetime


# both a Thread and a state machine
class ServerThread(threading.Thread):

    def __init__(self, ip_port: tuple, srft_sk: SRFTSocket, attack_mode: str = None) -> None:
        super().__init__()
        
        self.client_ip, self.client_port = ip_port
        self.sock: SRFTSocket = srft_sk          # write-only for a server thread
        self.in_queue = queue.Queue()   # for receiving packets from the main thread

        # State Machine
        self.state: ServerState = ServerState.SERVER_INIT
        self.transfer_success: bool = False   # we can reach COMPLETE state without success
        self.handshake_success: bool = False

        # File IO
        self.filename: str = ""
        self.file_handle: ServerFileManager | None = None

        # Sender Window (send_base is derived: last_ack + 1)
        # Outstanding packets range = [last_ack + 1 to next_seq_to_send - 1]
        self.next_seq_to_send: int = 1    # next new seq_number that has not been sent yet
        self.last_ack: int = 0            # highest cumulatively acked seq_number

        self.retry_count: int = 0
        self.start_time: float = time.time()
        self.end_time: float = 0.0

        # Stats for server report
        self.num_sent: int = 0
        self.num_recv: int = 0
       
        # Track dup ack count for fast retransmission
        self.dup_ack_count: int | None = None

        # security context
        self.sec_ctx: SecurityContext = SecurityContext(psk=SRFT_PSK)

        # Attack mode (server acts as built-in attack forwarder)
        self.attack_mode: str | None = attack_mode
        self.attack_triggered: bool = False
        self.replay_packet: tuple | None = None

        
    class AbortSignal(Exception): pass
    def abort(self) -> None:
        self.in_queue.put(None) # signal the thread to stop by sending None
        # the state machine should handle file descriptor & other cleanup

    # wrappers around SRFTSocket.send_one and in_queue.recv_one
    # to update stats + prevent misuse of raw socket methods
    def send_one(self, pkt: SRFTPacket, ip_port: tuple) -> int:
        self.num_sent += 1
        return self.sock.send_one(pkt, ip_port)

    def recv_one(self, block: bool = True, timeout: float | None = None) -> SRFTPacket:
        pkt: SRFTPacket = self.in_queue.get(block=block, timeout=timeout)
        if pkt is None:  # abort() sentinel
            raise ServerThread.AbortSignal()
        self.num_recv += 1
        return pkt
    

    def server_report(self) ->None:
        
        file_size = self.file_handle.get_file_size() if self.file_handle is not None else 0
        total_chunks = self.file_handle.get_total_chunks() if self.file_handle is not None else 0
        # Would need to send at least total_chunks + 2 extra(hello & finish)
        min_packet_sent_expected = total_chunks + 2
        report_str =  f"=====================================================================================\n"
        report_str += f"SERVER REPORT - {datetime.fromtimestamp(self.start_time).strftime('%m/%d/%Y %H:%M:%S')}\n"
        report_str += f"=====================================================================================\n"
        if not self.handshake_success:
            report_str += f"Handshake status:                        {'Success' if self.handshake_success else 'Fail'}\n"
        else:
            report_str += f"Name of the transferred file:            {self.filename}\n"
            report_str += f"Size of the transferred file:            {file_size:,} bytes\n"
            report_str += f"Number of packets sent from server:      {self.num_sent:,}\n"
            report_str += f"Number of retransmitted packets:         {max(0, self.num_sent - min_packet_sent_expected):,}\n"
            report_str += f"Number of packets received from client:  {self.num_recv:,}\n"
            report_str += f"Time duration of the file transfer:      {str(timedelta(seconds=int(self.end_time - self.start_time)))}\n"
            report_str += f"Original file MD5:                       {self.file_handle.get_md5sum()}\n"
        report_str += f"=====================================================================================\n\n"
        
        # Open report file to write, make directory if not exist
        source_dir = os.path.dirname(os.path.abspath(__file__))
        report_dir = os.path.join(source_dir, f"server_report.txt")

        # Open file for writing binary
        with open(report_dir, "a") as f:
            f.write(report_str)

    # when run() returns, is_alive() becomes False, gc picks it up
    def run(self):                                                                                   
        while not self.state == ServerState.SERVER_COMPLETE: # loop until complete state                              
            try:
                # try to keep all state transition (change to self.state) within next_state
                # the WAIT would be on srv_thread.in_queue.get(timeout=self.timeout_interval)
                SERVER_STATE_HANDLERS[self.state](self)
            except ServerThread.AbortSignal:
                self.state = ServerState.SERVER_CLEANUP
            except Exception as e:
                print(f"error in ServerThread for {self.client_ip}:{self.client_port}: {e}")
                break # on any error, break the loop and skip cleanup                                                                   

SERVER_GC_FREQ = 0.1 # 100ms, garbage collection for finished/completed ServerThread

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SRFT Server")
    parser.add_argument("--attack", choices=["tamper", "replay", "inject"], default=None, help="Enable attack mode")
    args = parser.parse_args()
    attack_mode = args.attack

    srv_threads = {}
    # this holds ALL ip_port -> ServerThread pairs
    # ip_port = tuple of (ip, port) from the client
    # one (ip, port) = one ServerThread = one state machine

    srft_sk = SRFTSocket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)    # read-only for the main thread
    srft_sk.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)                  # handle IP header ourselves
    srft_sk.ip = get_local_ip()
    srft_sk.port = SRFT_SERVER_PORT

    ServerFileManager.ensure_resources_dir()

    try:
        while True:
            # wake up by either packet arrival or timeout for garbage collection
            pkt_ready, _w, _e  = select.select([srft_sk], [], [], SERVER_GC_FREQ)

            # garbage collect ServerState.SERVER_DONE threads
            for ip_port in list(srv_threads):
                t = srv_threads.get(ip_port)
                if t is not None and t.state == ServerState.SERVER_COMPLETE:
                    del srv_threads[ip_port]

            # handle packet if ready
            srft_pkt, ip_port = None, None
            if pkt_ready:
                recv_result = srft_sk.recv_one()
                if (recv_result is None or not recv_result[0].is_valid()):
                    continue # packet is invalid
                srft_pkt, ip_port = recv_result
            else:
                continue # packet is not ready


            # packet must be valid at this point
            # perform packet forwarding/thread creation
            if srft_pkt.opcode == Opcode.CLIENT_HELLO.value:
                # unlikely: ip_port with existing conn making a new req
                if srv_threads.get(ip_port):
                    # kill the prev conn and reestablish
                    srv_threads.pop(ip_port).abort() # abrupting prompt the thread to close file descriptors and stop

                # create a new thread
                srv_threads[ip_port] = ServerThread(ip_port, srft_sk, attack_mode=attack_mode)
                srv_threads[ip_port].in_queue.put(srft_pkt)
                srv_threads[ip_port].start()

            else: # not a client hello
                if srv_threads.get(ip_port):
                    srv_threads[ip_port].in_queue.put(srft_pkt)
                else:
                    continue    # not a client hello + no current handler = ignore

    except KeyboardInterrupt:
        print("\nServer shutting down...\n")
    finally:
        for t in srv_threads.values():
            t.abort()
        for t in srv_threads.values():
            t.join()
        srft_sk.close()



 
