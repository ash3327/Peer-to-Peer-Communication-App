from tkinter import PhotoImage
from PIL import Image, ImageTk

delimiter = '\r\n'
_icons = {
    'side_bar':
    {
        'add_icon': [Image.open("./res/add_icon.png"), None], # Format: [Image.open(<path>), None].
        'join_room_icon': [Image.open("./res/join_group_icon.png"), None],
        'room_icon': [Image.open("./res/group_icon.png"), None],
        'brand_header': [Image.open("./res/brand_header.png"), None]
    }
}

_colors = {
    'window': 'light gray',
    'side_bar': {
        'fill': 'snow2',
        'button': {
            'text_color': 'black'
        }
    },
    'message': {
        'warning': 'coral1',
        'fail': 'coral1',
        'neutral': 'goldenrod1',
        'success': 'spring green',
        'info': 'dodger blue'
    }
}

def get_itm(ic, *list):
    for key in list:
        ic = ic[key]
    return ic

def get_icon(*list_, image_size:int=None):
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
    if isinstance(image_size, int):
        icc = icc.resize((image_size, image_size))
    elif isinstance(image_size, (list,tuple)):
        icc = icc.resize(image_size)
    ic[1] = ImageTk.PhotoImage(icc)
    return ic[1]

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