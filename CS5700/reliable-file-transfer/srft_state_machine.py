from __future__ import annotations

from enum import Enum, auto
from typing import TYPE_CHECKING
import os
import queue
import select
import time

from srft_config import SRFT_MAX_RETRIES, SRFT_WINDOW_SIZE, SRFT_TIMEOUT_INTERVAL, SRFT_DUP_ACK_THRESHOLD, SRFT_ACK_BATCH_THRESHOLD
from file_manager import ClientFileManager, ServerFileManager
from srft_packet import Opcode, SRFTPacket
from srft_attack import before_send, after_send_loop
if TYPE_CHECKING:
    from SRFT_UDPServer import ServerThread
    from SRFT_UDPClient import ClientRunner


class ClientState(Enum):
    CLIENT_INIT = auto()
    CLIENT_SEND_HELLO = auto()
    CLIENT_WAIT_HELLO = auto()
    CLIENT_SEND_REQUEST = auto()
    CLIENT_WAIT_PACKET = auto()
    CLIENT_PROCESS_TRANSMIT = auto()
    CLIENT_SEND_ACK = auto()
    CLIENT_SEND_FINISH_ACK = auto()
    CLIENT_CLEANUP = auto()
    CLIENT_COMPLETE = auto()


class ServerState(Enum):
    SERVER_INIT = auto()
    SERVER_SEND_HELLO = auto()
    SERVER_WAIT_REQUEST = auto()
    SERVER_PREPARE_FILE = auto()
    SERVER_SEND_TRANSMIT = auto()
    SERVER_FAST_RETRANSMIT = auto()
    SERVER_WAIT_ACK_OR_TIMEOUT = auto()
    SERVER_SEND_FINISH = auto()
    SERVER_CLEANUP = auto()
    SERVER_COMPLETE = auto()


# ================================================================================
# SERVER HANDLER FUNCTIONS
# - assumption: all queued packets = verified + checksumed
# ================================================================================

def srv_should_cleanup_after_retry(st: ServerThread, state_to_retry: ServerState) -> bool:
    """
    Increment retry count, then either schedule a retry state or transition to cleanup.
    Returns True if should cleanup, returns False if should continue retry.
    Mutates server state and retry count.
    """

    st.retry_count += 1
    if st.retry_count >= SRFT_MAX_RETRIES:
        st.state = ServerState.SERVER_CLEANUP
        return True
    st.state = state_to_retry
    return False


def srv_init(st: ServerThread) -> None:
    # st.state = ServerState.SERVER_WAIT_REQUEST
    st.state = ServerState.SERVER_SEND_HELLO
    return


def srv_send_hello(st: ServerThread) -> None:
    # assumption: main thread guarantees that
    # cli_hello_pkt is already in queue + checksum verified + is a hello

    cli_hello_pkt: SRFTPacket = st.recv_one()
    if not st.sec_ctx.verify_client_hello(cli_hello_pkt.payload_plaintext):
        st.state = ServerState.SERVER_CLEANUP
        return
    
    st.handshake_success = True

    # client hello must be valid, now create enc_key
    srv_hello_bytes = st.sec_ctx.get_server_hello()
    st.sec_ctx.derive_enc_key()

    srv_hello_pkt = SRFTPacket.build_server_hello_packet(srv_hello_bytes)
    st.send_one(srv_hello_pkt, (st.client_ip, st.client_port))
    st.state = ServerState.SERVER_WAIT_REQUEST


def srv_wait_request(st: ServerThread) -> None: 
    try:
        req_pkt: SRFTPacket = st.recv_one(timeout=SRFT_TIMEOUT_INTERVAL)
    except queue.Empty:
        if not srv_should_cleanup_after_retry(st, ServerState.SERVER_WAIT_REQUEST):
            # diff between this and going back to srv_send_hello
            # is that this doesn't try to receive another client hello
            srv_hello_bytes = st.sec_ctx.get_server_hello()
            srv_hello_pkt = SRFTPacket.build_server_hello_packet(srv_hello_bytes)
            st.send_one(srv_hello_pkt, (st.client_ip, st.client_port))
        return
    
    if not req_pkt.decrypt(st.sec_ctx):
        st.state = ServerState.SERVER_WAIT_REQUEST
        return

    st.filename = req_pkt.payload_plaintext.decode()
    st.state = ServerState.SERVER_PREPARE_FILE


