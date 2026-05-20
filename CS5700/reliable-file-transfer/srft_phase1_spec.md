# SRFT Phase 1 Spec

### 1. Packet Types
- REQUEST
- TRANSMIT
- ACKNOWLEDGE
- FINISH

### 2. SRFT Header Fields
- opcode
- seq_number
- ack_number
- payload_length
- checksum

### 3. Payload
- REQUEST: filename bytes
- TRANSMIT: file chunk bytes
- ACKNOWLEDGE: empty
- FINISH: empty

### 4. Notes
- opcode = packet type
- seq_number = current packet sequence number
- ack_number = highest contiguous in-order TRANSMIT packet received so far
- payload_length = payload bytes only
- checksum = corruption check

### 5. Rules
- The client sends REQUEST with the filename in the payload.
- The server sends TRANSMIT packets with file chunks.
- The sender uses a small fixed sender window.
- The client uses cumulative ACK.
- ack_number represents the highest contiguous in-order TRANSMIT packet received so far.
- The sender retransmits on timeout.
- Sequence numbers are used for duplicate detection and re-order handling.
- The client may keep limited out-of-order packets within a small receiver window.
- ACK generation is cumulative and is not tied to every single received TRANSMIT packet.

### 6. Initial Design Choices
- REQUEST seq_number = 0
- REQUEST ack_number = 0
- The first TRANSMIT packet uses seq_number = 1.
- ACKNOWLEDGE uses ack_number to indicate the highest contiguous in-order packet received.
- payload_length does not include SRFT, IP, or UDP headers.
- sender_window_size is a small fixed value chosen by the implementation.
- receiver_window_size is a small fixed value chosen by the implementation.
- ack_delay_interval is a small fixed value chosen by the implementation.
- ack_batch_threshold is a small fixed value chosen by the implementation.
- A single ACKNOWLEDGE may cumulatively cover multiple TRANSMIT packets.

### 7. Header Layout
- Field order:
  1) opcode
  2) seq_number
  3) ack_number
  4) payload_length
  5) checksum

- Field size:
  - opcode: 1 byte
  - seq_number: 4 bytes
  - ack_number: 4 bytes
  - payload_length: 2 bytes
  - checksum: 2 bytes

- Byte order:
  - big-endian

- Total SRFT header size:
  - 13 bytes

### 8. Opcode Values
- REQUEST = 1
- TRANSMIT = 2
- ACKNOWLEDGE = 3
- FINISH = 4

### 9. Phase 1 State Machine

**Client States**
- CLIENT_INIT
- CLIENT_SEND_REQUEST
- CLIENT_WAIT_PACKET
- CLIENT_PROCESS_TRANSMIT
- CLIENT_SEND_ACK
- CLIENT_CLEANUP
- CLIENT_COMPLETE

**Server States**
- SERVER_INIT
- SERVER_WAIT_REQUEST
- SERVER_PREPARE_FILE
- SERVER_SEND_TRANSMIT
- SERVER_WAIT_ACK_OR_TIMEOUT
- SERVER_SEND_FINISH
- SERVER_CLEANUP
- SERVER_COMPLETE


### 10. Client State Behavior

**Client Transitions**
```
- CLIENT_INIT -> CLIENT_SEND_REQUEST
  - Start client
  - Initialize expected_seq = 1

- CLIENT_SEND_REQUEST -> CLIENT_WAIT_PACKET
  - Send REQUEST with filename in the payload

- CLIENT_WAIT_PACKET -> CLIENT_PROCESS_TRANSMIT
  - Receive a TRANSMIT packet

- CLIENT_WAIT_PACKET -> CLIENT_SEND_ACK
  - ack_deadline has expired
  - socket timeout

- CLIENT_WAIT_PACKET -> CLIENT_CLEANUP
  - Receive a FINISH packet

- CLIENT_PROCESS_TRANSMIT -> CLIENT_SEND_ACK
  - If ack_batch_count >= ack_batch_threshold, or
  - duplicate/out-of-order/outside-window packet received, or
  - ack_deadline has expired

- CLIENT_PROCESS_TRANSMIT -> CLIENT_WAIT_PACKET
  - If no immediate ACK trigger and ack_deadline not expired

- CLIENT_SEND_ACK -> CLIENT_WAIT_PACKET
  - Send ACKNOWLEDGE
  - ack_number = last_in_order
  - Reset ack_batch_count, clear ack_deadline

- CLIENT_CLEANUP -> CLIENT_COMPLETE
  - Close output file, mark transfer_success = True

- CLIENT_COMPLETE
  - Terminal state — no handler, run loop exits
```

