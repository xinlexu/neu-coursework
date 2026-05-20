import hashlib
import mmap
import os
import time

RESOURCES_DIR = "resources"

class ServerFileManager:
    """
    Manage open file pointer and return corresponding chunk for sending via network
    """
    @staticmethod
    def ensure_resources_dir():
        project_dir = os.path.dirname(os.path.abspath(__file__))
        resources_dir = os.path.join(project_dir, RESOURCES_DIR)
        if not os.path.isdir(resources_dir):
            raise FileNotFoundError(f"Server resources directory '{RESOURCES_DIR}' missing")

    def __init__(self, filename: str, chunk_size: int = 1400):
        self.filename = filename
        self.chunk_size = chunk_size
        
        project_dir = os.path.dirname(os.path.abspath(__file__))  # current file directory
        resources_dir = os.path.join(project_dir, RESOURCES_DIR)

        try:
            # Ensure the request file and path is inside resources dir
            file_path_maybe = os.path.abspath(os.path.join(resources_dir, filename))
            
            # Ensure candidate stays inside resources_dir
            if os.path.commonpath([resources_dir, file_path_maybe]) != resources_dir:
                raise ValueError("Path traversal detected")
            
            # Ensure it is a real file
            if not os.path.isfile(file_path_maybe):
                raise FileNotFoundError("File does not exist")
            
            self.full_path = file_path_maybe
            self.file = open(self.full_path, "rb")
            self.file_size = os.path.getsize(self.full_path)
            self.sha256 = hashlib.sha256()
            if self.file_size == 0:
                # File exists but is empty
                self.total_chunks = 0
                self.mm = None
                self.valid = True
                self.close()
            else:
                self.total_chunks = (self.file_size + chunk_size - 1) // chunk_size
                self.mm = mmap.mmap(self.file.fileno(), 0, access=mmap.ACCESS_READ)
                self.valid = True
                self._hashed_chunks = set()
        except (FileNotFoundError, OSError, ValueError):
            # File does not exist or cannot be opened
            self.file = None
            self.file_size = 0
            self.total_chunks = 0
            self.valid = False
            self.mm = None
            self.close()
    def file_is_valid(self) -> bool:
        return self.valid
    def get_chunk(self, seq_num: int) -> bytes:
        """
        Get data chunk bytes from given sequence number (1-indexed)
        The size of the chunks will be equal to self.chunk_size
        In the case of remaining chunks is smaller than chunk_size, return chunk of the remaining size
        """
        if seq_num < 1 or seq_num > self.total_chunks:
            raise ValueError(f"Invalid sequence number: {seq_num}")
        
        chunk_index = seq_num - 1

        offset = chunk_index * self.chunk_size
        actual_chunk_size = min(self.chunk_size, self.file_size - offset)
        
        data = self.mm[offset:offset + actual_chunk_size]
        
        # Update hash for sha256 once per chunk index
        if seq_num not in self._hashed_chunks:
            self.sha256.update(data)
            self._hashed_chunks.add(seq_num)
        return data
    def get_total_chunks(self) -> int:
        return self.total_chunks
    def get_file_size(self) -> int:
        return self.file_size
    def get_sha256(self) -> str:
        return self.sha256.hexdigest()
    def get_md5sum(self) -> str:
        if not self.valid:
            raise ValueError("Cannot compute MD5 for an invalid file")

        md5 = hashlib.md5()
        if self.mm is not None:
            chunk_size = 8192
            for offset in range(0, self.file_size, chunk_size):
                md5.update(self.mm[offset:offset + chunk_size])
        return md5.hexdigest()
    def close(self):
        if self.mm:
            self.mm.close()
            self.mm = None
        if self.file != None:
            self.file.close()
            self.file = None
            
