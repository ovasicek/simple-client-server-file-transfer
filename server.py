from pathlib import Path
import socket
import json
from utils import Logger

# HARD CODED CONSTANTS
PATH_TO_CONFIG = 'server.conf'  # path to conf file
CHUNK_SIZE = 1024               # data is received in chunks

# Class to hold server configuration
class Config:
    def __init__(self, host, port, directory, log_level):
        self.host = host
        self.port = port
        self.directory = directory
        self.log_level = log_level


# Load JSON configuration file
# Expected fields: host, port, directory, log_level
def load_config():
    with open(PATH_TO_CONFIG, 'r') as config_file:
        config = json.load(config_file)
    return Config(
        host=config['host'],
        port=config['port'],
        directory=config['directory'],
        log_level=config['log_level']
    )


# The main server class
class Server:
    def __init__(self, config, logger):
        self.host = config.host
        self.port = config.port
        self.directory = config.directory
        self.logger = logger
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen(5)
        self.logger.log(f"Server started on {self.host}:{self.port}")
        
    def __del__(self):
        self.server_socket.close()
        self.logger.log(f"Server socket closed", "DEBUG")
    
    # Implementation of "recvall" to ensure we receive the exact number of bytes requested
    def recv_exact(self, sock, size):
        data = bytearray()

        while len(data) < size:
            chunk = sock.recv(size - len(data))
            if not chunk:
                raise ConnectionError("Connection closed")
            data.extend(chunk)

        return bytes(data)

    def start(self):
        while True:
            try:
                connection, client_addr = self.server_socket.accept()
                self.logger.log(f"Connection from {client_addr}")
            except Exception as e:
                self.logger.log(f"Failed to connect: {e}", "ERROR")
                continue
            
            try:
                # Receive filename size from client
                filename_byte_size = int.from_bytes(self.recv_exact(connection, 8), byteorder='big')
                self.logger.log(f"Received filename_byte_size from {client_addr}: {filename_byte_size}", "DEBUG")
                
                # Receive filename from client
                data = self.recv_exact(connection, filename_byte_size)
                filename = data.decode()
                filename = Path(filename).name  # sanitize the filename to avoid directory traversal
                self.logger.log(f"Received filename from {client_addr}: {filename}", "DEBUG")
                
                # Form the filepath and rename if duplicate
                filepath = Path(self.directory) / filename
                while filepath.exists():
                    # Generate a new filename
                    self.logger.log(f"File already exists: {filepath}", "DEBUG")
                    filepath = filepath.with_stem(filepath.stem + "_copy")
                    self.logger.log(f"Renaming to: {filepath}", "DEBUG")
                
                # Receive file size from client
                file_size = int.from_bytes(self.recv_exact(connection, 8), byteorder='big')
                self.logger.log(f"Received file size from {client_addr}: {file_size}", "DEBUG")
                
                if file_size != 0:
                    # Receive data from client in chunks and write them to file
                    with open(filepath, 'wb') as file:
                        remaining = file_size
                        while remaining:
                            data = connection.recv(min(CHUNK_SIZE,remaining))
                            if not data:
                                if filepath.exists():
                                    filepath.unlink()  # delete the incomplete file
                                raise ConnectionError("Connection closed")
                            self.logger.log(f"Received data from {client_addr}: {len(data)} bytes", "DEBUG")
                            file.write(data)
                            remaining -= len(data)
                            
                else:   # create empty file
                    filepath.touch()
                    
                self.logger.log(f"File receiving complete: {filepath.name}")
                        
            except Exception as e:
                self.logger.log(f"Failed to receive file from {client_addr}: {e}", "ERROR")
            finally:
                connection.close()
                self.logger.log(f"Connection with {client_addr} closed", "DEBUG")



# ===============================================================================
if __name__ == '__main__':
    logger = Logger("INFO")
    try:
        config = load_config()
        logger = Logger(config.log_level)
        logger.log(f"Configuration loaded: {config.__dict__}", "DEBUG")
    except Exception as e:
        logger.log(f"Failed to load configuration: {e}", "ERROR")
        exit(1)

    # check that the directory to save files to exists
    if not Path(config.directory).exists():
        logger.log(f"File directory does not exist, creating...: {config.directory}", "WARNING")
        Path(config.directory).mkdir(parents=True)

    # start the server
    server = Server(config, logger)
    server.start()