**CLIENT_INIT**
- Create raw socket
- Initialize output file
- Initialize expected_seq = 1
- Initialize transfer_success = False
- Initialize last_in_order = 0
- Initialize buffered_packets = empty
- Initialize receiver_window_size
- Initialize ack_batch_count = 0
- Initialize ack_batch_threshold
- Initialize ack_delay_interval
- Initialize ack_deadline = None

**CLIENT_SEND_REQUEST**
- Build REQUEST packet
- Set opcode = REQUEST
- Set seq_number = 0
- Set ack_number = 0
- Set payload = filename bytes
- Set payload_length = length of filename bytes
- Compute checksum
- Send packet to server

**CLIENT_WAIT_PACKET**
- Wait for an incoming packet from the server (use time until ack_deadline as socket timeout if set)
- If socket times out (no packet received before ack_deadline), move to CLIENT_SEND_ACK
- If packet type is TRANSMIT, move to CLIENT_PROCESS_TRANSMIT
- If packet type is FINISH, move to CLIENT_COMPLETE
- Ignore unknown packet types

**CLIENT_PROCESS_TRANSMIT**
- Verify checksum
- If checksum is invalid:
  - Drop packet
  - Go back to CLIENT_WAIT_PACKET
- If seq_number == expected_seq:
  - Accept payload
  - Store payload
  - Advance expected_seq
  - If the next expected packets are already buffered:
    - write all newly contiguous buffered data in order
    - continue advancing expected_seq
  - Set last_in_order = expected_seq - 1
  - Increase ack_batch_count
  - If ack_deadline is None:
    - set ack_deadline = now + ack_delay_interval
- If seq_number < expected_seq:
  - Treat packet as duplicate
  - Do not write payload again
- If seq_number > expected_seq and seq_number is within the receiver window:
  - Treat packet as out-of-order
  - Buffer payload
  - Do not write it yet
  - Do not advance last_in_order
- If seq_number is outside the receiver window:
  - Ignore payload
- After processing:
  - If ack_batch_count >= ack_batch_threshold, or
    a duplicate packet was received, or
    an out-of-order packet was received, or
    an outside-window packet was received, or
    ack_deadline is not None and ack_deadline has expired
    then move to CLIENT_SEND_ACK
  - Otherwise go back to CLIENT_WAIT_PACKET

**CLIENT_SEND_ACK**
- Build ACKNOWLEDGE packet
- Set opcode = ACKNOWLEDGE
- Set seq_number = 0
- Set ack_number = last_in_order
- Set payload = empty
- Set payload_length = 0
- Compute checksum
- Send ACK to server
- Reset ack_batch_count = 0
- Clear ack_deadline
- Go back to CLIENT_WAIT_PACKET

**CLIENT_CLEANUP**
- Mark transfer_success = True
- Close output file
- Transition to CLIENT_COMPLETE

**CLIENT_COMPLETE**
- Terminal state — no handler, run loop exits

### 11. Server State Behavior

**Server Transitions**

```
- SERVER_INIT -> SERVER_WAIT_REQUEST
  - Start server
  - Wait for client request

- SERVER_WAIT_REQUEST -> SERVER_PREPARE_FILE
  - Receive a valid REQUEST packet
  - Extract filename from the payload

- SERVER_PREPARE_FILE -> SERVER_SEND_TRANSMIT
  - Open file
  - Set next_seq_to_send = 1

- SERVER_SEND_TRANSMIT -> SERVER_WAIT_ACK_OR_TIMEOUT
  - Send one or more TRANSMIT packets while:
    - next_seq_to_send <= total_chunks
    - next_seq_to_send < last_acknowledged + 1 + sender_window_size

- SERVER_WAIT_ACK_OR_TIMEOUT -> SERVER_SEND_TRANSMIT
  - Receive a valid ACKNOWLEDGE
  - If ack_number > last_acknowledged:
    - Set last_acknowledged = ack_number
    - If all file chunks are cumulatively acknowledged:
      - Move to SERVER_SEND_FINISH
    - Else if unsent chunks remain AND the sender window now has space:
      - Move to SERVER_SEND_TRANSMIT

- SERVER_WAIT_ACK_OR_TIMEOUT -> SERVER_WAIT_ACK_OR_TIMEOUT
  - Receive an old or duplicate ACKNOWLEDGE
  - Ignore it and continue waiting

- SERVER_WAIT_ACK_OR_TIMEOUT -> SERVER_SEND_TRANSMIT
  - Timeout with retry_count < max_retries
  - Increment retry_count
  - Reset next_seq_to_send = last_acknowledged + 1

- SERVER_WAIT_ACK_OR_TIMEOUT -> SERVER_CLEANUP
  - Timeout with retry_count >= max_retries (give up)

- SERVER_WAIT_ACK_OR_TIMEOUT -> SERVER_SEND_FINISH
  - All file chunks have been cumulatively acknowledged

- SERVER_SEND_FINISH -> SERVER_CLEANUP
  - Send FINISH

- SERVER_CLEANUP -> SERVER_COMPLETE
  - Close file, record end time, output report

- SERVER_COMPLETE
  - Terminal state, thread exits
```