class ClientFileManager:
    """
    Manages file chunks collection and buffering for receiveed file packets from network
    """
    def __init__(self, filename: str, chunk_size: int = 1400):
        project_dir = os.path.dirname(os.path.abspath(__file__))
        self.full_path = os.path.join(project_dir, "downloads", filename)

        os.makedirs(os.path.dirname(self.full_path), exist_ok=True)
        # Open file for writing binary
        self.file = open(self.full_path, "wb")
        # Next expected sequence (ACK number)
        self.expected_seq = 1
        # Buffer for out-of-order packets, use as dictonary: {seq_num: bytes}
        self.buffer = {}
        self.sha256 = hashlib.sha256()
    def append_chunk(self, seq_num: int, data: bytes) -> int:
        """
        Write incoming data to the output file at the offset specified by seq_num (1-indexed).
        If data arrives out of order (earlier bytes are missing),
        temporarily buffer it using seq_num as the key.
        Buffered segments are flushed to the file once all preceding data has been received.
        """
        # Duplicate or old packet, ignore
        if seq_num < self.expected_seq:
            return self.expected_seq
        # Store in buffer
        self.buffer[seq_num] = data
        # Try to flush consecutive chunks
        while self.expected_seq in self.buffer:
            chunk = self.buffer.pop(self.expected_seq)

            self.file.write(chunk)
            self.sha256.update(chunk)
            self.expected_seq += 1
        return self.expected_seq
    def close(self, valid: bool):
        if self.file:
            self.file.close()
            self.file = None
        # Delete partial file if invalid
        if not valid and self.full_path is not None:
            try:
                if os.path.isfile(self.full_path):
                    os.remove(self.full_path)
            except OSError:
                pass
    def get_file_size(self) -> int:
        self.file.flush()
        return os.path.getsize(self.full_path)
    def get_sha256(self) -> str:
        return self.sha256.hexdigest()
    def get_md5sum(self) -> str:
        if self.file is None:
            raise ValueError("Cannot compute MD5 for a closed file")
        
        self.file.flush()

        md5 = hashlib.md5()
        with open(self.full_path, "rb") as infile:
            while True:
                chunk = infile.read(8192)
                if not chunk:
                    break
                md5.update(chunk)

        return md5.hexdigest()
            
            
def test_server_file_mgr():
    # Test happy path
    file_mgr = ServerFileManager("test.txt", chunk_size = 1)
    with open(file_mgr.full_path, "rb") as infile:
        expected_sha256 = hashlib.sha256(infile.read()).hexdigest()
    assert file_mgr.file != None
    assert file_mgr.file_size == 6
    assert file_mgr.total_chunks == 6
    assert file_mgr.valid == True
    assert file_mgr.get_chunk(1) == b"a"
    assert file_mgr.get_chunk(3) == b"c"
    assert file_mgr.get_sha256() == expected_sha256
    file_mgr.close()
    print("File Manager Happy path test success")
    file_mgr = ServerFileManager("Fake.txt")
    assert file_mgr.file == None
    assert file_mgr.file_size == 0
    assert file_mgr.total_chunks == 0
    assert file_mgr.valid == False
    print("File Manager File not found path test success")
    file_mgr.close()
    
    
def test_file_transfer_and_collection():
    srv_file_mgr = ServerFileManager("test.txt", chunk_size = 2)
    cli_file_mgr = ClientFileManager("recv.txt", chunk_size = 2)
    first_chunk = srv_file_mgr.get_chunk(1)
    second_chunk = srv_file_mgr.get_chunk(2)
    third_chunk = srv_file_mgr.get_chunk(3)
    # Test with out-of-order chunk and duplicate chunk
    cli_file_mgr.append_chunk(1, first_chunk)
    cli_file_mgr.append_chunk(3, third_chunk)
    cli_file_mgr.append_chunk(1, first_chunk)
    cli_file_mgr.append_chunk(2, second_chunk)
    
    # Buffer should be empty now
    assert len(cli_file_mgr.buffer) == 0
    assert cli_file_mgr.get_sha256() == srv_file_mgr.get_sha256()
    
    # Assert both file contents
    with open(srv_file_mgr.full_path, "rb") as a, open(cli_file_mgr.full_path, "rb") as b:
        assert a.read() == b.read()

    srv_file_mgr.close()
    cli_file_mgr.close(True)
    for _ in range(5):
        try:
            os.remove(cli_file_mgr.full_path)
            break
        except PermissionError:
            time.sleep(0.05)
    
    
if __name__ == "__main__":
    test_server_file_mgr()
    test_file_transfer_and_collection()
    
        
