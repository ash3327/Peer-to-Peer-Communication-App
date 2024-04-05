import tkinter as tk
import customtkinter as ctk

import resources

# reference: official documentations and official github examples
class RoomsPanel(ctk.CTkScrollableFrame):
    def __init__(self, master, button_style, join_room_command, **kwargs):
        super().__init__(master, **kwargs)
        self.widget_list = list()
        self.widget_dict = dict()
        self.button_style = button_style
        self.join_room_command = join_room_command
        self.active = None

    def insert(self, pos, room_name, is_member=False):
        if pos == tk.END:
            pos = len(self.widget_list)

        room_button = ctk.CTkButton(
                self, 
                image=resources.get_icon('side_bar','room_icon' if is_member else 'join_room_icon',image_size=32), 
                text=room_name, 
                command=lambda: self.call(room_name),
                **self.button_style
            )
        room_button.pack()#pady=5)
        self.widget_list.insert(pos, [room_name, room_button])
        self.widget_dict.update({room_name: room_button})

    def call(self, room_name):
        self.active = room_name
        self.join_room_command(selected_room=room_name)

    def update(self, room_name, is_member=False):
        if room_name not in self.widget_dict:
            self.insert(tk.END, room_name, is_member)
        else:
            self.widget_dict[room_name].configure(image=resources.get_icon('side_bar','room_icon' if is_member else 'join_room_icon',image_size=32))

    def remove(self, room_name):
        for room_info in self.widget_list:
            room, room_btn = room_info
            if room == room_name:
                room_btn.destroy()
                self.widget_list.remove(room_info)
                return
            
    def delete(self, start, end):
        if end == tk.END:
            end = len(self.widget_list)
        clear_all = end-start == len(self.widget_list)
        for room_info in self.widget_list[start:end]:
            room, room_btn = room_info
            room_btn.pack_forget()
            room_btn.destroy()
            if not clear_all:
                self.widget_list.remove(room_info)
        if clear_all:
            self.widget_list.clear()

    def get(self, pos):
        if pos == tk.ACTIVE:
            return self.active
        return self.widget_list[pos]
        

    