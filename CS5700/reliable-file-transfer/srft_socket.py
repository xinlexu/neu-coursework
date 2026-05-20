import socket

from srft_packet import SRFTPacket
from srft_raw_socket import (
    build_ipv4_udp_srft_packet,
    send_ipv4_udp_packet,
    receive_ipv4_udp_packet,
    parse_ipv4_header,
    parse_udp_header,
    extract_srft_packet_from_ipv4_udp_packet,
)

# For server, since we are sharing the same socket among threads
# - Main thread: should only call recv_one()
# - Handler thread:  should only call send_one()

# For client: no restrictions since it is single-threaded
class SRFTSocket(socket.socket):
    ip: str    # local IP — source IP for outgoing packets; used to filter incoming
    port: int  # local port — source port for outgoing packets; used to filter incoming

    #  __init__, bind and other original socket methods are inherited
    def recv_one(self) -> tuple[SRFTPacket, tuple[str, int]] | None:
        """
        Receive one raw packet and return (SRFTPacket, (src_ip, src_port)) if valid, None otherwise.
        Validates: IPv4/UDP structure, SRFT opcode, payload checksum.
        """
        try:
            raw_bytes, _ = receive_ipv4_udp_packet(self)
        except Exception:
            return None

        try:
            ip_header = parse_ipv4_header(raw_bytes)
        except Exception:
            return None

        if ip_header.protocol != socket.IPPROTO_UDP:
            return None

        if ip_header.destination_ip != self.ip:
            return None

        ip_header_len = ip_header.ihl * 4

        try:
            udp_header = parse_udp_header(raw_bytes, ip_header_len)
        except Exception:
            return None

        if udp_header.destination_port != self.port:
            return None

        try:
            srft_pkt = extract_srft_packet_from_ipv4_udp_packet(raw_bytes, ip_header_len)
        except Exception:
            return None

        src_addr = (ip_header.source_ip, udp_header.source_port)
        
        return srft_pkt, src_addr

    def send_one(self, srft_pkt: SRFTPacket, ip_port: tuple[str, int]) -> int:
        """
        Send one SRFT packet to (dest_ip, dest_port).
        Wraps the packet in a full IPv4/UDP frame using self.ip and self.port as source.
        Returns the number of bytes sent.
        """
        dest_ip, dest_port = ip_port
        raw_packet = build_ipv4_udp_srft_packet(
            source_ip=self.ip,
            destination_ip=dest_ip,
            source_port=self.port,
            destination_port=dest_port,
            srft_packet=srft_pkt,
        )
        return send_ipv4_udp_packet(self, raw_packet, dest_ip)


# Helper function to get our local IP for building network headers
# For server: AWS instance is NATed as well - so network header should not contain the server public IP
def get_local_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("1.1.1.1", 53))
    local_ip = s.getsockname()[0]
    s.close()
    return local_ip
