# Client-Server App

A simple client-server file transfer. Server stays up and listens for file uploads by clients. Client starts to send one file and then terminates.


## Usage

In one terminal:
``$ python server.py``

Then in a second terminal:
``$ python client.py path_to_file``
``$ python client.py path_to_file2``


## Configuration

The server expects a `server.conf` file with the following fields: `host, port, directory, log_level`

The client expects a `client.conf` file with the following fields: `server_host, server_port, log_level`


## Sending protocol

connect --> 8 bytes filename size --> N bytes filename --> 8 bytes filesize --> N bytes file contents


## Very basic test script

Use ``$ test.sh``


## Python version

Developed using Python 3.13.9 and Ubuntu WSL on Windows 11