def srv_prepare_file(st: ServerThread) -> None:
    if len(st.filename) > 0:
        st.file_handle = ServerFileManager(st.filename)
        if st.file_handle.file_is_valid():
            if st.file_handle.get_total_chunks() == 0:
                st.state = ServerState.SERVER_SEND_FINISH
            else:
                st.state = ServerState.SERVER_SEND_TRANSMIT
            return  # expected path

    # error path
    pkt = SRFTPacket.build_not_found_packet()
    pkt.encrypt(st.sec_ctx)
    st.send_one(pkt, (st.client_ip, st.client_port))
    st.state = ServerState.SERVER_CLEANUP


def srv_can_send(st: ServerThread) -> bool:
    is_within_window = st.next_seq_to_send < (st.last_ack + 1) + SRFT_WINDOW_SIZE
    has_remaining_chunks = st.next_seq_to_send <= st.file_handle.get_total_chunks()
    return is_within_window and has_remaining_chunks


def srv_send_transmit(st: ServerThread) -> None:
    ip_port = (st.client_ip, st.client_port)

    while srv_can_send(st):
        next_seq = st.next_seq_to_send
        chunk_bytes = st.file_handle.get_chunk(next_seq)
        pkt = SRFTPacket.build_transmit_packet(next_seq, chunk_bytes)
        pkt.encrypt(st.sec_ctx)
        before_send(st, pkt, ip_port)
        st.send_one(pkt, ip_port)
        st.next_seq_to_send += 1

    after_send_loop(st, ip_port)
    st.state = ServerState.SERVER_WAIT_ACK_OR_TIMEOUT


def srv_fast_retransmit(st: ServerThread) -> None:
    ip_port = (st.client_ip, st.client_port)
    next_seq = st.last_ack + 1
    chunk_bytes = st.file_handle.get_chunk(next_seq)
    pkt = SRFTPacket.build_transmit_packet(next_seq, chunk_bytes)
    pkt.encrypt(st.sec_ctx)
    st.send_one(pkt, ip_port)
    st.dup_ack_count = None
    st.state = ServerState.SERVER_WAIT_ACK_OR_TIMEOUT


def srv_wait_ack_or_timeout(st: ServerThread) -> None:
    try:
        pkt: SRFTPacket = st.recv_one(timeout=SRFT_TIMEOUT_INTERVAL)
    except queue.Empty:
        if not srv_should_cleanup_after_retry(st, ServerState.SERVER_SEND_TRANSMIT):
            st.dup_ack_count = None
            st.next_seq_to_send = st.last_ack + 1  # retry all outstanding
        return

    # decryption failure
    if not pkt.decrypt(st.sec_ctx):
        st.state = ServerState.SERVER_WAIT_ACK_OR_TIMEOUT
        return

    # not ACK = keep waiting
    if pkt.opcode != Opcode.ACKNOWLEDGE.value:
        st.state = ServerState.SERVER_WAIT_ACK_OR_TIMEOUT
        return

    # stale or duplicate ACK
    if pkt.ack_number <= st.last_ack:
        # dup ACK = potential fast retransmit trigger
        if pkt.ack_number == st.last_ack:
            st.dup_ack_count = (st.dup_ack_count or 0) + 1
            if st.dup_ack_count >= SRFT_DUP_ACK_THRESHOLD:
                st.state = ServerState.SERVER_FAST_RETRANSMIT
                return
        st.state = ServerState.SERVER_WAIT_ACK_OR_TIMEOUT
        return

    # valid cumulative ACK — advance window
    st.dup_ack_count = None
    st.retry_count = 0
    st.last_ack = pkt.ack_number

    if pkt.ack_number >= st.file_handle.get_total_chunks():  # all chunks acked
        st.state = ServerState.SERVER_SEND_FINISH
    else:
        st.state = ServerState.SERVER_SEND_TRANSMIT


