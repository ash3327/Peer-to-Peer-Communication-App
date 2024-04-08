import argparse
import signal
import sys
import os
import shutil

import socket
import threading
import json
import selectors 
import base64
import time

import resources
from buffer import Buffer
from Audio import output_audio
from pydub import AudioSegment

from chat_client import CHUNK, CHANNELS, RATE
SAMPLE_WIDTH = 2
SILENT_DURATION_MS = 1000 * CHUNK / RATE

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
    parser.add_argument('-r', '--rate', type=int, default=RATE, help='The audio sample rate, normally 22050 or 44100.')
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
        self.chat_rooms_start_time = dict() # Format: {room_name: room's start time}
        self.chat_rooms_audio_overlay = dict() # Format: {room_name: dict(time: dict(client: audio_data))}
        self.user_name_cnt = 0
        self.user_names = dict()

        # Dictionary to keep track of recording data in each chat room
        self.recordings = dict() 
        ''' Format:
        self.recordings = {
            'room_name_1': AudioSegment(),
            'room_name_2': AudioSegment(),
            # ... more rooms with their respective AudioSegment
        }
        '''

        # Dictionary to keep track of screen share
        self.is_room_share_screen = dict() # Format: {room_name: True/False}
        self.room_screens = dict() # Format: {room_name: screen_bytes}

        # List to keep track of active requests
        self.requests = set()

        print('Initializing Chat Server at IP [{}] and port [{}]'.format(*self.get_ip()))
        print('Accepted Audio Sample Rate:', RATE)
        
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
            # On socket error, close the client's connection
            except socket.error as e1:
                try:
                    print('Error. Ended request from: %s port %s' % client_socket.getpeername())
                    self.remove_client(client_socket)
                    self.requests.remove(client_socket)
                    client_socket.close()
                    print('Error 94:',e1)
                    return
                except Exception as e:
                    # raise e
                    print('Error 98:',e)
                    return
                
    # Handler
    def handle_listener(self, message, client_socket):
        try: 
            command = message#json.loads(message)
        except Exception as e:
            self.log(message+'\n'+e, mode='E/error', socket=client_socket)
            raise e
            return
        self.log(command, mode=f"I/{command['action']}", socket=client_socket)
        # Execute the appropriate action based on the command received
        if command['action'] == 'create':
            self.create_room(command['room'], client_socket)
        elif command['action'] == 'list':
            self.list_rooms(client_socket)
        elif command['action'] == 'join':
            self.join_room(command['room'], client_socket, command['old_room'])
        elif command['action'] == 'request_user_name':
            self.assign_user_name(command['user_name'], client_socket, command['room'])
        elif command['action'] == 'quit_room':
            self.quit_room(command['room'], client_socket)
        elif command['action'] == 'exit':
            self.remove_client(client_socket, command['room_name'])
            self.requests.remove(client_socket)
            print('Ended request from: %s port %s' % client_socket.getpeername())
            client_socket.close()
            return
        elif command['action'] == 'voice':
            self.voice(command, client_socket) # fyi, command structure is in send_audio_thread

        elif command['action'] == 'record_start':
            if command['room_name'] not in self.recordings:
                self.start_recording(command['room_name'])
        elif command['action'] == 'record_end':
            if command['room_name'] in self.recordings:
                self.stop_recording(command['room_name'])

        elif command['action'] == 'request_sample_rate':
            self.send_data(client_socket, label='response_sample_rate', contents={'sample_rate':RATE})
        elif command['action'] == 'screen_share':
            if (command['room_name'] not in self.is_room_share_screen) or (not self.is_room_share_screen[command['room_name']]):
                self.is_room_share_screen[command['room_name']] = True
                self.send_data(client_socket, label='screen_share_response', contents={'status': 'ok'})
            else:
                self.send_data(client_socket, label='screen_share_response', contents={'status': 'someone else is sharing'})
        elif command['action'] == 'screen_unshare':
            self.is_room_share_screen[command['room_name']] = False
            self.room_screens.pop(command['room_name'])
        elif command['action'] == 'update_screen':
            self.room_screens[command['room_name']] = command['screen_data']
        elif command['action'] == 'request_screen_data':
            if (command['room_name'] in self.is_room_share_screen) and (self.is_room_share_screen[command['room_name']]):
                content = {'screen_data': self.room_screens[command['room_name']]}
                self.send_data(client_socket, label='response_screen_data', contents=content)
            else:
                # self.send_data(client_socket, label='clear_canvas')
                self.send_data(client_socket, label='clear_canvas', contents={'d':'ummy'})

    # remove client from room if client exits
    def remove_client(self, client_socket, room_name=None):
        if room_name:
            self.quit_room(room_name, client_socket)
        else:
            for room in self.chat_rooms:
                self.quit_room(room, client_socket)
        self.user_names.pop(client_socket, None)

    def append_recording(self, last_chunk_data, room_name):
        try:
            audio = AudioSegment.silent(duration=SILENT_DURATION_MS, frame_rate=RATE,)
            for user in self.chat_rooms[room_name].copy():
                if user in last_chunk_data:
                    user_voice = last_chunk_data[user]
                    audio = audio.overlay(user_voice)

            self.recordings[room_name] += audio
        except KeyError as e:
            raise e

    def output_last_chunk_to_client(self, room_name):
        last_chunk =  list(self.chat_rooms_audio_overlay[room_name].keys())
        if last_chunk:
            last_chunk = last_chunk[0]
            try:
                last_chunk_data = self.chat_rooms_audio_overlay[room_name].pop(last_chunk)
            except KeyError as e:
                raise e
            if room_name in self.recordings:
                self.append_recording(last_chunk_data, room_name)

            for user in self.chat_rooms[room_name]:
                audio = AudioSegment.silent(duration=SILENT_DURATION_MS, frame_rate=RATE,)
                for other_user in self.chat_rooms[room_name]:
                    try:
                        if other_user != user:
                            other_user_voice = last_chunk_data[other_user]
                            audio = audio.overlay(other_user_voice)
                    except KeyError: # KeyError is the person is muted / no audio signal
                        pass
                audio_data = base64.b64encode(audio.raw_data).decode('utf-8')
                self.send_data(user, label='voice', contents={'audio_data': audio_data})

            return last_chunk
        else:
            return None


    # calculate chunk number of a specific time in a specific room
    def calculate_chunk(self, time, room_name):
        time_passed = time - self.chat_rooms_start_time[room_name]
        chunk_time = CHUNK / RATE
        return int(time_passed // chunk_time)

    # receive voice from user and send voice to other user
    def voice(self, command, client_socket):
        try:
            room_name = command['room_name']
            if not room_name:
                return
            audio_data = base64.b64decode(command['audio_data'])
            current_chunk = self.calculate_chunk(time.time(), room_name)
            last_chunk = None

            if current_chunk not in self.chat_rooms_audio_overlay[room_name]: # New chunk
                last_chunk = self.output_last_chunk_to_client(room_name)
                self.chat_rooms_audio_overlay[room_name][current_chunk] = {}

            self.chat_rooms_audio_overlay[room_name][current_chunk][client_socket] = AudioSegment(data=audio_data, sample_width=SAMPLE_WIDTH, frame_rate=RATE, channels=CHANNELS)

        except Exception as e:
            raise e

    # Create a new chat room or inform the host if it already exists
    def create_room(self, room_name, host_socket):        
        if room_name not in self.chat_rooms:
            self.chat_rooms[room_name] = []
            self.chat_rooms_start_time[room_name] = time.time()
            self.chat_rooms_audio_overlay[room_name] = dict()
            self.send_data(host_socket, label='created_room', contents={'status': 'ok','room':room_name})
            for client_socket in self.requests:
                self.list_rooms(client_socket)
        else:
            self.send_data(host_socket, label='created_room', contents={'status': 'room already exists','room':room_name})

    # List all chat rooms to the requesting client
    def list_rooms(self, client_socket):
        try:
            cr_info = {room: client_socket in self.chat_rooms[room] for room in self.chat_rooms}
            self.send_data(client_socket, label='list_rooms', contents={'rooms': cr_info})
        except Exception:
            pass
    
    # Add a client to an existing chat room
    def join_room(self, room_name, client_socket, old_room):
        if room_name in self.chat_rooms and client_socket not in self.chat_rooms[room_name]:
            if old_room:
                self.chat_rooms[old_room].remove(client_socket)
            self.chat_rooms[room_name].append(client_socket)
            
            self.send_data(client_socket, label='join_room', contents={'status': 'ok','room':room_name})
            self.update_room_users(room_name)
            self.update_room_users(old_room)
        else:
            self.send_data(client_socket, label='join_room', contents={
                    'status': 'room already joined' if room_name in self.chat_rooms else 'room not found',
                    'room':room_name
                })
            
    # Update the room members to other users
    def update_room_users(self, room_name):
        if room_name is None or room_name not in self.chat_rooms:
            return
        user_names = [self.user_names[user] for user in self.chat_rooms[room_name]]
        for client_socket in self.chat_rooms[room_name]:
            try:
                self.send_data(client_socket, label='update_room_users', contents={
                        'room':room_name,
                        'users':user_names
                    })
            except Exception:
                pass
            
    # Assign a user name to client
    def assign_user_name(self, user_name, client_socket, room_name):
        if user_name is None:
            self.user_name_cnt += 1
            user_name = f'User{self.user_name_cnt:06}'
        username_is_valid = user_name not in self.user_names.values()
        
        if username_is_valid:
            self.user_names.update({client_socket: user_name})
            self.update_room_users(room_name)
        self.send_data(client_socket, label='response_user_name', contents={
                    'status': 'ok' if username_is_valid else 'conflict',
                    'user_name':user_name
                })
            
    # Remove the client from the chat room
    def quit_room(self, room_name, client_socket):
        if room_name and client_socket in self.chat_rooms[room_name]:
            self.chat_rooms[room_name].remove(client_socket)
            self.list_rooms(client_socket)
            self.update_room_users(room_name)

    # Send data and encode data sent.
    def send_data(self, client_socket, label:str, contents:dict, mode:str='utf-8'):
        assert mode=='utf-8', 'please write your own handler or modify code'
        self.log(contents, mode=f'O/{label}', socket=client_socket)
        contents.update({'label': label})
        self.buffers[client_socket].send(client_socket, contents)    

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
            print('Deleting chat rooms')
            for chat_room_dir in self.chat_rooms:
                try:
                    shutil.rmtree(chat_room_dir)
                except OSError as e:
                    print(f"Error: {e.strerror}")
            print('Server terminated.')
            sys.exit()

    # Handler of logging
    def log(self, content, mode='D', socket:socket.socket=None):
        if self.show_log:
            if mode == 'I/voice' or mode == 'O/voice':
                return
            print(mode.ljust(20), '\t:', *socket.getpeername() if socket else [None], '\t:', content)

    def start_recording(self, room_name):
        for member_socket in self.chat_rooms[room_name]:
            self.send_data(member_socket, label='record_start', contents={'room_name': room_name})
        # Empty audio init
        self.recordings[room_name] = AudioSegment(data=b"", sample_width=SAMPLE_WIDTH, frame_rate=RATE, channels=CHANNELS)
    
    def stop_recording(self, room_name):
        # audio processing and saving
        for member_socket in self.chat_rooms[room_name]:
            self.send_data(member_socket, label='record_end', contents={'room_name': room_name})
        try:
            output_audio(self.recordings[room_name], room_name)
            del self.recordings[room_name]
        except Exception as e:
            self.log(e, mode='E/error')
            raise e


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
    print('Public IP:',resolve_public_ip())
    #HOST = '127.0.0.1'  # Loopback address for localhost
    HOST = socket.gethostbyname(socket.gethostname())
    PORT = args.port
    RATE = args.rate
    SILENT_DURATION_MS = 1000 * CHUNK / RATE
    ChatServer(HOST, PORT, show_log='log' in args).start()