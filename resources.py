from tkinter import PhotoImage
from PIL import Image, ImageTk

_icons = {
    'side_bar':
    {
        'add_icon': [Image.open("./res/add_icon.png"), None],
        'brand_header': [Image.open("./res/brand_header.png"), None]
    }
}

_colors = {
    'window': 'light gray',
    'side_bar': 'snow2'
}

def get_itm(ic, *list):
    for key in list:
        ic = ic[key]
    return ic

def get_icon(*list_, image_size:int=None):
    ic = get_itm(_icons, *list_)
    icc = ic[0]
    if isinstance(image_size, int):
        icc = icc.resize((image_size, image_size))
    elif isinstance(image_size, (list,tuple)):
        icc = icc.resize(image_size)
    ic[1] = ImageTk.PhotoImage(icc)
    return ic[1]

def get_color(*list):
    return get_itm(_colors, *list)