def srv_send_finish(st: ServerThread) -> None:
    ip_port = (st.client_ip, st.client_port)
    out_pkt = SRFTPacket.build_finish_packet(
        st.next_seq_to_send,
        st.last_ack,
        st.file_handle.get_sha256(),
    )
    out_pkt.encrypt(st.sec_ctx)
    st.send_one(out_pkt, ip_port)

    try:
        in_pkt: SRFTPacket = st.recv_one(timeout=SRFT_TIMEOUT_INTERVAL)
    except queue.Empty:
        srv_should_cleanup_after_retry(st, ServerState.SERVER_SEND_FINISH)
        return

    if not in_pkt.decrypt(st.sec_ctx):
        st.state = ServerState.SERVER_SEND_FINISH
        return

    # for the client, last in-order+1 = ACK for FINISH
    if (
        in_pkt.opcode == Opcode.ACKNOWLEDGE.value
        and in_pkt.ack_number >= st.file_handle.get_total_chunks() + 1
    ):
        st.retry_count = 0
        st.transfer_success = True
        st.state = ServerState.SERVER_CLEANUP


def srv_cleanup(st: ServerThread) -> None:
    st.end_time = time.time()
    st.server_report()
    if st.file_handle is not None:
        st.file_handle.close()
    st.state = ServerState.SERVER_COMPLETE


# ================================================================================
# CLIENT HANDLER FUNCTIONS
# ================================================================================


def cli_handle_wait_packet_retry(
    cli: ClientRunner, state_to_retry: ClientState, timeout: float) -> tuple[SRFTPacket, tuple[str, int]] | None:
    """
    Reusable logic for waiting for packet with timeout and retry management
    - Returns a packet pair or None
    - if a packet pair is returned, caller should process it
    - if None is returned, caller should return and not mutate state
    """
    pkt_ready, _, _ = select.select([cli.srft_sk], [], [], timeout)

    # 1. success path: pkt ready
    if pkt_ready:
        pair = cli.srft_sk.recv_one()
        if pair is not None:
            cli.retry_count = 0
            # Increment received packets (not validated)
            cli.num_packets_received_from_server += 1
            if not pair[0].is_valid():
                # Invalid SRFT packets, increment checksum error if checksum not valid
                # else drop silently
                if not pair[0].is_valid_checksum():
                    cli.num_checksum_error_packets += 1
                pair = None # Invalid packet return to none
        return pair
    cli.retry_count += 1

    # 2. bail out path: max retries exceeded
    if cli.retry_count > SRFT_MAX_RETRIES:
        print(f"Transfer failed: max retries exceeded")
        cli.state = ClientState.CLIENT_CLEANUP
        return None

    # 3. retry path: no pkt + timeout but can retry
    cli.state = state_to_retry
    return None


def cli_init(cli: ClientRunner) -> None:
    cli.file_manager = ClientFileManager(cli.outfile)
    cli.state = ClientState.CLIENT_SEND_HELLO


def cli_send_hello(cli: ClientRunner) -> None:
    cli_hello_bytes = cli.sec_ctx.get_client_hello()
    cli_hello_pkt = SRFTPacket.build_client_hello_packet(cli_hello_bytes)
    cli.srft_sk.send_one(cli_hello_pkt, cli.server_ip_port)
    cli.state = ClientState.CLIENT_WAIT_HELLO


def cli_wait_hello(cli: ClientRunner) -> None:
    pair = cli_handle_wait_packet_retry(cli, ClientState.CLIENT_SEND_HELLO, SRFT_TIMEOUT_INTERVAL)
    if pair is None:
        return

    srv_hello_pkt, _addr = pair
    if srv_hello_pkt.opcode != Opcode.SERVER_HELLO.value:
        cli.state = ClientState.CLIENT_WAIT_HELLO
        return
    if not cli.sec_ctx.verify_server_hello(srv_hello_pkt.payload_plaintext):
        cli.state = ClientState.CLIENT_CLEANUP
        return
    cli.sec_ctx.derive_enc_key()
    cli.handshake_success = True
    cli.state = ClientState.CLIENT_SEND_REQUEST