**SERVER_INIT**
- Create raw socket
- Initialize transfer state
- Initialize next_seq_to_send = 1
- Initialize last_acknowledged = 0
- Initialize sender_window_size
- Initialize transfer_success = False

**SERVER_WAIT_REQUEST**
- Wait for an incoming packet from the client
- If packet type is REQUEST:
  - Verify checksum
  - If checksum is valid:
    - Extract filename from payload
    - Move to SERVER_PREPARE_FILE
- Ignore other packet types

**SERVER_PREPARE_FILE**
- Open the requested file
- Split file into chunks
- Store chunks in order
- Set total_chunks
- Set next_seq_to_send = 1
- Move to SERVER_SEND_TRANSMIT

**SERVER_SEND_TRANSMIT**
- While the sender window has available space and unsent chunks remain:
  - Build TRANSMIT packet for next_seq_to_send
  - Set opcode = TRANSMIT
  - Set seq_number = next_seq_to_send
  - Set ack_number = 0
  - Set payload = file chunk bytes
  - Set payload_length = length of file chunk bytes
  - Compute checksum
  - Send packet to client
  - Set next_seq_to_send = next_seq_to_send + 1
- Move to SERVER_WAIT_ACK_OR_TIMEOUT

**SERVER_WAIT_ACK_OR_TIMEOUT**
- Wait for ACKNOWLEDGE or timeout
- If ACKNOWLEDGE is received:
  - Verify checksum
  - If checksum is valid:
    - Read ack_number
    - If ack_number > last_acknowledged:
      - Set last_acknowledged = ack_number
          - If all chunks are acknowledged:
        - Move to SERVER_SEND_FINISH
      - Else if the sender window now has available space:
        - Move to SERVER_SEND_TRANSMIT
      - Else:
        - Continue waiting
    - If ack_number <= last_acknowledged:
      - Ignore duplicate or old ACK
      - Continue waiting
- If timeout happens:
  - Increment retry_count
  - If retry_count >= max_retries: move to SERVER_CLEANUP
  - Else: set next_seq_to_send = last_acknowledged + 1, move to SERVER_SEND_TRANSMIT

**SERVER_SEND_FINISH**
- Build + Send FINISH packet
- Move to SERVER_CLEANUP

**SERVER_CLEANUP**
- Close file (if open)
- Record transfer end time
- Output server report
- Move to SERVER_COMPLETE

**SERVER_COMPLETE**
- Terminal state, thread exits

### 12. ACK and Retransmission Rules

**ACK Rules**
- The client uses cumulative ACKNOWLEDGE packets.
- ack_number means the highest contiguous in-order TRANSMIT seq_number received so far.
- ACK generation is event-driven and cumulative.
- The client must not generate one ACKNOWLEDGE for every single TRANSMIT packet by default.
- A single ACKNOWLEDGE may cumulatively cover multiple newly received in-order TRANSMIT packets.
- The client sends ACKNOWLEDGE when receiver state needs to be reported, including:
  - when ack_delay_interval expires after contiguous progress
  - when ack_batch_threshold is reached
  - when a duplicate packet is received
  - when an out-of-order packet is received
  - when an outside-window packet is received
- The client does not advance ack_number unless the received data becomes contiguous from the current expected_seq.

**Cumulative ACK**
- If packets 1, 2, and 3 have been received in order, then ack_number = 3.
- If packets 1 and 2 arrive and ACK is delayed, one ACKNOWLEDGE with ack_number = 2 may cover both packets.
- If packet 5 arrives before packet 4, then ack_number stays at 3.
- If packet 4 later arrives and packet 5 was already buffered, then ack_number advances to 5.
- Duplicate packets do not change ack_number.

**Checksum Handling**
- If a received packet fails checksum verification, the receiver drops it.
- A corrupted TRANSMIT packet is not accepted and is not written to file.
- A corrupted ACKNOWLEDGE packet is ignored by the sender.

**Retransmission Rules**
- The sender waits for timeout_interval in SERVER_WAIT_ACK_OR_TIMEOUT.
- If no valid cumulative ACKNOWLEDGE is received before timeout, the sender retransmits the unacknowledged packets starting from last_acknowledged + 1.
- A retransmitted packet keeps the same seq_number and payload.
- The sender gives up after max_retries consecutive timeouts.

**Duplicate and Out-of-Order Handling**
- If the client receives a duplicate TRANSMIT packet, it does not write the payload again.
- If the client receives an out-of-order TRANSMIT packet within the receiver window, it may buffer the payload but does not write it until the missing earlier packets arrive.
- If the client receives an out-of-window TRANSMIT packet, it ignores the payload.
- In duplicate, out-of-order, and outside-window cases, the client sends ACKNOWLEDGE with the current last_in_order value.

