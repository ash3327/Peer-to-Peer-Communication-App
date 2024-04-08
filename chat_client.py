import argparse

import socket
import threading
import tkinter as tk
import pyaudio
import pyautogui
from PIL import Image, ImageTk
import time
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
RATE = 11025
CHUNK = 1024
FRAME_PER_SECOND = 10

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
        self.has_microphone = True
        self.reopen_audio_stream()
        self.audio_stream_thread = None
        self.is_streaming = False
        self.is_watching_stream = True#False

        # Screen share
        self.is_screen_sharing = False
        self.stream_resolution = (854, 480)
        self.screen_photo = None
        self.buffer_image = None

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
                height=self.submenu_frame.winfo_height()*.65,
                fg_color=resources.get_color('side_bar','fill'),
                border_width=0, corner_radius=0
            )
        self.rooms_listbox.pack(pady=10)

        # --------- INFO AND SETTINGS ---------
        # Chat server details
        self.info_label = tk.Label(
            self.submenu_frame, 
            text=f'Server: \t{self.socket.getpeername()[0]}\n'+\
                 f'Port: \t{self.socket.getpeername()[1]}'+\
                 f'Sample Rate: \t{RATE}', 
            justify='left', bg=resources.get_color('side_bar','fill'))
        self.info_label.pack(side='bottom', anchor='w', padx=5, pady=2)

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
        self.user_name_label.pack(side='bottom')

        # ---------------------------------------
        #               MAIN FRAME
        # ---------------------------------------  
        self.main_frame = tk.Frame(self.root, bg=resources.get_color('window'))
        self.main_frame.place(relx=.25, rely=0, relwidth=.75, relheight=1)

        # Screen display canvas
        self.screen_canvas = tk.Canvas(self.main_frame, bg=resources.get_color('window'))
        self.screen_canvas.pack(fill='both', expand=True, padx=0, pady=0)

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

        # Share screen Button
        self.screen_share_button = ToggleButton(
                self.recording_panel, 
                on_image=resources.get_icon('record','stop_share_screen',image_size=image_size),
                off_image=resources.get_icon('record','share_screen',image_size=image_size),
                on_command=self.share_screen,
                off_command=self.stop_share_screen,
                **button_configs
            )
        self.screen_share_button.pack(side='left', padx=5)

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
        if selected_room is None:
            return
        if selected_room != self.current_room:
            self.handle_join_quit_room()
            self.send_command({'action': 'join', 'room': selected_room, 'old_room': self.current_room})
        else:
            self.notify_user("Room already joined.", label='neutral')
            
    def screen_start_watching(self):
        self.send_command({'action': 'screen_start_watching', 'room': self.current_room})

    def screen_stop_watching(self):
        self.send_command({'action': 'screen_stop_watching', 'room': self.current_room})

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

                    # Send the audio data to the server
                    command = {'action': 'voice', 
                            'audio_data': audio_data,
                            'room_name': self.current_room,}
                    self.send_command(command)

                except Exception as e:
                    print("Error in send_audio_thread:", e)
                    break

    def play_audio_thread(self, audio_data):
        try:
            # Play the received audio data
            audio_data = base64.b64decode(audio_data)
            # print(audio_data[:20])
            self.audio_stream.write(audio_data)
        except OSError as e:
            raise e

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
        if not self.has_microphone:
            self.reopen_audio_stream()
        if not self.has_microphone:
            self.mute_button.set(is_on=False)
            self.notify_user('You don\'t have a microphone.', label='fail')
        elif self.current_room:
            self.notify_user('Unmuted')
            self.is_streaming = True
            self.start_audio_streaming(self.current_room)
        else:
            self.mute_button.set(is_on=False)
            self.notify_user('You cannot unmute without joining a room.', label='fail')

    def share_screen_thread(self):
        self.share_screen_got_feedback = True
        past_time = time.time()
        while self.current_room and self.is_screen_sharing:
            curr_time = time.time()
            if self.share_screen_got_feedback and curr_time-past_time > 1/FRAME_PER_SECOND:
                self.share_screen_got_feedback = False
                self.send_command({'action': 'request_update_screen', 'room_name': self.current_room})
                past_time = curr_time
            time.sleep(.1/FRAME_PER_SECOND)

    def send_share_screen(self):
        if not (self.current_room and self.is_screen_sharing):
            return
        # Capture the screen
        screenshot = pyautogui.screenshot()
        # Resize the screenshot to 480p (854x480)
        screenshot = screenshot.resize(self.stream_resolution)
        # Convert the screenshot image to bytes
        screen_bytes = screenshot.tobytes()
        # Encode the data to base64
        screen_bytes = base64.b64encode(screen_bytes).decode('utf-8')

        self.send_command({'action': 'update_screen', 'room_name': self.current_room, 'screen_data': screen_bytes})
        self.share_screen_got_feedback = True

    def share_screen(self):
        if self.current_room:
            self.send_command({'action': 'screen_share', 'room_name': self.current_room})
        else:
            self.screen_share_button.set(is_on=False)
            self.notify_user("You cannot share screen without joining a room.", label='fail')

    def share_screen_response(self, status):
        if status == 'ok':
            self.notify_user('Now Sharing Screen', label='success')
            self.is_screen_sharing = True

            threading.Thread(target=self.share_screen_thread, daemon=True).start()
        else: # someone else is sharing
            self.notify_user('Another user is sharing the screen', label='fail')
            self.screen_share_button.set(is_on=False)

    def stop_share_screen(self):
        if self.is_screen_sharing:
            self.send_command({'action': 'screen_unshare', 'room_name': self.current_room})
            self.notify_user('Stopped Sharing Screen')
            self.is_screen_sharing = False

    def update_canvas(self, screen_data, room):
        if self.current_room != room:
            return
        try:
            # Decode base64-encoded screen data
            screen_bytes = base64.b64decode(screen_data)

            # Convert bytes to image
            screen_image = Image.frombytes('RGB', self.stream_resolution, screen_bytes)

            # Convert image to PhotoImage for tkinter canvas
            self.screen_photo = ImageTk.PhotoImage(screen_image)

            # If buffer image is not created or its size differs from the screen photo, recreate buffer
            if self.buffer_image is None or self.buffer_image.size != (self.screen_photo.width(), self.screen_photo.height()):
                self.buffer_image = Image.new("RGB", (self.screen_photo.width(), self.screen_photo.height()))
            
            # Draw the screen photo onto the buffer image
            self.buffer_image.paste(screen_image, (0, 0))

            # Clear canvas before updating
            self.screen_canvas.delete("all")

            # Draw buffer image onto the canvas
            self.screen_canvas.create_image(0, 0, anchor='nw', image=self.screen_photo)

            # Keep a reference to the image to prevent it from being garbage collected
            self.screen_canvas.image = self.screen_photo
        except Exception as e:
            print('Error updating canvas:', e)

    def clear_canvas(self):
        self.screen_canvas.delete("all")
        # print('cleared canvas')

    def quit_room(self):
        # self.is_streaming = False
        self.handle_join_quit_room()
        self.quit_button.toggle()
        self.rooms_listbox.close_user_list()
        self.send_command({'action': 'quit_room', 'room': self.current_room})
        self.current_room = None
        self.notify_user('Room quitted.', label='success')

    def handle_join_quit_room(self):
        self.clear_canvas()
        self.screen_stop_watching()
        self.screen_share_button.set(is_on=False)
        self.mute_button.set(is_on=False)
        self.record_button.set(is_on=False, exec=False)

    def update_user_name(self, user_name):
        self.user_name = user_name
        self.user_name_label.configure(text=f'User: {self.user_name}')

    def update_room_users(self, room, user_list):
        # self.notify_user(f'Room {room} now has members: {user_list}')
        self.rooms_listbox.show_user_list(room, user_list)

    def set_sample_rate(self, sample_rate):
        global RATE
        self.mute_button.set(is_on=False)
        RATE = sample_rate

        self.info_label.configure(
            text=f'Server: \t{self.socket.getpeername()[0]}\n'+\
                 f'Port: \t{self.socket.getpeername()[1]}\n'+\
                 f'Rate: \t{RATE}'
        )
        self.reopen_audio_stream()

    def reopen_audio_stream(self):
        if hasattr(self, 'audio_stream') and self.audio_stream:
            self.audio_stream.close()
        try:
            self.audio_stream = self.paudio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, output=True, frames_per_buffer=CHUNK)
            self.has_microphone = True
        except OSError:
            self.audio_stream = self.paudio.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=False, output=True, frames_per_buffer=CHUNK)
            self.has_microphone = False

    # Handler of logging
    def log(self, content, mode='D'):
        if self.show_log:
            if len(mode) >= 2 and mode[2:] in resources.LIST_OF_STREAMING_CODES:
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
                self.clear_canvas()
                self.list_rooms()
                self.screen_start_watching()
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
            self.set_sample_rate(response['sample_rate'])

        elif label == 'terminate':
            self.notify_user("Server Terminated.", label='neutral')
        elif label == 'response_update_screen':
            if response['status'] == 'ok':
                self.send_share_screen()
        elif label == 'response_screen_data':
            self.update_canvas(response['screen_data'], response['room'])
        elif label == 'clear_canvas':
            self.clear_canvas()
        elif label == 'screen_share_response':
            self.share_screen_response(response['status'])

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