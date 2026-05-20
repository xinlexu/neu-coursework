import os
import random
from srft_packet import Opcode, SRFTPacket


def before_send(st, pkt, ip_port):
    """Called per-packet in srv_send_transmit, after encrypt, before send."""
    if st.attack_mode is None or st.attack_triggered:
        return

    if st.attack_mode == "tamper":
        # Test 3: flip two bits in encrypted data (past the 12-byte nonce)
        b = bytearray(pkt.payload_ciphertext)
        flips = 0
        # flip one 0-bit to 1
        for i in range(8):
            if not (b[12] & (1 << i)):
                b[12] |= (1 << i)
                flips += 1
                break
        # flip one 1-bit to 0
        for i in range(8):
            if b[13] & (1 << i):
                b[13] &= ~(1 << i)
                flips += 1
                break
        if flips < 2:
            return  # edge case: retry on next packet
        pkt.payload_ciphertext = bytes(b)
        pkt.checksum = SRFTPacket.compute_checksum(pkt.payload_ciphertext)
        st.attack_triggered = True
        print(f"[ATTACK] Tampered packet seq={pkt.seq_number}")

    elif st.attack_mode == "replay":
        # Test 4: store this valid packet for resend later
        st.replay_packet = (pkt, ip_port)


def after_send_loop(st, ip_port):
    """Called once in srv_send_transmit, after the send loop finishes."""
    if st.attack_mode is None or st.attack_triggered:
        return

    if st.attack_mode == "replay" and st.replay_packet is not None:
        # Test 4: resend the captured packet
        stored_pkt, stored_addr = st.replay_packet
        st.send_one(stored_pkt, stored_addr)
        st.attack_triggered = True
        print(f"[ATTACK] Replayed packet seq={stored_pkt.seq_number}")

    elif st.attack_mode == "inject":
        # Test 5: forged packet with random ciphertext
        # real TRANSMIT ciphertext = nonce(12) + encrypted_chunk + tag(16) = 1428 bytes
        payload = os.urandom(1428)
        forged = SRFTPacket(
            opcode=Opcode.TRANSMIT.value,
            session_id=st.sec_ctx.session_id,
            seq_number=random.randint(1, 65535),
            ack_number=0,
            payload_length=len(payload),
            checksum=SRFTPacket.compute_checksum(payload),
            payload_ciphertext=payload,
        )
        st.send_one(forged, ip_port)
        st.attack_triggered = True
        print(f"[ATTACK] Injected forged packet")
