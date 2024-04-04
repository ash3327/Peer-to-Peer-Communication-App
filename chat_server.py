import socket
import threading
import json

# Define the ChatServer class to manage chat rooms and client connections
class ChatServer:
    # Initialize the ChatServer with a host address and a port number
    def __init__(self, host, port):
        # Create a socket and bind it to the host and port, then start listening for connections
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((host, port))
        self.server_socket.listen()
        # Dictionary to keep track of chat rooms and their participants
        self.chat_rooms = {}  # Format: {room_name: [client_sockets]}

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
                message = client_socket.recv(1024).decode('utf-8')
                if message:
                    command = json.loads(message)
                    # Execute the appropriate action based on the command received
                    if command['action'] == 'create':
                        self.create_room(command['room'], client_socket)
                    elif command['action'] == 'list':
                        self.list_rooms(client_socket)
                    elif command['action'] == 'join':
                        self.join_room(command['room'], client_socket)
            # On socket error, close the client's connection
            except socket.error:
                client_socket.close()
                return
    
    # Create a new chat room or inform the host if it already exists
    def create_room(self, room_name, host_socket):
        if room_name not in self.chat_rooms:
            self.chat_rooms[room_name] = [host_socket]
            host_socket.send(json.dumps({'status': 'ok'}).encode('utf-8'))
        else:
            host_socket.send(json.dumps({'status': 'room already exists'}).encode('utf-8'))

    # List all chat rooms to the requesting client
    def list_rooms(self, client_socket):
        rooms = list(self.chat_rooms.keys())
        client_socket.send(json.dumps({'rooms': rooms}).encode('utf-8'))
    
    # Add a client to an existing chat room
    def join_room(self, room_name, client_socket):
        if room_name in self.chat_rooms and client_socket not in self.chat_rooms[room_name]:
            self.chat_rooms[room_name].append(client_socket)
            client_socket.send(json.dumps({'status': 'ok'}).encode('utf-8'))
        else:
            client_socket.send(json.dumps({'status': 'room not found'}).encode('utf-8'))
    
    # Start the server, accept connections, and spawn threads to handle each client
    def start(self):
        print("Starting server...")
        while True:
            client_socket, _ = self.server_socket.accept()
            threading.Thread(target=self.handle_client, args=(client_socket,)).start()

# If the script is the main program, define host and port, and start the server
if __name__ == '__main__':
    HOST = '127.0.0.1'  # Loopback address for localhost
    HOST = socket.gethostbyname(socket.gethostname())
    PORT = 12345         # Arbitrary non-privileged port number
    ChatServer(HOST, PORT).start()