def cli_send_request(cli: ClientRunner) -> None:
    request_pkt = SRFTPacket.build_request_packet(cli.filename)
    request_pkt.encrypt(cli.sec_ctx)
    cli.srft_sk.send_one(request_pkt, cli.server_ip_port)
    cli.state = ClientState.CLIENT_WAIT_PACKET


def cli_wait_packet(cli: ClientRunner) -> None:
    if cli.ack_deadline is not None:
        timeout = max(0.0, cli.ack_deadline - time.time())
    else:
        timeout = SRFT_TIMEOUT_INTERVAL

    state_to_retry = None
    if cli.transmit_started:
        state_to_retry = ClientState.CLIENT_SEND_ACK
    else: 
        state_to_retry = ClientState.CLIENT_SEND_REQUEST

    pair = cli_handle_wait_packet_retry(cli, state_to_retry, timeout)
    if pair is None:
        return

    pkt, _addr = pair

    if not pkt.decrypt(cli.sec_ctx):
        cli.aead_auth_failures += 1
        cli.state = ClientState.CLIENT_WAIT_PACKET
        return

    cli.pending_pkt = pkt

    if pkt.opcode == Opcode.TRANSMIT.value:
        cli.transmit_started = True
        cli.state = ClientState.CLIENT_PROCESS_TRANSMIT
    elif pkt.opcode == Opcode.NOT_FOUND.value:
        print(f"File not found on server: {cli.filename}")
        cli.state = ClientState.CLIENT_CLEANUP
    elif pkt.opcode == Opcode.FINISH.value:
        if pkt.payload_plaintext is None:
            cli.server_sha256 = None
        else:
            try:
                cli.server_sha256 = pkt.payload_plaintext.decode("ascii")
            except UnicodeDecodeError:
                cli.server_sha256 = None

        is_valid_server_sha256 = (
            cli.server_sha256 is not None
            and len(cli.server_sha256) == 64
            and all(ch in "0123456789abcdefABCDEF" for ch in cli.server_sha256)
        )

        if is_valid_server_sha256:
            cli.local_sha256 = cli.file_manager.get_sha256()
            cli.final_verification_passed = cli.local_sha256 == cli.server_sha256
        else:
            cli.local_sha256 = None
            cli.final_verification_passed = False

        if cli.final_verification_passed:
            cli.state = ClientState.CLIENT_SEND_FINISH_ACK
        else:
            print(
                f"SHA256 verification failed for {cli.filename}: "
                f"server={cli.server_sha256}, client={cli.local_sha256}"
            )
            cli.state = ClientState.CLIENT_CLEANUP
    else:
        cli.state = ClientState.CLIENT_WAIT_PACKET

    return


def cli_process_transmit(cli: ClientRunner) -> None:
    pkt = cli.pending_pkt
    assert pkt is not None  # pkt must exist if we WAIT => PROCESS

    if pkt.seq_number < cli.expected_seq:
        # dup detected: ACK immediately
        cli.num_duplicate_packets += 1
        cli.replay_drops += 1
        cli.state = ClientState.CLIENT_SEND_ACK
        return

    if pkt.seq_number >= cli.expected_seq + cli.receiver_window_size:
        # outside window: ACK immediately
        cli.replay_drops += 1
        cli.state = ClientState.CLIENT_SEND_ACK
        return

    if pkt.seq_number > cli.expected_seq:
        # out-of-order within window: buffer and ACK immediately
        cli.num_out_of_order_packets += 1
        if pkt.seq_number in cli.file_manager.buffer:
            # Already buffered this chunk, also treat as replay packet
            cli.replay_drops += 1
        else:
            cli.file_manager.append_chunk(pkt.seq_number, pkt.payload_plaintext)
        cli.out_of_order = True
        cli.state = ClientState.CLIENT_SEND_ACK
        return

    # in-order: write, flush any buffered packets, update progress
    prev_expected = cli.expected_seq

    # design quirk:
    # only file_manager knows the real expected_seq with buffering knowledge = source of truth
    # cli.expected_seq may cause TOCTOU
    cli.expected_seq = cli.file_manager.append_chunk(
        pkt.seq_number, pkt.payload_plaintext
    )
    cli.last_in_order = cli.expected_seq - 1
    cli.ack_batch_count += cli.expected_seq - prev_expected

    if cli.ack_deadline is None:
        cli.ack_deadline = time.time() + cli.ack_delay_interval

    # accumulated enough unACKed pkts or deadline exceeded
    # or notify server ASAP based on the out-of to in-order transition (reception of one missing packet)
    # (doesn't mean that ALL missing packets are fulfilled)
    if (
        cli.ack_batch_count >= SRFT_ACK_BATCH_THRESHOLD
        or time.time() >= cli.ack_deadline
        or cli.out_of_order
    ):
        cli.state = ClientState.CLIENT_SEND_ACK
        cli.out_of_order = False
    else:
        cli.state = ClientState.CLIENT_WAIT_PACKET


