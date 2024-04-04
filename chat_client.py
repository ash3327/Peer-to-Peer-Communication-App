import argparse

import socket
import threading
import tkinter as tk
import pyaudio
import json

# Networking configuration
SERVER_HOST = '10.13.252.5'#'127.0.0.1'#'server_ip'  # Replace with the server's IP
SERVER_PORT = 12345
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
CHUNK = 1024

'''
    Parse command line arguments
'''
def parse_args():
    parser = argparse.ArgumentParser(description='Compress or decompress files using LZW algorithm')
    parser.add_argument('-i', '--ip', type=str, default=SERVER_HOST, help='The server IP address.')
    parser.add_argument('-p', '--port', type=int, default=SERVER_PORT, help='The server port.')
    return parser.parse_args(), parser.print_help

class ChatClient:
    def __init__(self, host, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.rooms = []
        
        # Audio setup
        self.paudio = pyaudio.PyAudio()
        self.audio_stream = self.paudio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

        # Start the GUI
        self.root = tk.Tk()
        self.root.title("Voice Chat Rooms")
        self.root.protocol("WM_DELETE_WINDOW", self.terminate)
        self.gui_setup()
        self.root.mainloop()

    def gui_setup(self):
        # Room creation entry
        self.create_room_entry = tk.Entry(self.root)
        self.create_room_entry.pack()
        
        # Create room button
        create_room_button = tk.Button(self.root, text="Create Room", command=self.create_room)
        create_room_button.pack()

        # List rooms button
        list_rooms_button = tk.Button(self.root, text="List Rooms", command=self.list_rooms)
        list_rooms_button.pack()
        
        # Rooms listbox
        self.rooms_listbox = tk.Listbox(self.root)
        self.rooms_listbox.pack()

        # Join room button
        join_room_button = tk.Button(self.root, text="Join Room", command=self.join_room)
        join_room_button.pack()

    def create_room(self):
        room_name = self.create_room_entry.get()
        if room_name:
            self.send_command({'action': 'create', 'room': room_name})

    def list_rooms(self):
        self.send_command({'action': 'list'})

    def join_room(self):
        selected_room = self.rooms_listbox.get(tk.ACTIVE)
        if selected_room:
            self.send_command({'action': 'join', 'room': selected_room})

    def send_command(self, command):
        self.socket.send(json.dumps(command).encode('utf-8'))
        if command['action'] == 'exit':
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
            self.root.destroy()
            return
        
        response = json.loads(self.socket.recv(1024).decode('utf-8'))
        if command['action'] == 'list':
            self.update_rooms_list(response.get('rooms', []))
        elif command['action'] == 'create':
            if response['status'] == 'ok':
                print(f"Room '{command['room']}' created successfully.")
            else:
                print("Failed to create room.")
        elif command['action'] == 'join':
            if response['status'] == 'ok':
                print(f"Joined room '{command['room']}' successfully.")
                self.start_audio_streaming(command['room'])
            else:
                print("Failed to join room.")

    def update_rooms_list(self, rooms):
        self.rooms_listbox.delete(0, tk.END)
        for room in rooms:
            self.rooms_listbox.insert(tk.END, room)

    def start_audio_streaming(self, room_name):
        # This function would start two threads:
        # One to handle sending audio data to the room participants
        # Another to receive and play audio data from the room participants
        # You would need to implement the audio networking similar to the example in the previous answer
        pass

    def terminate(self):
        self.send_command({'action': 'exit'})

if __name__ == '__main__':
    args, help = parse_args()
    if 'h' in args:
        help()
        exit()
    SERVER_HOST = args.ip
    SERVER_PORT = args.port
    ChatClient(SERVER_HOST, SERVER_PORT)