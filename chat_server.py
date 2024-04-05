import argparse
import signal
import sys

import socket
import threading
import json
import selectors 

import resources
from buffer import Buffer

# Networking configuration
# (Default values if user did not pass in any parameters)
PORT = 12345         # Arbitrary non-privileged port number

'''
    Parse command line arguments
'''
def parse_args():
    parser = argparse.ArgumentParser(description='Compress or decompress files using LZW algorithm')
    parser.add_argument('-p', '--port', type=int, metavar="{1024..49151}", default=PORT, help='The port number in the range 1024-49151.')
    parser.add_argument('-l', '--log', default=argparse.SUPPRESS, action='store_true', help='Whether all communications are logged.')
    return parser.parse_args(), parser.print_help

# Define the ChatServer class to manage chat rooms and client connections
class ChatServer:
    # Initialize the ChatServer with a host address and a port number
    def __init__(self, host, port, show_log:bool=False):
        # Settings
        self.show_log = show_log

        # Create a socket and bind it to the host and port, then start listening for connections
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen()

        # Buffer
        self.buffers = dict()

        # Dictionary to keep track of chat rooms and their participants
        self.chat_rooms = dict()  # Format: {room_name: [client_sockets,...]}

        # List to keep track of active requests
        self.requests = set()

        print('Initializing Chat Server at IP [{}] and port [{}]'.format(*self.get_ip()))
        
    # Get the IP address of the server
    def get_ip(self):
        '''Output Format: (IPv4 address, port)'''
        ip = list(self.server_socket.getsockname())
        if ip[0] == '127.0.0.1':
            ip[0] = socket.gethostbyname(socket.gethostname())
        return ip

    # Handle incoming messages from clients
    def handle_client(self, client_socket):
        while True:
            try:
                # Receive and decode a message, then parse it as JSON
                self.buffers[client_socket].read(socket=client_socket, handler=self.handle_listener)
                # message = client_socket.recv(4096).decode('utf-8')
                # if message:
                #     self.handle_listener(self, message, client_socket)

            # On socket error, close the client's connection
            except socket.error:
                try:
                    self.requests.remove(client_socket)
                    print('Error. Ended request from: %s port %s' % client_socket.getpeername())
                    client_socket.close()
                    return
                except Exception:
                    return
                
    # Handler
    def handle_listener(self, message, client_socket):
        try: 
            command = message#json.loads(message)
        except Exception as e:
            self.log(message+'\n'+e, mode='E/error', socket=client_socket)
            return
        if command['action'] != 'voice':
            self.log(command, mode=f"I/{command['action']}", socket=client_socket)
        # Execute the appropriate action based on the command received
        if command['action'] == 'create':
            self.create_room(command['room'], client_socket)
        elif command['action'] == 'list':
            self.list_rooms(client_socket)
        elif command['action'] == 'join':
            self.join_room(command['room'], client_socket, command['old_room'])
        elif command['action'] == 'exit':
            self.remove_client(client_socket, command['room_name'])
            self.requests.remove(client_socket)
            print('Ended request from: %s port %s' % client_socket.getpeername())
            client_socket.close()
            return
        elif command['action'] == 'voice':
            self.voice(command, client_socket) # fyi, command structure is in send_audio_thread
    
    # remove client from room if client exits
    def remove_client(self, client_socket, room_name):
        if room_name:
            self.chat_rooms[room_name].remove(client_socket)

    # receive voice from user and send voice to other user
    def voice(self, command, client_socket):
        # print(f'audio data:{command["audio_data"]}')
        room_name = command['room_name']
        for other_user in self.chat_rooms[room_name]:
            if other_user != client_socket:
                self.send_data(other_user, label='voice', contents={'audio_data': command['audio_data']})

    # Create a new chat room or inform the host if it already exists
    def create_room(self, room_name, host_socket):
        if room_name not in self.chat_rooms:
            self.chat_rooms[room_name] = []
            self.send_data(host_socket, label='created_room', contents={'status': 'ok','room':room_name})
            for client_socket in self.requests:
                self.list_rooms(client_socket)
        else:
            self.send_data(host_socket, label='created_room', contents={'status': 'room already exists','room':room_name})
    
    # List all chat rooms to the requesting client
    def list_rooms(self, client_socket):
        cr_info = {room: client_socket in self.chat_rooms[room] for room in self.chat_rooms}
        self.send_data(client_socket, label='list_rooms', contents={'rooms': cr_info})
    
    # Add a client to an existing chat room
    def join_room(self, room_name, client_socket, old_room):
        if room_name in self.chat_rooms and client_socket not in self.chat_rooms[room_name]:
            if old_room:
                self.chat_rooms[old_room].remove(client_socket)
            self.chat_rooms[room_name].append(client_socket)
            
            self.send_data(client_socket, label='join_room', contents={'status': 'ok','room':room_name})
        else:
            self.send_data(client_socket, label='join_room', contents={
                    'status': 'room already joined' if room_name in self.chat_rooms else 'room not found',
                    'room':room_name
                })

    # Send data and encode data sent.
    def send_data(self, client_socket, label:str, contents:dict, mode:str='utf-8'):
        assert mode=='utf-8', 'please write your own handler or modify code'
        if label != 'voice':
            self.log(contents, mode=f'O/{label}', socket=client_socket)
        contents.update({'label': label})
        self.buffers[client_socket].send(client_socket, contents)
        # data = json.dumps(contents).encode('utf-8')
        # client_socket.send(data)        

    # Start the server, accept connections, and spawn threads to handle each client
    def start(self):
        print("Starting server...")
        threading.Thread(target=self.__listen, daemon=True).start()
        signal.signal(signal.SIGINT, self.terminate)
        while True:
            pass

    def __listen(self):
        while True:
            client_socket, _ = self.server_socket.accept()
            print('Accepted request from: %s port %s' % client_socket.getpeername())
            self.buffers.update({client_socket: Buffer()})
            threading.Thread(target=self.handle_client, args=(client_socket,), daemon=True).start()
            self.requests.add(client_socket)

    # Terminate all connections and shutdown the server.
    def terminate(self, *args):
        print('You are currently on Chat Server at IP [{}] and port [{}]'.format(*self.get_ip()))
        print('Are you sure that you want to terminate this server? Reply with y/n.')
        response = input()
        if response in ('y', 'yes'):
            print('Terminating all connections.')
            for client_socket in self.requests:
                self.send_data(client_socket, 'terminate', dict())
                client_socket.close()
            print('Server terminated.')
            sys.exit()

    # Handler of logging
    def log(self, content, mode='D', socket:socket.socket=None):
        if self.show_log:
            print(mode.ljust(20), '\t:', *socket.getpeername(), '\t:', content)


def resolve_public_ip(): 
    ## This returns a public IP, but is still useless for network hosting due to port fowarding
    import requests as req
    url = 'https://checkip.amazonaws.com/'
    request = req.get(url)
    ip = request.text
    return ip

# If the script is the main program, define host and port, and start the server
if __name__ == '__main__':
    args, help = parse_args()
    if 'h' in args:
        help()
        exit()
    #HOST = '127.0.0.1'  # Loopback address for localhost
    HOST = socket.gethostbyname(socket.gethostname())
    PORT = args.port
    ChatServer(HOST, PORT, show_log='log' in args).start()