import argparse

import socket
import threading
import tkinter as tk
import pyaudio
import json
import customtkinter as ctk
import warnings

import resources
from gui_utils import RoomsPanel, ToggleButton, InputDialog
import base64

from buffer import Buffer

ctk.deactivate_automatic_dpi_awareness()
warnings.filterwarnings('ignore')

# Networking configuration 
# (Default values if user did not pass in any parameters)
SERVER_HOST = '10.13.252.5'#'127.0.0.1'#'server_ip'  # Replace with the server's IP
SERVER_PORT = 12345
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 22050
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
        self.current_room = None # for removing from room if exit program
        self.error_state = False

        # Socket setup
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((host, port))
        self.rooms = []

        # User settings setup
        self.user_name = None

        # Buffer setup
        self.buffer = Buffer()
        
        # Audio setup
        self.paudio = pyaudio.PyAudio()
        self.audio_stream = self.paudio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, output=True, frames_per_buffer=CHUNK)
        self.audio_stream_thread = None
        self.is_streaming = False

        # Start the Window
        self.root = ctk.CTk()
        self.root.title("Voice Chat Rooms")
        self.root.protocol("WM_DELETE_WINDOW", self.terminate)
    
        self.gui_setup()
        threading.Thread(target=self.listen, daemon=True).start()
        self.list_rooms()
        self.request_user_name()
        self.request_sample_rate()
        self.root.mainloop()

    def gui_setup(self):
        # ---------------------------------------
        #              BACKGROUND
        # ---------------------------------------
        window_size = (800, 600)
        screen_size = (self.root.winfo_screenwidth(), self.root.winfo_screenheight()*.9)
        self.root.geometry('%dx%d' % window_size)
        self.root.eval('tk::PlaceWindow . center')
        self.root.geometry('+%d+%d' % (screen_size[0]/2-window_size[0]/2,screen_size[1]/2-window_size[1]/2))
        self.root.configure(bg=resources.get_color('window'))

        # ---------------------------------------
        #             SIDEBAR FRAME
        # ---------------------------------------
        self.sidebar = tk.Frame(self.root, bg=resources.get_color('side_bar','fill'))
        self.sidebar.place(relx=0, rely=0, relwidth=.25, relheight=1)

        # --------------- HEADER ----------------
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

        # ------------ SUBMENU BARS ------------
        # Submenu Bars
        self.submenu_frame = tk.Frame(self.sidebar, bg=resources.get_color('side_bar','fill'))
        self.submenu_frame.place(relx=0, rely=.25, relwidth=1, relheight=.75)

        # Button Styles
        button_style = dict(
            text_color=resources.get_color('side_bar','button','text_color'),
            width=self.sidebar.winfo_width(),
            corner_radius=0,
            anchor='w'
        )
        
        # Create room button
        def create_room_dialog():
            dialog = InputDialog(self.root, text='Please input a name for your new room:', title='Input Room Name:')
            self.create_room(dialog.get())

        create_room_button = ctk.CTkButton(
                self.submenu_frame, 
                image=resources.get_icon('side_bar','add_icon',image_size=32), 
                text="New Room", 
                command=create_room_dialog,
                **button_style
            )
        create_room_button.pack()
        
        # Rooms listbox
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

        # --------- INFO AND SETTINGS ---------
        # Chat server details
        label = tk.Label(
            self.submenu_frame, 
            text=f'Server: \t{self.socket.getpeername()[0]}\nPort: \t{self.socket.getpeername()[1]}', 
            justify='left', bg=resources.get_color('side_bar','fill'))
        label.pack(side='bottom', anchor='w', padx=5, pady=2)

        # Settings panel
        self.settings_panel = tk.Frame(self.submenu_frame, bg=resources.get_color('window'))
        self.settings_panel.pack(side='bottom', anchor='w')
        
        # User name button
        def ask_for_user_name():
            dialog = InputDialog(self.root, text='Please input a user name.', title='New user name:')
            user_name = dialog.get()
            if user_name:
                self.request_user_name(user_name)

        self.user_name_label = ctk.CTkButton(
            self.settings_panel, 
            image=resources.get_icon('side_bar', 'user', image_size=32),
            text=f'User: {self.user_name}',
            command=ask_for_user_name,
            **button_style)
        self.user_name_label.pack()

        # ---------------------------------------
        #               MAIN FRAME
        # ---------------------------------------  
        self.main_frame = tk.Frame(self.root, bg=resources.get_color('window'))
        self.main_frame.place(relx=.25, rely=0, relwidth=.75, relheight=1)

        # ----------- RECORDING PANEL -----------
        self.recording_panel = tk.Frame(self.main_frame, bg=resources.get_color('record_bar','fill'))
        self.recording_panel.pack(side='bottom', pady=10)
        
        # Button configs
        image_size=28
        basic_button_configs = dict(
            text=None,
            width=40, height=40,
            corner_radius=20,
            border_width=0,
        )
        button_configs = dict(
            **basic_button_configs,
            on_color=resources.get_color('record_bar','button_fill','on_state'),
            off_color=resources.get_color('record_bar','button_fill','off_state'),
            hover_on_color=resources.get_color('record_bar','button_fill','on_state_hover'),
            hover_off_color=resources.get_color('record_bar','button_fill','off_state_hover'),
        )

        # Record Button
        self.record_button = ToggleButton(
                self.recording_panel, 
                on_image=resources.get_icon('record','stop_recording',image_size=image_size),
                off_image=resources.get_icon('record','start_recording',image_size=image_size),
                on_command=self.start_recording,
                off_command=self.stop_recording,
                **button_configs
            )
        self.record_button.pack(side='left', padx=5)

        # Mute/Unmute Button
        self.mute_button = ToggleButton(
                self.recording_panel, 
                on_image=resources.get_icon('record','mute',image_size=image_size),
                off_image=resources.get_icon('record','unmute',image_size=image_size),
                on_command=self.unmute, 
                off_command=self.mute, 
                **button_configs
            )
        self.mute_button.pack(side='left', padx=5)

        # Quit Button
        self.quit_button = ToggleButton(
                self.recording_panel, 
                off_image=resources.get_icon('record','quit_room',image_size=image_size),
                on_command=self.quit_room, 
                off_color=resources.get_color('record_bar','button_fill','quit_room'),
                hover_off_color=resources.get_color('record_bar','button_fill','quit_room_hover'),
                **basic_button_configs,
                on_color='blue', hover_on_color='blue' # useless but need to be there
            )
        self.quit_button.pack(side='left', padx=5)

    # Alert Message
    def notify_user(self, message:str, duration:int=5000, label='info'):
        self.log(message, mode='D/print')
        if hasattr(self, 'notif') and self.notif.winfo_ismapped():
            self.notif.pack_forget()
        self.notif = notif = ctk.CTkLabel(self.root, text=message, 
                             bg_color=resources.get_color('message',label), 
                             padx=10, pady=10, corner_radius=20, text_color='black')
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
            self.record_button.set(is_on=False, exec=False)
            self.send_command({'action': 'join', 'room': selected_room, 'old_room': self.current_room})
            

    def request_user_name(self, user_name=None):
        self.send_command({'action': 'request_user_name', 'user_name': user_name, 'room': self.current_room})

    def request_sample_rate(self):
        self.send_command({'action': 'request_sample_rate'})

    def send_command(self, command):
        try:
            if command['action'] != 'voice':
                self.log(command, mode=f"O/{command['action']}")
            self.buffer.send(self.socket, command)
        except (ConnectionResetError, ConnectionAbortedError):
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

    def start_audio_streaming(self, room_name=None): # room_name is useless as self.current_room is used
        if not self.audio_stream_thread:
            self.audio_stream_thread = threading.Thread(target=self.send_audio_thread, daemon=True).start()

    def send_audio_thread(self):
        while self.is_streaming:
            if self.current_room:
                try:
                    # Read audio data from the microphone
                    audio_data = self.audio_stream.read(CHUNK)
                    audio_data = base64.b64encode(audio_data).decode('utf-8')
                    # print(len(audio_data))

                    # Send the audio data to the server
                    command = {'action': 'voice', 
                            'audio_data': audio_data,
                            'room_name': self.current_room,}
                    # command = {'action':'dummy'}
                    self.send_command(command)

                except Exception as e:
                    print("Error in send_audio_thread:", e)
                    break

    def play_audio_thread(self, audio_data):
        # Play the received audio data
        audio_data = base64.b64decode(audio_data)
        # print(audio_data[:20])
        self.audio_stream.write(audio_data)
        # self.play_audio(audio_data)

    def start_recording(self):
        if self.current_room:
            self.notify_user('Start Recording')
            self.send_command({'action': 'record_start', 'room_name': self.current_room})
        else:
            self.record_button.set(is_on=False)
            self.notify_user('You cannot record without joining a room.', label='fail')

    def stop_recording(self):
        if self.current_room:
            self.notify_user('Stop Recording')
            self.send_command({'action': 'record_end', 'room_name': self.current_room})

    def mute(self):
        if self.is_streaming:
            self.notify_user('Muted')
            self.is_streaming = False

    def unmute(self):
        if self.current_room:
            self.notify_user('Unmuted')
            self.is_streaming = True
            self.start_audio_streaming(self.current_room)
        else:
            self.mute_button.set(is_on=False)
            self.notify_user('You cannot unmute without joining a room.', label='fail')

    def quit_room(self):
        # self.is_streaming = False
        self.quit_button.toggle()
        self.mute_button.set(is_on=False)
        self.record_button.set(is_on=False, exec=False)
        self.rooms_listbox.close_user_list()
        self.send_command({'action': 'quit_room', 'room': self.current_room})
        self.current_room = None
        self.notify_user('Room quitted.', label='success')

    def update_user_name(self, user_name):
        self.user_name = user_name
        self.user_name_label.configure(text=f'User: {self.user_name}')

    def update_room_users(self, room, user_list):
        # self.notify_user(f'Room {room} now has members: {user_list}')
        self.rooms_listbox.show_user_list(room, user_list)

    # Handler of logging
    def log(self, content, mode='D'):
        if self.show_log:
            if mode == 'I/voice' or mode == 'O/voice':
                return
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
                self.current_room = response['room']
                self.list_rooms()
                # print('start audio_streaming thread')
                self.start_audio_streaming(response['room'])
            elif response['status'] == 'room already joined':
                self.notify_user("Room already joined.", label='neutral')
            else:
                self.notify_user("Failed to join room.", label='fail')

        elif label == 'response_user_name':
            if response['status'] == 'ok':
                self.update_user_name(response['user_name'])
            elif response['status'] == 'conflict':
                self.notify_user('This username has been used.', label='fail')
        elif label == 'update_room_users':
            self.update_room_users(response['room'], response['users'])

        elif label == 'record_start':
            self.record_button.set(is_on=True, exec=False)
        elif label == 'record_end':
            self.record_button.set(is_on=False, exec=False)

        elif label == 'voice': # receive voice of other people
            threading.Thread(target=self.play_audio_thread, args=(response['audio_data'],), daemon=True).start()
        elif label == 'response_sample_rate':
            self.mute_button.set(is_on=False)
            RATE = response['sample_rate']

        elif label == 'terminate':
            self.notify_user("Server Terminated.", label='neutral')

    # Listening for data packets
    def listen(self):
        while True:
            try:
                self.buffer.read(socket=self.socket, handler=self.handle_listener)
            except socket.error:
                return
            
    # Handler
    def handle_listener(self, response, _):
        label = response['label']
        response.pop('label',None)
        self.handle(label, response)

    # Terminate the current connection.
    def terminate(self):
        self.quit_room()
        self.send_command({'action': 'exit', 'room_name': self.current_room})
        if self.error_state:
            exit()

    # Handler in case of losing connection.
    def handle_lost_connection(self):
        if not self.error_state:
            self.notify_user('Lost Connection to server.', label='fail')
            self.error_state = True
            self.root.after(4000, lambda: exit())

if __name__ == '__main__':
    args, help = parse_args()
    if 'h' in args:
        help()
        exit()
    SERVER_HOST = args.ip
    SERVER_PORT = args.port
    ChatClient(SERVER_HOST, SERVER_PORT, show_log='log' in args)