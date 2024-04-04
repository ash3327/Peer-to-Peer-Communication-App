import argparse

import socket
import threading
import tkinter as tk
import pyaudio
import json

# Networking configuration 
# (Default values if user did not pass in any parameters)
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
    parser.add_argument('-l', '--log', default=argparse.SUPPRESS, action='store_true', help='Whether all communications are logged.')
    return parser.parse_args(), parser.print_help

class ChatClient:
    def __init__(self, host, port, show_log:bool=False):
        # Settings
        self.show_log = show_log

        # Socket setup
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
        threading.Thread(target=self.listen, daemon=True).start()
        self.list_rooms()
        self.root.mainloop()

    def gui_setup(self):
        window_size = (800, 600)
        screen_size = (self.root.winfo_screenwidth(), self.root.winfo_screenheight()*.9)
        self.root.geometry('%dx%d' % window_size)
        self.root.eval('tk::PlaceWindow . center')
        self.root.geometry('+%d+%d' % (screen_size[0]/2-window_size[0]/2,screen_size[1]/2-window_size[1]/2))
        self.root.configure(bg='light gray')

        # Room creation entry
        self.create_room_entry = tk.Entry(self.root)
        self.create_room_entry.pack()
        
        # Create room button
        create_room_button = tk.Button(self.root, text="Create Room", command=self.create_room)
        create_room_button.pack()

        # List rooms button
        # list_rooms_button = tk.Button(self.root, text="List Rooms", command=self.list_rooms)
        # list_rooms_button.pack()
        
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
            self.list_rooms()

    def list_rooms(self):
        self.send_command({'action': 'list'})

    def join_room(self):
        selected_room = self.rooms_listbox.get(tk.ACTIVE)
        if selected_room:
            self.send_command({'action': 'join', 'room': selected_room})

    def send_command(self, command):
        try:
            self.log(command, mode=f"O/{command['action']}")
            self.socket.send(json.dumps(command).encode('utf-8'))
        except ConnectionResetError:
            self.handle_lost_connection()
            return
        if command['action'] == 'exit':
            self.socket.shutdown(socket.SHUT_RDWR)
            self.socket.close()
            self.root.destroy()
            return

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

    # Handler of logging
    def log(self, content, mode='D'):
        if self.show_log:
            print(mode.ljust(20), '\t:', content)

    # Handler of packages
    def handle(self, label, response:dict):
        self.log(response, mode=f'I/{label}')
        if label == 'list_rooms':
            self.update_rooms_list(response.get('rooms', []))
        elif label == 'created_room':
            if response['status'] == 'ok':
                print(f"Room '{response['room']}' created successfully.")
            else:
                print("Failed to create room.")
        elif label == 'join_room':
            if response['status'] == 'ok':
                print(f"Joined room '{response['room']}' successfully.")
                self.start_audio_streaming(response['room'])
            else:
                print("Failed to join room.")

    # Listening for data packets
    def listen(self):
        while True:
            try:
                response = json.loads(self.socket.recv(1024).decode('utf-8'))
                if response:
                    label = response['label']
                    response.pop('label',None)
                    self.handle(label, response)
            except socket.error:
                return

    # Terminate the current connection.
    def terminate(self):
        self.send_command({'action': 'exit'})

    # Handler in case of losing connection.
    def handle_lost_connection(self):
        print('Lost Connection to server.')
        exit()

if __name__ == '__main__':
    args, help = parse_args()
    if 'h' in args:
        help()
        exit()
    SERVER_HOST = args.ip
    SERVER_PORT = args.port
    ChatClient(SERVER_HOST, SERVER_PORT, show_log='log' in args)