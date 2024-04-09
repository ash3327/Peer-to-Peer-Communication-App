from tkinter import PhotoImage
from PIL import Image, ImageTk
import customtkinter as ctk

delimiter = '\r\n'
_icons = {
    'side_bar':
    {
        'add_icon': [Image.open("./res/add_icon.png")], # Format: [Image.open(<path>), (...)].
        'join_room_icon': [Image.open("./res/join_group_icon.png")],
        'room_icon': [Image.open("./res/group_icon.png")],
        'user': [Image.open("./res/user_icon.png")],
        'self': [Image.open("./res/self_icon.png")],
        'brand_header': [Image.open("./res/brand_header.png")]
    },
    'record':
    {
        'start_recording': [Image.open("./res/start_recording.png")],
        'stop_recording': [Image.open("./res/stop_recording.png")],
        'start_playback': [Image.open("./res/start_playback.png")],
        'start_playback': [Image.open("./res/stop_playback.jpg")],
        'mute': [Image.open("./res/mute.png")],
        'unmute': [Image.open("./res/unmute.png")],
        'quit_room': [Image.open("./res/quit_room.png")],
        'share_screen': [Image.open("./res/share_screen.png")],
        'stop_share_screen': [Image.open("./res/stop_share_screen.png")],
    },
    'status':
    {
        'sharing_screen': [Image.open("./res/sharing_screen.png")],
    }
}

_colors = {
    'window': 'light gray',
    'side_bar': {
        'fill': 'snow2',
        'button': {
            'text_color': 'black',
            'inactive': ctk.ThemeManager.theme["CTkButton"]["fg_color"],
            'active': 'SteelBlue2'
        }
    },
    'message': {
        'warning': 'coral1',
        'fail': 'coral1',
        'neutral': 'goldenrod1',
        'success': 'spring green',
        'info': 'dodger blue'
    },
    'record_bar': {
        'fill': 'light gray',
        'button_fill': {
            'on_state': 'white',
            'off_state': 'gray',
            'on_state_hover': 'snow2',
            'off_state_hover': 'dim gray',
            'quit_room': 'orange red',
            'quit_room_hover': 'OrangeRed2'
        }
    }
}

LIST_OF_STREAMING_CODES = [
    'voice', 'update_screen', 'request_screen_data', 
    'screen_share_response', 'response_screen_data',
    'request_update_screen', 'response_update_screen'
]

_mag_ratio = 1.0

def set_ratio(ratio:float):
    global _mag_ratio
    _mag_ratio = ratio

def get_itm(ic, *list):
    for key in list:
        ic = ic[key]
    return ic

def get_icon(*list_, image_size:int=None, rescale:bool=True):
    '''
            Usage: get_icon('side_bar', 'add_icon', image_size=32) 

        ->  _icons = {
                'side_bar': # <---
                {
                    'add_icon': [Image.open("./res/add_icon.png"), None],  # <--------
                    'brand_header': [Image.open("./res/brand_header.png"), None]
                }
            }
    '''
    ic = get_itm(_icons, *list_)
    icc = ic[0]
    mag_ratio = _mag_ratio if rescale else 1.0
    if isinstance(image_size, int):
        image_size = int(image_size*mag_ratio)
        icc = icc.resize((image_size, image_size))
    elif isinstance(image_size, (list,tuple)):
        icc = icc.resize((int(itm*mag_ratio) for itm in image_size))
    ic.append(ImageTk.PhotoImage(icc))
    return ic[-1]

def get_color(*list):
    '''
            Usage: get_color('side_bar', 'add_icon') 

        ->  _colors = {
                'side_bar': # <---
                {
                    'add_icon':'snow2',  # <--------
                    'brand_header':'gray'
                }
            }
    '''
    return get_itm(_colors, *list)

def exec(fun, *args, **kwargs):
    try:
        fun(*args, **kwargs)
    except Exception:
        pass