def cli_send_ack(cli: ClientRunner) -> None:
    ack_pkt = SRFTPacket.build_ack_packet(cli.last_in_order)
    ack_pkt.encrypt(cli.sec_ctx)
    cli.srft_sk.send_one(ack_pkt, cli.server_ip_port)
    cli.ack_batch_count = 0
    cli.ack_deadline = None
    cli.state = ClientState.CLIENT_WAIT_PACKET


def cli_send_finish_ack(cli: ClientRunner) -> None:
    ack_pkt = SRFTPacket.build_ack_packet(
        cli.last_in_order + 1
    )  # last in-order+1 = ACK for FINISH
    ack_pkt.encrypt(cli.sec_ctx)
    cli.srft_sk.send_one(ack_pkt, cli.server_ip_port)
    cli.state = ClientState.CLIENT_CLEANUP


def cli_cleanup(cli: ClientRunner) -> None:
    cli.end_time = time.time()
    if cli.pending_pkt and cli.pending_pkt.opcode == Opcode.FINISH.value and cli.final_verification_passed:
        cli.transfer_success = True
    else:
        cli.transfer_success = False  # e.g. file not found
    cli.client_report()

    if cli.file_manager is not None:
        cli.file_manager.close(cli.transfer_success)

    cli.state = ClientState.CLIENT_COMPLETE


# ================================================================================
# exported function tables for server and client
# ================================================================================

SERVER_STATE_HANDLERS = {
    # they must share the same function signature: (server_thread: ServerThread) -> None
    ServerState.SERVER_INIT: srv_init,
    ServerState.SERVER_SEND_HELLO: srv_send_hello,
    ServerState.SERVER_WAIT_REQUEST: srv_wait_request,
    ServerState.SERVER_PREPARE_FILE: srv_prepare_file,
    ServerState.SERVER_SEND_TRANSMIT: srv_send_transmit,
    ServerState.SERVER_FAST_RETRANSMIT: srv_fast_retransmit,
    ServerState.SERVER_WAIT_ACK_OR_TIMEOUT: srv_wait_ack_or_timeout,
    ServerState.SERVER_SEND_FINISH: srv_send_finish,
    ServerState.SERVER_CLEANUP: srv_cleanup,
}

CLIENT_STATE_HANDLERS = {
    # they must share the same function signature: (client_runner: ClientRunner) -> None
    ClientState.CLIENT_INIT: cli_init,
    ClientState.CLIENT_SEND_HELLO: cli_send_hello,
    ClientState.CLIENT_WAIT_HELLO: cli_wait_hello,
    ClientState.CLIENT_SEND_REQUEST: cli_send_request,
    ClientState.CLIENT_WAIT_PACKET: cli_wait_packet,
    ClientState.CLIENT_PROCESS_TRANSMIT: cli_process_transmit,
    ClientState.CLIENT_SEND_ACK: cli_send_ack,
    ClientState.CLIENT_SEND_FINISH_ACK: cli_send_finish_ack,
    ClientState.CLIENT_CLEANUP: cli_cleanup,
}
