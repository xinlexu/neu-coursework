# CS5700 Group 5 SRFT Project

## Table of Contents
- [Overview](#overview)
- [Usage](#usage)
- [Design and Key Funtionalities](#design)
    - [State Machine and Packet Sequence Handling](#state-machine-and-packet-sequence-handling)
    - [Server and Client File Manager](#server-and-client-file-manager)
    - [Packet Layer](#packet-layer)
    - [Socket Layer](#socket-layer)
    - [Security Context](#security-context)
    - [Threading Model](#threading-model)
    - [Implemented Features](#implemented-features)
    - [Current Limitations](#current-limitations)
    - [Lesson Learned](#lesson-learned)
    - [Future Improvements](#future-improvements)
- [Implementation and Test Results](#implementation-and-test-results)
- [Docker Usage](#docker-usage)

## Overview

This project implements SRFT, a reliable and secure file transfer protocol over UDP using raw sockets. The implementation combines explicit client/server state machines, packet sequence and acknowledgement handling, timeout-based recovery, a security handshake using a pre-shared key, HKDF-based key derivation, AES-GCM packet encryption, and final SHA-256 verification of the transferred file.

The code is organized around a packet layer, a security context, file managers, and separate client/server state-machine handlers. This structure made it easier to evolve the project from the reliable transfer baseline into the secure transfer path.

## Usage

### Server

```bash
# Run server
python3 SRFT_UDPServer.py

# Optional: run server in attack mode for security testing
python3 SRFT_UDPServer.py --attack <mode>
```

#### Available modes

`tamper` - Modify one DATA packet sent from the server by flipping 2 bits, one `0->1` and one `1->0`.

`replay` - Capture one valid DATA packet and retransmit it later (duplicate/replay).

`inject` - Inject and transmit one random forged DATA packet.

All files that are accessible and transferable from the server are located inside the `resources` directory.

### Client

```bash
# Run client
python3 SRFT_UDPClient.py <file_name> <server_ip>

# Optional: specify a different pre-shared key (PSK) for security testing
python3 SRFT_UDPClient.py <file_name> <server_ip> --psk <PSK>
```

All downloaded files are stored inside the `downloads` directory.

# Design and Key Functionalities

## State Machine and Packet Sequence Handling

The protocol is implemented with explicit client-side and server-side state handlers instead of one large monolithic loop. This makes the control flow easier to follow, test, and extend.

### Client State Flow

The client-side state machine includes these states:

- `CLIENT_INIT`
- `CLIENT_SEND_HELLO`
- `CLIENT_WAIT_HELLO`
- `CLIENT_SEND_REQUEST`
- `CLIENT_WAIT_PACKET`
- `CLIENT_PROCESS_TRANSMIT`
- `CLIENT_SEND_ACK`
- `CLIENT_SEND_FINISH_ACK`
- `CLIENT_CLEANUP`
- `CLIENT_COMPLETE`

The client starts by creating its file manager and sending `CLIENT_HELLO`. After receiving and validating `SERVER_HELLO`, it derives the encryption key, sends the filename request, waits for packets from the server, processes incoming data packets, sends acknowledgements when needed, and finally handles `FINISH`, SHA-256 verification, cleanup, and completion.

### Server State Flow

The server-side state machine includes these states:

- `SERVER_INIT`
- `SERVER_SEND_HELLO`
- `SERVER_WAIT_REQUEST`
- `SERVER_PREPARE_FILE`
- `SERVER_SEND_TRANSMIT`
- `SERVER_FAST_RETRANSMIT`
- `SERVER_WAIT_ACK_OR_TIMEOUT`
- `SERVER_SEND_FINISH`
- `SERVER_CLEANUP`
- `SERVER_COMPLETE`

The server begins with the security handshake, waits for an encrypted request, prepares the requested file, sends data chunks while the send window has space, waits for acknowledgements, retransmits when needed, sends `FINISH` once the transfer is complete, and then performs cleanup.

### Packet Format

Each SRFT packet contains:

- `opcode`
- `session_id`
- `seq_number`
- `ack_number`
- `payload_length`
- `checksum`

The protocol currently uses these packet types:

- `REQUEST`
- `TRANSMIT`
- `ACKNOWLEDGE`
- `FINISH`
- `NOT_FOUND`
- `CLIENT_HELLO`
- `SERVER_HELLO`

`CLIENT_HELLO` and `SERVER_HELLO` are plaintext packets. After the handshake is complete, normal request, data, acknowledgement, and finish packets are sent through the encrypt/decrypt interface.

### Sequence Numbers and Acknowledgements

Data packets use increasing sequence numbers, and the client tracks both `expected_seq` and `last_in_order`.

The acknowledgement number is cumulative and represents the highest contiguous in-order chunk received so far. This allows the sender to know how much of the file has been accepted by the receiver.

On the client side:

- in-order packets are written and advance progress
- duplicate packets are dropped and acknowledged
- out-of-order packets within the receiver window are buffered
- packets outside the receiver window are dropped

On the server side:

- packets are sent while the sender window has space
- timeout-based retransmission is supported
- duplicate ACKs can trigger fast retransmit

This keeps the reliability logic separate from file management and packet encoding/decoding.

### Security Handshake and Encrypted Path

The secure path is built around a pre-shared key (PSK). The client first sends `CLIENT_HELLO`, the server validates it and replies with `SERVER_HELLO`, and both sides derive the encryption key through HKDF.

After the handshake, the packet flow uses the current `SecurityContext` to encrypt and decrypt normal protocol packets. AES-GCM is used for packet encryption, and packet metadata is included as authenticated data. Each encrypted packet also carries a session ID so packets can be tied to the active security context.

### Final SHA-256 Verification

At transfer completion, the server computes the SHA-256 digest of the source file and sends it in the `FINISH` packet. The client computes the SHA-256 of the received file locally and compares the two digests.

The transfer is only treated as successful if:

1. the `FINISH` packet is received and validated,
2. the server SHA-256 is well-formed,
3. the local SHA-256 matches the server SHA-256, and
4. the final `FINISH` acknowledgement is sent successfully.

### Empty File Handling

An existing 0-byte file is treated as a valid file, not as `NOT_FOUND`.

For an empty file:

- the server file manager treats it as valid
- `total_chunks == 0`
- the normal `TRANSMIT` path is skipped
- the server goes directly to `FINISH`
- the final SHA-256 verification flow still applies

This allows valid empty files to complete cleanly through the same completion path instead of being rejected as missing files.

## Server and Client File Manager

The `file_manager.py` module implements the file handling layer for a custom reliable network file transfer protocol. It is responsible for secure file access, chunk-based transmission, buffering, and integrity verification on both the server and client sides.

The file manager is split into two main components:

`ServerFileManager` – Handles reading and serving files in chunks

`ClientFileManager` – Handles receiving, buffering, and reconstructing files from received chunks

### ServerFileManager

The server reads files from a restricted `resources/` directory and serves them in fixed-size chunks.

- Splits files into fixed-size chunks and serves them via sequence numbers
- Uses memory-mapped I/O (mmap) to enable efficient random access to file data, reducing repeated disk reads and improving performance during retransmissions


### ClientFileManager

The client reconstructs the file from incoming chunks and handles unreliable delivery.

- Writes data sequentially to disk based on expected sequence number
- Buffers out-of-order chunks instead of discarding for performance improvements during packet loss
    - Flushes buffered data once missing gaps are filled, ensuring in-order writes

### Design Considerations

Initially SHA-256 is being computed over the entire file at once when server is constructing FINISH packet and when client is verifying it's received file SHA-256 against server's. For large files, this introduced a significant delay leading to timeout on the opposite side due to lack of incoming packets from peer.

This was fixed by switching to incremental (per-chunk) hashing when server calls `get_chunk` and client calls `append_chunk`, allowing hashing to progress alongside normal data transmission with minimal added latency spike.

### Security 

- The file manager includes basic path validation (server-side) to prevent unauthorized file access and path traversal vulnerability

## Packet Layer

The [srft_packet.py](srft_packet.py) module implements the `SRFTPacket` class that is used across every layer of the protocol. It defines the wire format, provides builders for each opcode, handles encoding and decoding, computes the payload checksum, and exposes the AES-GCM encrypt and decrypt methods used after the handshake.

### Packet Structure

Each SRFT packet has a fixed 20-byte header followed by a variable-length payload. The header is packed with `struct` using `!B8sIIHH` in network byte order.

- `opcode` (1 byte) – packet type
- `session_id` (8 bytes) – ties the packet to the current security context
- `seq_number` (4 bytes) – data chunk sequence number
- `ack_number` (4 bytes) – cumulative in-order acknowledgement number
- `payload_length` (2 bytes) – length of the payload in bytes
- `checksum` (2 bytes) – 16-bit one's complement checksum over the payload

### Opcodes

The `Opcode` enum defines seven packet types. `CLIENT_HELLO` and `SERVER_HELLO` are plaintext handshake packets listed in `PLAINTEXT_OPCODES`. `REQUEST`, `TRANSMIT`, `ACKNOWLEDGE`, `FINISH`, and `NOT_FOUND` are encrypted protocol packets that flow once the handshake is complete.

### Packet Builders

Each opcode has its own factory method so packets are not constructed inline:

- `build_client_hello_packet` and `build_server_hello_packet` for the handshake
- `build_request_packet` for the filename request
- `build_transmit_packet` for a data chunk with its sequence number
- `build_ack_packet` for the cumulative acknowledgement
- `build_finish_packet` for the final SHA-256 digest
- `build_not_found_packet` for the file-missing response

All builders go through a private `__build_packet` so `payload_length` and the initial checksum stay consistent across packet types.

### Encoding and Decoding

`encode_packet` serializes a packet to bytes. It checks `is_valid()` first and raises `ValueError` if the packet is malformed, so invalid packets are never placed on the wire.

`decode_packet` parses raw bytes back into an `SRFTPacket`. The opcode decides whether the payload is treated as plaintext (handshake) or ciphertext (everything else). Encrypted packets still need a `decrypt()` call before the payload can be used.

### Checksum

`compute_checksum` implements a 16-bit one's complement checksum over the payload. It catches corruption that slipped past lower-layer checks and provides integrity for handshake packets that are not yet protected by AEAD.

### Encrypt and Decrypt

After the handshake, `encrypt` and `decrypt` connect the packet layer to `SecurityContext`.

- `opcode`, `session_id`, `seq_number`, and `ack_number` are packed with `!B8sII` and passed as Additional Authenticated Data, so tampering with any header field invalidates the AEAD tag.
- A fresh 12-byte nonce is generated for each encryption and prepended to the ciphertext. The payload on the wire is laid out as `[12-byte nonce][ciphertext + 16-byte GCM tag]`.
- `encrypt` updates the packet in place, filling `payload_ciphertext`, recomputing `payload_length` and `checksum`, and stamping the current `session_id` onto the packet.
- `decrypt` rejects packets whose `session_id` does not match the current security context and returns `False` on AEAD tag failure instead of raising.

### Design Considerations

- The header is not encrypted but is bound into each packet as AEAD AAD. This keeps opcodes, sequence numbers, and session IDs readable for early filtering while still detecting tampering.
- `payload_plaintext` and `payload_ciphertext` coexist on the same packet so one object can represent pre-encrypt, post-encrypt, and post-decrypt states. This avoids re-allocation on retransmissions and on replayed packets.

## Socket Layer

The [srft_socket.py](srft_socket.py) module wraps a raw socket with two helpers, `recv_one` and `send_one`, that exchange fully-parsed SRFT packets instead of raw bytes. This hides the IPv4 and UDP framing details from the state machines above it.

### SRFTSocket

`SRFTSocket` extends `socket.socket` and carries two fields:

- `ip` – the local IP used as the source IP for outgoing packets and as the destination filter for incoming packets
- `port` – the local port used the same way

Because the underlying socket is a raw socket, the kernel delivers every IPv4 packet seen on the interface. `recv_one` is responsible for narrowing that down to packets actually addressed to this application.

### recv_one

`recv_one` receives one raw IPv4 frame, validates it, and returns `(SRFTPacket, (src_ip, src_port))` on success or `None` on any failure. The packet is dropped if:

- the raw receive fails
- the IPv4 header cannot be parsed
- the protocol is not UDP
- the destination IP does not match `self.ip`
- the UDP header cannot be parsed
- the destination port does not match `self.port`
- the SRFT packet cannot be decoded from the UDP payload

Every failure returns `None` instead of raising, so the receive loop does not need per-iteration exception handling. Opcode validation, checksum verification, and AEAD authentication are done further up the stack.

### send_one

`send_one` takes an `SRFTPacket` and a destination `(ip, port)`, builds the full IPv4/UDP frame using `self.ip` and `self.port` as the source, and hands the raw bytes to the kernel. It returns the number of bytes sent.

### Threading

The server shares a single `SRFTSocket` across threads with a strict split:

- The main thread only calls `recv_one` to receive packets and dispatch work
- Handler threads only call `send_one` to transmit replies

This avoids contention between receive and send paths without needing an explicit lock around the socket. The client is single-threaded, so this split does not apply.

### get_local_ip

The module also exports `get_local_ip`, which is used by both the server and the client to obtain the LAN IP. It opens a throwaway UDP socket to `1.1.1.1:53` and reads `getsockname()` to discover the local IP. This is needed on AWS because the instance's public IP is NAT-translated and must not appear in outgoing IP headers. The instance's private IP is what goes on the wire.

## Threading Model

The server uses a main thread / worker thread model. The main thread effectively acts as a "router" for accepting new client connections, launching new `ServerThread` instances and dispatching incoming packets into the correct `ServerThread` via a queue. Each `ServerThread` accepts incoming packets via a queue instead of directly from the socket to avoid race-condition issues around reading from the shared socket. 

Each `ServerThread` corresponds cleanly to exactly one client session with its own `SecurityContext`, file handle, and server state machine instance in order to maximize isolation and aid per-client reasoning. 

Although in the current design, most heavy operations including file management or decryption are handle by the standalone `ServerThread` instance, the main thread is still effectively handling and performing basic parsing on every incoming packet in order to perform routing decisions. The limitations are manifested when multiple parallel clients are downloading large files, during which the main thread could be overloaded and become a bottleneck. A potential fix would require a significant rewrite, which ditches the central dispatch model and allow each worker thread create its own `SOCK_RAW` socket for both read and write operations. 

On the other hand, the client has a simple single-threaded model, but maintains similar code shape as the server for a neat state machine oriented approach. `ClientRunner` runs the state machine loop directly and has complete ownership over the socket, without the need for a packet queue like the server.

## Security Context

The `SecurityContext` class owns the entire cryptographic lifecycle for one transfer session. Each `ServerThread` or `ClientRunner` instance has a 1:1 relationship with a `SecurityContext` instance, which starts in an unestablished state and transitions to established after the handshake completes.

During the handshake, both sides exchange nonces and authenticate them with HMAC-SHA256 keyed by the PSK. After both hellos are verified, `derive_enc_key()` runs HKDF-SHA256 over the PSK salted with both nonces to produce a 32-byte AES-256-GCM key. Once the key is derived, `is_established()` returns `True` and the context is ready to use with simple `encrypt()` and `decrypt()` interfaces.

While AES-256-GCM is the only support cipher suite currently implemented, the `SecurityContext` abstraction allows for future extension to support additional protocols, and potentially a cipher suite negotiation phase between the client and the server during the handshake.

Each encrypted packet carries a fresh random 12-byte nonce with packet header fields are passed as AEAD authenticated data, which allows for pre-decryption packet unpacking (especially for the server's routing functionality) while still ensuring metadata integrity.

## Implemented Features

- Raw-socket-based SRFT transfer over UDP
- Explicit client/server state-machine handlers
- `CLIENT_HELLO` / `SERVER_HELLO` handshake
- PSK-based key derivation through HKDF
- AES-GCM packet encryption/decryption through `SecurityContext`
- Session-bound packet handling using `session_id`
- Sequence number and cumulative acknowledgement handling
- Receiver-side buffering for in-window out-of-order packets
- Duplicate and out-of-window packet dropping
- Timeout retransmission
- Duplicate-ACK-based fast retransmit
- Final SHA-256 verification on `FINISH`
- Correct handling of valid empty files
- Replay packet protection
- Path traversal protection

## Current Limitations

- The implementation prioritizes protocol correctness and clarity over aggressive performance optimization.
- Some retry and cleanup paths could still be simplified further.
- Replay protection and broader attack-hardening can still be improved.
- Larger-scale benchmark and stress testing can be expanded.
- `ClientFileManager` itself does not provide replay protection
    - Buffered chunks can be overwritten if duplicate or malicious packets are received
    - Replay protection is instead enforced at the state machine level to check whether chunk with a given sequence number exists in the buffer

## Lessons Learned

One major lesson from this project was that packet design, state transitions, reliability logic, and the security layer all depend on one another. A small change in protocol behavior can affect multiple modules at once. Keeping the packet layer, state machine, and final verification path aligned was important throughout development.

## Future Improvements

Possible future improvements include:

- simplifying the state-machine control flow
- reducing duplicated retry/cleanup logic
- expanding end-to-end testing around failure and recovery paths
- improving performance under larger workloads
- strengthening replay protection and attack-path validation


## Implementation and Test Results

### 1. Transfer Performances with Various Packet Loss Percentage on Various File Sizes

This section measure file transfer performances of the application with varying file size under different network packet loss percentage. All transfers were conducted on two AWS EC2 instances, one running `SRFT_UDPServer.py` and one running `SRFT_UDPClient.py`.

The baseline performance measurement is done with no artificial packet loss or delay imposed on server instance.

Table 1 shows transfer performances for five test files with varying sizes with no artificial packet loss or delay.

|  File Name  | Server Reports | Client Reports | Transfer Duration (h:mm:ss) |
|-------------|----------------|----------------|-----------------------------|
| test_10mb   | ![img](testing_results/Performance/0_pkt_loss_server_10mb.png)  | ![img](testing_results/Performance/0_pkt_loss_client_10mb.png) | 0:00:04 |
| test_100mb  | ![img](testing_results/Performance/0_pkt_loss_server_100mb.png) | ![img](testing_results/Performance/0_pkt_loss_client_100mb.png)| 0:00:40 |
| test_500mb  | ![img](testing_results/Performance/0_pkt_loss_server_500mb.png) | ![img](testing_results/Performance/0_pkt_loss_client_500mb.png)| 0:03:25 | 
| test_800mb  | ![img](testing_results/Performance/0_pkt_loss_server_800mb.png) | ![img](testing_results/Performance/0_pkt_loss_client_800mb.png)| 0:06:01 | 
| test_1gb    | ![img](testing_results/Performance/0_pkt_loss_server_1gb.png)   | ![img](testing_results/Performance/0_pkt_loss_client_1gb.png)  | 0:06:59 |
<p align="center"><em>Table 1 - Transfer Performances on various file sizes with 0% packet loss</em></p>

After baseline performance is measured, different packet loss percentage is simulated onto server instance using Linux `tc-netem` and same performance measurement was performed. Two different packet loss percentage was done as part of this measurement, `2%` and `4%`

Table 2 shows transfer performances for five test files with varying sizes with 2% artificial packet loss.

|  File Name  | Server Reports | Client Reports | Transfer Duration (h:mm:ss) |
|-------------|----------------|----------------|-----------------------------|
| test_10mb   | ![img](testing_results/Performance/2_pkt_loss_server_10mb.png)  | ![img](testing_results/Performance/2_pkt_loss_client_10mb.png) | 0:00:07 |
| test_100mb  | ![img](testing_results/Performance/2_pkt_loss_server_100mb.png) | ![img](testing_results/Performance/2_pkt_loss_client_100mb.png)| 0:01:13 |
| test_500mb  | ![img](testing_results/Performance/2_pkt_loss_server_500mb.png) | ![img](testing_results/Performance/2_pkt_loss_client_500mb.png)| 0:06:14 | 
| test_800mb  | ![img](testing_results/Performance/2_pkt_loss_server_800mb.png) | ![img](testing_results/Performance/2_pkt_loss_client_800mb.png)| 0:10:38 | 
| test_1gb    | ![img](testing_results/Performance/2_pkt_loss_server_1gb.png)   | ![img](testing_results/Performance/2_pkt_loss_client_1gb.png)  | 0:12:16 |
<p align="center"><em>Table 2 - Transfer Performances on various file sizes with 2% packet loss</em></p>

Table 3 shows transfer performances for five test files with varying sizes with 4% artificial packet loss.

|  File Name  | Server Reports | Client Reports | Transfer Duration (h:mm:ss) |
|-------------|----------------|----------------|-----------------------------|
| test_10mb   | ![img](testing_results/Performance/4_pkt_loss_server_10mb.png)  | ![img](testing_results/Performance/4_pkt_loss_client_10mb.png) | 0:00:07 |
| test_100mb  | ![img](testing_results/Performance/4_pkt_loss_server_100mb.png) | ![img](testing_results/Performance/4_pkt_loss_client_100mb.png)| 0:01:15 |
| test_500mb  | ![img](testing_results/Performance/4_pkt_loss_server_500mb.png) | ![img](testing_results/Performance/4_pkt_loss_client_500mb.png)| 0:06:31 | 
| test_800mb  | ![img](testing_results/Performance/4_pkt_loss_server_800mb.png) | ![img](testing_results/Performance/4_pkt_loss_client_800mb.png)| 0:11:12 | 
| test_1gb    | ![img](testing_results/Performance/4_pkt_loss_server_1gb.png)   | ![img](testing_results/Performance/4_pkt_loss_client_1gb.png)  | 0:13:30 |
<p align="center"><em>Table 3 - Transfer Performances on various file sizes with 4% packet loss</em></p>

### 2. Security Tests

This section test the application to ensure the implemented security features works correctly and safely under various attack-like conditions.

All the tests were done with 0% packet loss on the server instance.

#### Test 1 - Secure Transfer (Baseline)

A small image file was transferred through the network with security feature enabled.

Expected  behavior: Handshake = Success, AEAD auth failures = 0, Replay drops = 0, SHA-256 match = True.

|  File Name  |                      Server Report                            |                          Client Report                        |
|-------------|---------------------------------------------------------------|---------------------------------------------------------------|
| test_image.png   | ![img](testing_results/SecurityTest/Test1_server_report.png) | ![img](testing_results/SecurityTest/Test1_client_report.png) |
<p align="center"><em>Table 4 - Reports of transferring a small image file with security features enabled</em></p>

#### Test 2 - Wrong PSK (Authentication Failure)

This test will configure `SRFT_UDPClient` instance with different pre-shared key(PSK) than default PSK configured. 

Expected behavior: Handshake = Fail (connection rejected from server leading to timeout). No valid file output is produced.

![img](testing_results/SecurityTest/PSK.png)

|  File Name  |                      Server Report                            |                          Client Report                        |
|-------------|---------------------------------------------------------------|---------------------------------------------------------------|
| test_500mb & test_1gb  | ![img](testing_results/SecurityTest/Test2_server_report.png) | ![img](testing_results/SecurityTest/Test2_client_report.png) |
<p align="center"><em>Table 5 - Reports of attempting to transfer a file with different PSK configured at client</em></p>

#### Test 3 - Tamper Detection (Integrity)

This test will configure `SRFT_UDPServer` with `--attack tamper` flag to modify one in-transit DATA packet by performing bit flipping on 2 payload bits.

Expected behavior: Receiver drops the packet (AEAD authentication failure increments). Transfer completes correctly via retransmission with SHA-256 match = True.

![img](testing_results/SecurityTest/Tamper.png)

|  File Name  |                      Server Report                            |                          Client Report                        |
|-------------|---------------------------------------------------------------|---------------------------------------------------------------|
| test_500mb   | ![img](testing_results/SecurityTest/Test3_server_500mb.png) | ![img](testing_results/SecurityTest/Test3_client_500mb.png) |
| test_1gb   | ![img](testing_results/SecurityTest/Test3_server_1gb.png) | ![img](testing_results/SecurityTest/Test3_client_1gb.png) |
<p align="center"><em>Table 6 - Reports of transferring file with server configured to tamper one packet payload</em></p>

#### Test 4 - Replay Protection

This test will configure `SRFT_UDPServer` with `--attack replay` flag to capture one valid DATA packet and resend it later.

Expected behavior: Packet is rejected as duplicate/out-of-window (Replay drops and duplicate packet count increments). Transfer completes correctly and SHA-256 match = True.

![img](testing_results/SecurityTest/Replay.png)

|  File Name  |                      Server Report                            |                          Client Report                        |
|-------------|---------------------------------------------------------------|---------------------------------------------------------------|
| test_500mb   | ![img](testing_results/SecurityTest/Test4_server_500mb.png) | ![img](testing_results/SecurityTest/Test4_client_500mb.png) |
| test_1gb   | ![img](testing_results/SecurityTest/Test4_server_1gb.png) | ![img](testing_results/SecurityTest/Test4_client_1gb.png) |
<p align="center"><em>Table 7 - Reports of transferring file with server configured to capture and retransmit one valid packet</em></p>

#### Test 5 - Forged Injection

This test will configure `SRFT_UDPServer` with `--attack inject` flag to inject one forged random DATA packet and transmit it to client.

Expected behavior: Injected packet fails AEAD authentication and rejected (AEAD authentication failures count increments). Transfer completes correctly and SHA-256 match = True.

![img](testing_results/SecurityTest/Inject.png)

|  File Name  |                      Server Report                            |                          Client Report                        |
|-------------|---------------------------------------------------------------|---------------------------------------------------------------|
| test_500mb   | ![img](testing_results/SecurityTest/Test5_server_500mb.png) | ![img](testing_results/SecurityTest/Test5_client_500mb.png) |
| test_1gb   | ![img](testing_results/SecurityTest/Test5_server_1gb.png) | ![img](testing_results/SecurityTest/Test5_client_1gb.png) |
<p align="center"><em>Table 8 - Reports of transferring file with server configured to inject and transmit one forged packet</em></p>

## Docker Usage

| Container | IP Address | Reachable At |
|-----------|------------|--------------|
| srft-server | 172.16.0.2 | `srft-server.local` |
| srft-client | 172.16.0.3 | `srft-client.local` |
| srft-attacker | 172.16.0.1 via bridge |  |

- The project directory is mounted at `/srftproject` in all containers.
- `srft-server` has 4% packet loss pre-applied to it.
- `srft-attacker` uses `network_mode: host`. Similar to the SEED Labs setup, it can sniff all client-server traffic directly on the bridge interface.

```bash
# Start all containers
docker compose up -d
docker compose up -d --build

# Example interaction
docker exec -it srft-server /bin/bash
docker exec srft-client ping srft-server.local -c 20

# Stop all containers
docker compose down -t 1
```
