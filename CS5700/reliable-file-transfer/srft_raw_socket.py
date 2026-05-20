import random
import socket
import struct
from dataclasses import dataclass

from srft_packet import SRFTPacket


IP_VERSION = 4
IP_IHL = 5
IP_TOS = 0
IP_TTL = 64
IP_PROTO_UDP = socket.IPPROTO_UDP
IP_HEADER_LEN = 20
UDP_HEADER_LEN = 8


def compute_internet_checksum(data: bytes) -> int:
    if len(data) % 2 == 1:
        data += b"\x00"

    total = 0

    for i in range(0, len(data), 2):
        word = (data[i] << 8) + data[i + 1]
        total += word
        total = (total & 0xFFFF) + (total >> 16)

    return (~total) & 0xFFFF


@dataclass
class IPv4Header:
    source_ip: str
    destination_ip: str
    total_length: int
    identification: int
    ttl: int = IP_TTL
    protocol: int = IP_PROTO_UDP

    def build(self) -> bytes:
        version_ihl = (IP_VERSION << 4) | IP_IHL
        flags_fragment_offset = 0
        header_checksum = 0

        header_without_checksum = struct.pack(
            "!BBHHHBBH4s4s",
            version_ihl,
            IP_TOS,
            self.total_length,
            self.identification,
            flags_fragment_offset,
            self.ttl,
            self.protocol,
            header_checksum,
            socket.inet_aton(self.source_ip),
            socket.inet_aton(self.destination_ip),
        )

        header_checksum = compute_internet_checksum(header_without_checksum)

        return struct.pack(
            "!BBHHHBBH4s4s",
            version_ihl,
            IP_TOS,
            self.total_length,
            self.identification,
            flags_fragment_offset,
            self.ttl,
            self.protocol,
            header_checksum,
            socket.inet_aton(self.source_ip),
            socket.inet_aton(self.destination_ip),
        )


@dataclass
class UDPHeader:
    source_port: int
    destination_port: int
    length: int

    def build(self) -> bytes:
        checksum = 0

        return struct.pack(
            "!HHHH",
            self.source_port,
            self.destination_port,
            self.length,
            checksum,
        )


@dataclass
class ParsedIPv4Header:
    version: int
    ihl: int
    total_length: int
    identification: int
    ttl: int
    protocol: int
    checksum: int
    source_ip: str
    destination_ip: str


@dataclass
class ParsedUDPHeader:
    source_port: int
    destination_port: int
    length: int
    checksum: int


def parse_ipv4_header(packet: bytes) -> ParsedIPv4Header:
    if len(packet) < IP_HEADER_LEN:
        raise ValueError("Packet too short for IPv4 header")

    (
        version_ihl,
        tos,
        total_length,
        identification,
        flags_fragment_offset,
        ttl,
        protocol,
        checksum,
        source_ip,
        destination_ip,
    ) = struct.unpack("!BBHHHBBH4s4s", packet[:IP_HEADER_LEN])

    version = version_ihl >> 4
    ihl = version_ihl & 0x0F

    if version != 4:
        raise ValueError("Not an IPv4 packet")

    if ihl < 5:
        raise ValueError("Invalid IPv4 header length")

    return ParsedIPv4Header(
        version=version,
        ihl=ihl,
        total_length=total_length,
        identification=identification,
        ttl=ttl,
        protocol=protocol,
        checksum=checksum,
        source_ip=socket.inet_ntoa(source_ip),
        destination_ip=socket.inet_ntoa(destination_ip),
    )


def parse_udp_header(packet: bytes, ip_header_length_bytes: int = IP_HEADER_LEN) -> ParsedUDPHeader:
    udp_start = ip_header_length_bytes
    udp_end = udp_start + UDP_HEADER_LEN

    if len(packet) < udp_end:
        raise ValueError("Packet too short for UDP header")

    source_port, destination_port, length, checksum = struct.unpack(
        "!HHHH",
        packet[udp_start:udp_end],
    )

    return ParsedUDPHeader(
        source_port=source_port,
        destination_port=destination_port,
        length=length,
        checksum=checksum,
    )


def extract_udp_payload(packet: bytes, ip_header_length_bytes: int = IP_HEADER_LEN) -> bytes:
    udp_payload_start = ip_header_length_bytes + UDP_HEADER_LEN
    return packet[udp_payload_start:]


def build_ipv4_udp_packet(
    source_ip: str,
    destination_ip: str,
    source_port: int,
    destination_port: int,
    payload: bytes,
    identification: int | None = None,
) -> bytes:
    if identification is None:
        identification = random.randint(0, 65535)

    udp_length = UDP_HEADER_LEN + len(payload)
    udp_header = UDPHeader(
        source_port=source_port,
        destination_port=destination_port,
        length=udp_length,
    ).build()

    total_length = IP_HEADER_LEN + udp_length
    ip_header = IPv4Header(
        source_ip=source_ip,
        destination_ip=destination_ip,
        total_length=total_length,
        identification=identification,
    ).build()

    return ip_header + udp_header + payload


def build_ipv4_udp_srft_packet(
    source_ip: str,
    destination_ip: str,
    source_port: int,
    destination_port: int,
    srft_packet: SRFTPacket,
    identification: int | None = None,
) -> bytes:
    srft_payload = srft_packet.encode_packet()

    return build_ipv4_udp_packet(
        source_ip=source_ip,
        destination_ip=destination_ip,
        source_port=source_port,
        destination_port=destination_port,
        payload=srft_payload,
        identification=identification,
    )


def extract_srft_packet_from_ipv4_udp_packet(
    packet: bytes,
    ip_header_length_bytes: int = IP_HEADER_LEN,
) -> SRFTPacket:
    udp_payload = extract_udp_payload(packet, ip_header_length_bytes)
    return SRFTPacket.decode_packet(udp_payload)



def send_ipv4_udp_packet(
    raw_socket: socket.socket,
    packet: bytes,
    destination_ip: str,
) -> int:
    return raw_socket.sendto(packet, (destination_ip, 0))


def receive_ipv4_udp_packet(
    raw_socket: socket.socket,
    buffer_size: int = 65535,
) -> tuple[bytes, tuple[str, int]]:
    return raw_socket.recvfrom(buffer_size)


if __name__ == "__main__":
    request_packet = SRFTPacket.build_request_packet("test.txt")

    wrapped_packet = build_ipv4_udp_srft_packet(
        source_ip="127.0.0.1",
        destination_ip="127.0.0.1",
        source_port=40000,
        destination_port=50000,
        srft_packet=request_packet,
        identification=12345,
    )

    parsed_ip = parse_ipv4_header(wrapped_packet)
    parsed_udp = parse_udp_header(wrapped_packet)
    extracted_srft_packet = extract_srft_packet_from_ipv4_udp_packet(wrapped_packet)

    print("wrapped_packet_length =", len(wrapped_packet))
    print()

    print("--- parsed ip header ---")
    print(parsed_ip)
    print()

    print("--- parsed udp header ---")
    print(parsed_udp)
    print()

    print("--- extracted srft packet ---")
    print(extracted_srft_packet.summary())