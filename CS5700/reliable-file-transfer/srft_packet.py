from enum import IntEnum
import os
from srft_security import SecurityContext
import struct


class Opcode(IntEnum):
    REQUEST = 1
    TRANSMIT = 2
    ACKNOWLEDGE = 3
    FINISH = 4
    NOT_FOUND = 5
    CLIENT_HELLO = 6
    SERVER_HELLO = 7

PLAINTEXT_OPCODES = {Opcode.CLIENT_HELLO.value, Opcode.SERVER_HELLO.value}
HEADER_FORMAT = "!B8sIIHH"
HEADER_SIZE = struct.calcsize(HEADER_FORMAT)
AAD_FORMAT = "!B8sII"

class SRFTPacket:
    opcode: int
    session_id: bytes
    seq_number: int
    ack_number: int
    payload_length: int
    checksum: int
    payload_plaintext: bytes
    payload_ciphertext: bytes
    
    def __init__(
        self,
        opcode: int,
        session_id: bytes,
        seq_number: int,
        ack_number: int,
        payload_length: int,
        checksum: int,
        payload_plaintext: bytes = None,
        payload_ciphertext: bytes = None
    ):
        self.opcode = opcode
        self.session_id = session_id
        self.seq_number = seq_number
        self.ack_number = ack_number
        self.payload_length = payload_length
        self.checksum = checksum
        self.payload_plaintext = payload_plaintext
        self.payload_ciphertext = payload_ciphertext

    def is_valid_checksum(self) -> bool:
        payload = (
            self.payload_ciphertext
            if self.payload_ciphertext is not None
            else self.payload_plaintext
        )
        return self.checksum == SRFTPacket.compute_checksum(payload)
    
    def is_valid(self) -> bool:
        valid_opcodes = [op.value for op in Opcode]
        payload = (
            self.payload_ciphertext
            if self.payload_ciphertext is not None
            else self.payload_plaintext
        )

        if (self.opcode not in valid_opcodes or 
            self.seq_number < 0 or
            self.ack_number < 0 or
            payload is None or
            self.payload_length != len(payload) or
            not self.is_valid_checksum()
            ):
            return False

        return True

    def summary(self) -> str:
        valid_opcodes = [op.value for op in Opcode]
        opcode_name = Opcode(self.opcode).name if self.opcode in valid_opcodes else "UNKNOWN"

        return (
            f"SRFTPacket(opcode={opcode_name}, "
            f"session_id={self.session_id}, "
            f"seq_number={self.seq_number}, "
            f"ack_number={self.ack_number}, "
            f"payload_length={self.payload_length}, "
            f"checksum={self.checksum}, "
            f"payload_plain={self.payload_plaintext}, "
            f"payload_cipher={self.payload_ciphertext})"
        )

          
    @classmethod
    def compute_checksum(cls, payload: bytes) -> int:
        if len(payload) % 2 == 1:
            payload += b"\x00"

        total = 0

        for i in range(0, len(payload), 2):
            word = (payload[i] << 8) + payload[i + 1]
            total += word
            total = (total & 0xFFFF) + (total >> 16)

        return (~total) & 0xFFFF

    # Base packet building method
    @classmethod
    def __build_packet(
        cls,
        opcode: int,
        session_id: bytes = b"",
        seq_number: int = 0,
        ack_number: int = 0,
        checksum: int = 0,
        payload_plain: bytes = None,
        payload_cipher: bytes = None
    ) -> "SRFTPacket":
        # assert payload_plain is not None or payload_cipher is not None
        if payload_plain is not None:
            payload = payload_plain
            p_length = len(payload_plain)
        else:
            # Cipher payload
            payload = payload_cipher
            p_length = len(payload_cipher)
            
        # Compute checksum for non encrypted packey
        # Use mainly for hello packet during handshake
        # Checksum will be re compute after encryption
        if checksum == 0:
            checksum = cls.compute_checksum(payload)
            
        return SRFTPacket(
            opcode=opcode,
            session_id=session_id,
            seq_number=seq_number,
            ack_number=ack_number,
            payload_length=p_length,
            checksum=checksum,
            payload_plaintext=payload_plain,
            payload_ciphertext=payload_cipher
        )
        
    @classmethod
    def build_client_hello_packet(cls, handshake_chunk: bytes) -> "SRFTPacket":
        return cls.__build_packet(
            opcode=Opcode.CLIENT_HELLO.value,
            payload_plain=handshake_chunk
        )


    @classmethod
    def build_server_hello_packet(cls, handshake_chunk: bytes) -> "SRFTPacket":
        return cls.__build_packet(
            opcode=Opcode.SERVER_HELLO.value,
            payload_plain=handshake_chunk
        )

    @classmethod
    def build_request_packet(cls, filename: str) -> "SRFTPacket":
        return cls.__build_packet(
            opcode=Opcode.REQUEST.value,
            payload_plain=filename.encode("utf-8")
        )

    @classmethod
    def build_not_found_packet(cls) -> "SRFTPacket":
        return cls.__build_packet(
            opcode=Opcode.NOT_FOUND.value,
            payload_plain=b""
        )

    @classmethod
    def build_transmit_packet(cls, seq_number: int, chunk: bytes) -> "SRFTPacket":
        return cls.__build_packet(
            opcode=Opcode.TRANSMIT.value,
            seq_number=seq_number,
            payload_plain=chunk
        )

    @classmethod
    def build_ack_packet(cls, last_in_order: int) -> "SRFTPacket":
        return cls.__build_packet(
            opcode=Opcode.ACKNOWLEDGE.value,
            ack_number=last_in_order,
            payload_plain=b""
        )

    @classmethod
    def build_finish_packet(
        cls, seq_number: int, last_acknowledged: int, sha256_hex: str
    ) -> "SRFTPacket":
        return cls.__build_packet(
            opcode=Opcode.FINISH.value,
            seq_number=seq_number,
            ack_number=last_acknowledged,
            payload_plain=sha256_hex.encode("ascii")
        )

    def encode_packet(self) -> bytes:
        if not self.is_valid():
            raise ValueError("Cannot encode invalid SRFTPacket")

        header_bytes = struct.pack(
            HEADER_FORMAT,
            self.opcode,
            self.session_id,
            self.seq_number,
            self.ack_number,
            self.payload_length,
            self.checksum,
        )
        
        if self.payload_ciphertext is not None:
            return header_bytes + self.payload_ciphertext
        if self.payload_plaintext is not None:
            return header_bytes + self.payload_plaintext
        raise ValueError("Packet missing payload bytes")

    @classmethod
    def decode_packet(cls, raw_bytes: bytes) -> "SRFTPacket":
        if len(raw_bytes) < HEADER_SIZE:
            raise ValueError("Raw bytes shorter than SRFT header size")

        header_part = raw_bytes[:HEADER_SIZE]
        payload_part = raw_bytes[HEADER_SIZE:]

        opcode, session_id, seq_number, ack_number, payload_length, checksum = struct.unpack(
            HEADER_FORMAT,
            header_part,
        )
        
        if opcode in PLAINTEXT_OPCODES:
            packet = SRFTPacket(
                opcode=opcode,
                session_id=session_id,
                seq_number=seq_number,
                ack_number=ack_number,
                payload_length=payload_length,
                checksum=checksum,
                payload_plaintext=payload_part
            )
        else:
            packet = SRFTPacket(
                opcode=opcode,
                session_id=session_id,
                seq_number=seq_number,
                ack_number=ack_number,
                payload_length=payload_length,
                checksum=checksum,
                payload_ciphertext=payload_part
            )

        return packet
    
    
    def encrypt(self, sec_ctx: SecurityContext):
        """
        - Encrypt payload_plaintext using AES_GCM encryption provided by
          security_cntxt parameter. Using opcode, session_id, seq_number,
          and ack_number as AAD(Additional Authenticated Data)
        - Additionally prepend 12 bytes nonce into the payload for serialization
        - Final packet payload in bytes is structure as:
          [nonce(12 bytes)] + [encrypted_payload(include 16 bytes tag)]      
        - The operation is done in-place where the encrypted payload will be added
          onto payload_ciphertext field with payload_length and checksum recalculated
        """
        if not sec_ctx.is_established():
            raise ValueError("SecurityContext not established")

        self.session_id = sec_ctx.session_id

        # Serialize AAD for encryption
        aad_bytes = struct.pack(
            AAD_FORMAT,             
            self.opcode,
            self.session_id,
            self.seq_number,
            self.ack_number
            )
        nonce = os.urandom(12)
        encrypted_payload = sec_ctx.encrypt(
            nonce,
            self.payload_plaintext,
            aad_bytes
            )
        
        # Replace ciphertext payload with nonce + encrypted payload
        self.payload_ciphertext = nonce + encrypted_payload
        self.payload_length = len(self.payload_ciphertext)
        # Recompute checksum
        self.checksum = SRFTPacket.compute_checksum(self.payload_ciphertext)
    
    def decrypt(self, sec_ctx: SecurityContext):
        """
        - Decrypt payload_plaintext using SecurityContext.
          Using opcode, session_id, seq_number and ack_number as AAD(Additional Authenticated Data)
        - Extract nonce from the first 12 bytes of payload_ciphertext     
        - The operation is done in-place where the encrypted payload will be added
          onto payload_plaintext field
        - In case of decryption/authentication failed:
          SecurityContext would absorb the exception and return None
        - Returns bool for whether the decryption is successful
        """
        if not sec_ctx.is_established():
            return False

        if self.session_id != sec_ctx.session_id:
            return False

        # Serialize AAD for encryption
        aad_bytes = struct.pack(
            AAD_FORMAT,             
            self.opcode,
            self.session_id,
            self.seq_number,
            self.ack_number
            )
        nonce = self.payload_ciphertext[:12]
        enc_text = self.payload_ciphertext[12:]
        # security context will return None if decryption failed
        self.payload_plaintext = sec_ctx.decrypt(nonce, enc_text, aad_bytes)
        if self.payload_plaintext is None:
            return False
        return True


if __name__ == "__main__":
    print("HEADER_SIZE =", HEADER_SIZE)
    print()

    request_packet = SRFTPacket.build_request_packet("test.txt")
    transmit_packet = SRFTPacket.build_transmit_packet(1, b"chunk1")
    ack_packet = SRFTPacket.build_ack_packet(1)
    finish_packet = SRFTPacket.build_finish_packet(2, 1, "a" * 64)

    packets = [
        ("REQUEST", request_packet),
        ("TRANSMIT", transmit_packet),
        ("ACKNOWLEDGE", ack_packet),
        ("FINISH", finish_packet),
    ]

    for label, packet in packets:
        print(f"--- {label} original ---")
        print(packet.summary())
        print("valid =", packet.is_valid())

        encoded = SRFTPacket.encode_packet(packet)
        decoded = SRFTPacket.decode_packet(encoded)

        print(f"--- {label} decoded ---")
        print(decoded.summary())
        print("valid =", decoded.is_valid())
        print()

    bad_packet = SRFTPacket.build_transmit_packet(1, b"chunk1")
    bad_packet.checksum += 1

    print("--- CORRUPTED PACKET TEST ---")
    print(bad_packet.summary())
    print("valid =", bad_packet.is_valid())