**Finish Rule**
- The server sends FINISH only after all file chunks have been cumulatively acknowledged.
- The client completes the transfer after receiving FINISH.

### 13. Sender and Receiver Variables

**Client Variables**
- expected_seq
  - The next seq_number the client expects to receive
  - Initial value: 1

- last_in_order
  - The highest contiguous in-order TRANSMIT seq_number received so far
  - Initial value: 0

- buffered_packets
  - A limited buffer for out-of-order TRANSMIT packets within the receiver window

- receiver_window_size
  - The size of the limited receiver window

- ack_batch_count
  - The number of newly covered in-order packets since the last ACKNOWLEDGE

- ack_batch_threshold
  - The fixed threshold that can trigger ACKNOWLEDGE generation

- ack_delay_interval
  - The fixed ACK delay used to avoid one ACK per TRANSMIT

- ack_deadline
  - The time when the pending ACK should be sent if no earlier trigger happens

- output_file
  - The destination file used to store received data

- server_address
  - The source address used to receive packets and send ACKs

**Server Variables**
- next_seq_to_send
  - The next new seq_number that has not been sent yet
  - Initial value: 1

- last_ack
  - The highest cumulatively acknowledged seq_number
  - Initial value: 0

- sender_window_size
  - The size of the fixed sender window

- file_handle
  - file data split into ordered chunks
  - total number of file chunks to send

- timeout_interval
  - The retransmission timeout value

- retry_count
  - The number of consecutive timeouts without progress
  - Reset to 0 on valid ACK
  - Initial value: 0

- max_retries
  - The maximum number of consecutive timeouts before giving up

- client_address
  - The destination address used to send TRANSMIT and FINISH packets

### 14. Phase 1 Assumptions and Scope

**Scope**
- This specification describes the Phase 1 baseline only.
- Phase 1 focuses on reliable file transfer over UDP using raw sockets.
- Security features are not included in this Phase 1 specification.

**Phase 1 Assumptions**
- The Phase 1 baseline uses a small fixed sender window instead of strict stop-and-wait.
- The sender may transmit multiple TRANSMIT packets within the configured sender window before receiving acknowledgements.
- The timeout interval uses a fixed value.
- ack_delay_interval uses a fixed small value.
- ACKNOWLEDGE packets use empty payload.
- FINISH packets use empty payload.
- The client uses cumulative ACKNOWLEDGE packets.
- The client may keep limited out-of-order packets within a small receiver window.
- Out-of-order packets are not written to file until the missing earlier packets arrive and the data becomes contiguous.
- Duplicate packets are not written again.
- The file is split into ordered chunks before transmission.
- The receiver writes data only when the received data becomes contiguous from the current expected_seq.

**Out of Scope for Phase 1**
- PSK handshake
- HKDF key derivation
- AES-GCM or other AEAD protection
- Replay protection beyond basic duplicate handling
- Final SHA-256 verification for the secure version
- Dynamic or adaptive window sizing
- Congestion control
- Selective acknowledgement extensions
- Fast retransmit or fast recovery
- Receiver buffering beyond the small fixed receiver window baseline

**Validation Goal**
- The goal of Phase 1 is reliable transfer with checksum, sequence number, cumulative acknowledgement, and timeout retransmission.
- The received file should match the original file.

### 15. Phase 2 Extension: Final SHA-256 Verification

**Spec File**
- This file also records the minimal Phase 2 protocol extension for final SHA-256 verification.

**Phase 2 Message Flow**
- The client sends REQUEST with the requested filename.
- The server sends TRANSMIT packets until the full file has been cumulatively acknowledged.
- After all file chunks are acknowledged, the server computes the SHA-256 of the source file.
- The server sends FINISH with the SHA-256 hex digest in `FINISH.payload`.
- The client computes the SHA-256 of the received file after all data chunks have been written.
- The client compares the local SHA-256 against the SHA-256 received in `FINISH.payload`.
- If the digests match, the client sends the final ACKNOWLEDGE for FINISH and marks the transfer successful.
- If the digests do not match, or the FINISH payload is not a valid SHA-256 hex digest, the client treats final verification as failed and does not mark the transfer successful.

**Phase 2 Notes**
- Phase 2 reuses the existing FINISH message instead of adding a new opcode.
- For Phase 2, `FINISH.payload` contains a 64-character ASCII hex SHA-256 digest.
- This Phase 2 extension covers final file verification only.
- Session ID handling, payload plaintext/ciphertext splitting, AEAD, PSK, HKDF, replay detection, and related secure-session features remain outside this minimal Phase 2 extension.
