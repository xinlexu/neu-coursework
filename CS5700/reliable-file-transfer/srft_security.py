import hmac
import hashlib
import os
import secrets
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.exceptions import InvalidTag

from enum import Enum


class CipherInfo(Enum):
    AES_256_GCM = 1


NONCE_SZ = 16
CIPHERINFO_SZ = 4
SESSIONID_SZ = 8
MAC_SZ = hashlib.sha256().digest_size  # 32
ENC_KEY_SZ = 32

CLIENT_HELLO_SZ = NONCE_SZ + CIPHERINFO_SZ + MAC_SZ  # 52
SERVER_HELLO_SZ = NONCE_SZ + SESSIONID_SZ + MAC_SZ  # 56

"""
1. client sends client_nonce+cipher_info+HMAC
2. server verifies client hello
3. server sends server_nonce+session_id+HMAC
4. client verifies server hello
5. both derive enc_key
"""


class SecurityContext:
    def __init__(self, psk: bytes):
        self.psk = psk
        # nonce and session_id are generated once only per security context
        self.client_nonce: bytes | None = None
        self.server_nonce: bytes | None = None
        self.cipher_info: bytes | None = None
        self.session_id: bytes | None = None
        self.enc_key: bytes | None = None
        self.aesgcm: AESGCM | None = None

    # structure: [16 bytes client nonce][4 bytes cipherinfo][32 bytes HMAC]
    def get_client_hello(self) -> bytes:
        # keep nonce constant in one SecurityContext instance in case of retransmit 
        if self.client_nonce is None:
            self.client_nonce = os.urandom(NONCE_SZ)
        self.cipher_info = CipherInfo.AES_256_GCM.value.to_bytes(
            CIPHERINFO_SZ, "little"
        )
        fields = self.client_nonce + self.cipher_info
        mac = hmac.new(self.psk, fields, hashlib.sha256).digest()
        return fields + mac

    # structure: [16 bytes server nonce][8 bytes session ID][32 bytes HMAC]
    def get_server_hello(self) -> bytes:
        # keep nonce/sesh_id constant in one SecurityContext instance in case of retransmit 
        if self.server_nonce is None:
            self.server_nonce = os.urandom(NONCE_SZ)
        if self.session_id is None:
            self.session_id = secrets.token_hex(SESSIONID_SZ // 2).encode("ascii")
        fields = self.server_nonce + self.session_id
        mac = hmac.new(self.psk, fields, hashlib.sha256).digest()
        return fields + mac

    def verify_client_hello(self, cli_hello: bytes) -> bool:
        if len(cli_hello) != CLIENT_HELLO_SZ:
            return False
        client_nonce = cli_hello[:NONCE_SZ]
        cipher_info = cli_hello[NONCE_SZ : NONCE_SZ + CIPHERINFO_SZ]
        mac = cli_hello[NONCE_SZ + CIPHERINFO_SZ :]
        fields = client_nonce + cipher_info
        expected_mac = hmac.new(self.psk, fields, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected_mac):
            return False
        self.client_nonce = client_nonce
        self.cipher_info = cipher_info
        return True

    def verify_server_hello(self, srv_hello: bytes) -> bool:
        if len(srv_hello) != SERVER_HELLO_SZ:
            return False
        server_nonce = srv_hello[:NONCE_SZ]
        session_id = srv_hello[NONCE_SZ : NONCE_SZ + SESSIONID_SZ]
        mac = srv_hello[NONCE_SZ + SESSIONID_SZ :]
        fields = server_nonce + session_id
        expected_mac = hmac.new(self.psk, fields, hashlib.sha256).digest()
        if not hmac.compare_digest(mac, expected_mac):
            return False
        self.server_nonce = server_nonce
        self.session_id = session_id
        return True

    # TODO: method name is weird
    def derive_enc_key(self) -> bytes:
        if self.client_nonce is None or self.server_nonce is None:
            raise ValueError("SecurityContext: Missing nonces for key derivation")
        self.enc_key = HKDF(
            algorithm=hashes.SHA256(),
            length=ENC_KEY_SZ,
            salt=self.client_nonce + self.server_nonce,
            info=b"enc_key",
        ).derive(self.psk)
        self.aesgcm = AESGCM(self.enc_key)
        return self.enc_key

    def encrypt(self, nonce, plaintext, aad_bytes) -> bytes:
        if self.aesgcm is None:
            raise ValueError("SecurityContext: AESGCM key not initialized")
        return self.aesgcm.encrypt(nonce, plaintext, aad_bytes)

    def decrypt(self, nonce, enc_text, aad_bytes) -> bytes | None:
        if self.aesgcm is None:
            raise ValueError("SecurityContext: AESGCM key not initialized")
        try:
            plaintext = self.aesgcm.decrypt(nonce, enc_text, aad_bytes)
            return plaintext
        except InvalidTag:
            print("AEAD decryption failed")
            return None


    def is_established(self) -> bool:
        return (
            self.client_nonce is not None
            and self.server_nonce is not None
            and self.cipher_info is not None
            and self.session_id is not None
            and self.enc_key is not None
            and self.aesgcm is not None
        )
