import argparse

import socket
import threading
import tkinter as tk
import pyaudio
import json
import customtkinter as ctk
import warnings

import resources
from gui_utils import RoomsPanel

ctk.deactivate_automatic_dpi_awareness()
warnings.filterwarnings('ignore')

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

        # Start the Window
        self.root = ctk.CTk()
        self.root.title("Voice Chat Rooms")
        self.root.protocol("WM_DELETE_WINDOW", self.terminate)
    
        self.gui_setup()
        threading.Thread(target=self.listen, daemon=True).start()
        self.list_rooms()
        self.root.mainloop()

    def gui_setup(self):
        # -------------- BACKGROUND -------------
        window_size = (800, 600)
        screen_size = (self.root.winfo_screenwidth(), self.root.winfo_screenheight()*.9)
        self.root.geometry('%dx%d' % window_size)
        self.root.eval('tk::PlaceWindow . center')
        self.root.geometry('+%d+%d' % (screen_size[0]/2-window_size[0]/2,screen_size[1]/2-window_size[1]/2))
        self.root.configure(bg=resources.get_color('window'))

        # --------------- SIDEBAR ---------------
        # Sidebar Frame
        self.sidebar = tk.Frame(self.root, bg=resources.get_color('side_bar','fill'))
        self.sidebar.place(relx=0, rely=0, relwidth=.25, relheight=1)

        # Header
        self.brand_frame = tk.Frame(self.sidebar)
        self.brand_frame.place(relx=0, rely=0, relwidth=1, relheight=.2)
        self.brand_frame.update()
        logo_size = (self.brand_frame.winfo_width(), self.brand_frame.winfo_height())
        
        logo = tk.Label(self.brand_frame, 
                        image=resources.get_icon(
                            'side_bar','brand_header',
                            image_size=logo_size
                        ))
        logo.pack()

        # Submenu Bars
        self.submenu_frame = tk.Frame(self.sidebar, bg=resources.get_color('side_bar','fill'))
        self.submenu_frame.place(relx=0, rely=.25, relwidth=1, relheight=.75)

        ## Room creation entry
        # self.create_room_entry = ctk.CTkEntry(self.submenu_frame)
        # self.create_room_entry.pack(pady=5)

        ## Button Styles
        button_style = dict(
            text_color=resources.get_color('side_bar','button','text_color'),
            width=self.sidebar.winfo_width(),
            corner_radius=0,
            anchor='w'
        )
        
        ## Create room button
        def create_room_dialog():
            self.root.update_idletasks()
            dialog = ctk.CTkInputDialog(text='Please input a name for your new room:', title='Input Room Name:')
            dialog.update()
            screen_size = (self.root.winfo_screenwidth(), self.root.winfo_screenheight()*.9)
            window_size = (dialog.winfo_width()*1.5, dialog.winfo_height())
            dialog.tk.eval(f'tk::PlaceWindow {dialog._w} center')
            dialog.geometry('+%d+%d' % (screen_size[0]/2-window_size[0]/2,screen_size[1]/2-window_size[1]/2))
            result = dialog.get_input()
            self.create_room(result)

        create_room_button = ctk.CTkButton(
                self.submenu_frame, 
                image=resources.get_icon('side_bar','add_icon',image_size=32), 
                text="New Room", 
                command=create_room_dialog,
                **button_style
            )
        create_room_button.pack()

        ## List rooms button
        # list_rooms_button = tk.Button(self.root, text="List Rooms", command=self.list_rooms)
        # list_rooms_button.pack()
        
        ## Rooms listbox
        # self.rooms_listbox = tk.Listbox(self.submenu_frame)
        # self.rooms_listbox.pack(pady=5)
        self.submenu_frame.update()
        self.rooms_listbox = RoomsPanel(
                master=self.submenu_frame, 
                button_style=button_style, 
                join_room_command=self.join_room,
                height=self.submenu_frame.winfo_height()*.7,
                fg_color=resources.get_color('side_bar','fill'),
                border_width=0, corner_radius=0
            )
        self.rooms_listbox.pack(pady=10)

        ## Join room button
        # join_room_button = ctk.CTkButton(
        #         self.submenu_frame, text="Join Room", command=self.join_room, 
        #         image=resources.get_icon('side_bar','join_room_icon', image_size=32), 
        #         **button_style
        #     )
        # join_room_button.pack()

    # Alert Message
    def notify_user(self, message:str, duration:int=5000, label='info'):
        self.log(message, mode='D/print')
        if hasattr(self, 'notif') and self.notif.winfo_ismapped():
            self.notif.pack_forget()
        self.notif = notif = ctk.CTkLabel(self.root, text=message, 
                             bg_color=resources.get_color('message',label), 
                             padx=10, pady=10, corner_radius=20)
        notif.pack(expand=True)
        notif.after(duration, lambda: notif.pack_forget())

    def create_room(self, room_name):
        #room_name = self.create_room_entry.get()
        if room_name:
            self.send_command({'action': 'create', 'room': room_name})
            self.list_rooms()

    def list_rooms(self):
        self.send_command({'action': 'list'})

    def join_room(self, selected_room=None):
        if selected_room is None:
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

    def update_rooms_list(self, rooms:dict):
        for room, is_member in rooms.items():
            self.rooms_listbox.update(room, is_member)

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
        elif mode.startswith('D') or mode.startswith('E'):
            print(content)

    # Handler of packages
    def handle(self, label, response:dict):
        self.log(response, mode=f'I/{label}')
        if label == 'list_rooms':
            self.update_rooms_list(response.get('rooms', dict()))
        elif label == 'created_room':
            if response['status'] == 'ok':
                self.notify_user(f"Room '{response['room']}' created successfully.", label='success')
            elif response['status'] == 'room already exists':
                self.notify_user("Room already exists.", label='neutral')
            else:
                self.notify_user("Failed to create room.", label='fail')
        elif label == 'join_room':
            if response['status'] == 'ok':
                self.notify_user(f"Joined room '{response['room']}' successfully.", label='success')
                self.list_rooms()
                self.start_audio_streaming(response['room'])
            elif response['status'] == 'room already joined':
                self.notify_user("Room already joined.", label='neutral')
            else:
                self.notify_user("Failed to join room.", label='fail')

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
        self.notify_user('Lost Connection to server.', label='fail')
        self.root.after(4000, lambda: exit())

if __name__ == '__main__':
    args, help = parse_args()
    if 'h' in args:
        help()
        exit()
    SERVER_HOST = args.ip
    SERVER_PORT = args.port
    ChatClient(SERVER_HOST, SERVER_PORT, show_log='log' in args)