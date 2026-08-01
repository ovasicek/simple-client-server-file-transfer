from pathlib import Path
import argparse
import socket
import json
from utils import Logger

# HARD CODED CONSTANTS
PATH_TO_CONFIG = 'client.conf'  # path to conf file
CHUNK_SIZE = 1024               # data is sent in chunks


# Class to hold client configuration
class Config:
    def __init__(self, server_host, server_port, log_level):
        self.server_host = server_host
        self.server_port = server_port
        self.log_level = log_level


# Load JSON configuration file
# Expected fields: server_host, server_port, log_level
def load_config():
    with open(PATH_TO_CONFIG, 'r') as config_file:
        config = json.load(config_file)
    return Config(
        server_host=config['server_host'],
        server_port=config['server_port'],
        log_level=config['log_level']
    )


# Process command line arguments to get file path and filename
def process_args():
    parser = argparse.ArgumentParser(description='Send a file to the server')
    parser.add_argument('file_path', help='The source file to send')
    arguments = parser.parse_args()
    return [arguments.file_path, Path(arguments.file_path).name]


# The main client class
class Client:
    # Constructor establishes a connection to the server
    def __init__(self, config, logger):
        self.server_host = config.server_host
        self.server_port = config.server_port
        self.logger = logger
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_socket.connect((self.server_host, self.server_port))
        self.logger.log(f"Connected to server at {self.server_host}:{self.server_port}")

    # Destructor closes connection to the server
    def __del__(self):
        self.client_socket.close()
        self.logger.log(f"Connection closed", "DEBUG")
    
    # Counts the number of chunks that will be sent based on the file size
    def __count_chunks(self, file_size):
        num_chunks = file_size // CHUNK_SIZE
        if file_size % CHUNK_SIZE:
            num_chunks += 1
        return num_chunks
    
    # The byte sending loop for a file
    def __send_file_in_chunks(self, file, num_chunks):
        progress = ProgressBar(num_chunks)
        data = file.read(CHUNK_SIZE)
        while data:
            self.client_socket.sendall(data)
            self.logger.log(f"Sending chunk: {len(data)} bytes", "DEBUG")
            progress.update()
            data = file.read(CHUNK_SIZE)
        progress.complete()
    
    # Send a file to the server using our protocol
    # The protocol is:
    #   8 bytes filename size
    #   N bytes filename
    #   8 bytes filesize
    #   N bytes file contents
    def send_file(self, filename, file_path):
        with open(file_path, 'rb') as file:
            filename_byte_size = len(filename.encode())
            
            # Send filename size to server
            self.client_socket.sendall(filename_byte_size.to_bytes(8, byteorder='big'))
            self.logger.log(f"Sent filename size to server: {filename_byte_size}", "DEBUG")
            
            # Send filename to server
            self.client_socket.sendall(filename.encode())
            self.logger.log(f"Sent filename to server: {filename}", "DEBUG")

            # check file size and count chunks
            file_size = Path(file_path).stat().st_size
            num_chunks = self.__count_chunks(file_size)

            # Send file size to server
            self.client_socket.sendall(file_size.to_bytes(8, byteorder='big'))
            self.logger.log(f"Sent file size to server: {file_size}", "DEBUG")
            
            # Send file data to server (unless file is empty)
            if file_size != 0:
                self.__send_file_in_chunks(file, num_chunks)
            
            self.logger.log(f"File sending complete: {file_path}")


# A visual progress bar for the file transfer
# Looks like this:
# Sending: |████████████████████████████████████| 100.00%
class ProgressBar:
    def __init__(self, total_chunks, width=40):
        self.total_chunks = total_chunks
        self.current_chunk = 0
        self.width = width

    # Redraw the progress bar in the console and increment the current chunk number
    def update(self):
        self.current_chunk += 1
        if self.total_chunks == 0:
            progress = 1.0
        else:
            progress = self.current_chunk / self.total_chunks   # percentage to fill
        filled = int(self.width * progress)                     # percentage to number of filled characters
        bar = "█" * filled + "-" * (self.width - filled)        # filled characters + the rest of the bar
        print(f"\rSending: |{bar}| {progress * 100:6.2f}%", end="", flush=True)

    # Complete the progress bar when done
    def complete(self):
        print()  # Move to the next line


# ===============================================================================
if __name__ == '__main__':
    
    # Initialize and parse command line arguments
    logger = Logger("INFO")
    file_path, filename = process_args()
    
    # Check the file
    if not (Path(file_path).exists() and Path(file_path).is_file()):
        logger.log(f"Invalid file: {file_path}", "ERROR")
        exit(1)
    
    # Load configuration
    try:
        config = load_config()
        logger = Logger(config.log_level)
        logger.log(f"Configuration loaded: {config.__dict__}", "DEBUG")
    except Exception as e:
        logger.log(f"Failed to load configuration: {e}", "ERROR")
        exit(1)
    
    # Send the file
    try:
        client = Client(config, logger)
        client.send_file(filename, file_path)
    except Exception as e:
        logger.log(f"Failed to send file: {e}", "ERROR")
        exit(1)
    
    