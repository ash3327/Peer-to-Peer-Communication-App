# csci3280_2

> [!NOTE]
> Developer may need to call their ```pip install -r requirements.txt``` again after this update to support the use of fancier GUI through the ```customtkinter``` package. <br>
>   - For more references on how to use this package, please refer to https://github.com/TomSchimansky/CustomTkinter.<br>
>   - But actually you can still stick with the normal ```tkinter``` for basic UI.

> [!IMPORTANT]
> Please refer to ```JobAllocation.md``` for the latest (potential) bugs yet to be fixed.

## Installation

To install this package, perform the following:

1) Execute ```pip3 install -r requirements.txt``` in command prompt.

> [!CAUTION]
>
> 2) To allow the usage of the audio-to-text function, you need to manually install the ffmpeg package. (Note that we only allow English transcription for now)
>
>    If you're using conda, then do ```conda install ffmpeg``` (advised).
>
>       <details>
>       <summary>More:</summary>
>
>       If your OS is linux, then do ```sudo apt install ffmpeg```.
>
>    If your OS is windows, you can download FFMPEG from the official download page: https://ffmpeg.org/download.html#build-windows. (Personally, we used the version ffmpeg-master-latest-win64-gpl.zip provided in https://github.com/BtbN/FFmpeg-Builds/releases)
>
>    If your OS is MacOS, you can also download it from the official download page: https://ffmpeg.org/download.html#build-mac.
>
>    Note that if you downloaded the executable from the website, you'll have to manually move it (```ffmpeg.exe``` in the unzipped ```bin``` subfolder) to your script's root directory (in the SAME layer as other .py files) (or add it to PATH).</details>

Note:

1) The application currently only work with computers _in the same local area network_ due to port forwarding. 

> [!CAUTION]
>
> 2) Please TURN OFF Windows Defender Firewall AND Windows Firewall (or any firewalls) in the private network before using.

## Server-Side
To start the server, perform the following:

1) Run ```chat_server.py``` by calling ```python chat_server.py --port <port>```. 

    - Use the token ```-h``` to get hints on the arguments.
    - Use the token ```-l``` to show logs of all communication between server and client.
    - Press ```Ctrl+C``` for the following:
        - check the ip and port of the server, or
        - terminate the server

Notes:

1) You should be able to read the server IP and the port as follows: 
`Initializing Chat Server at IP [10.13.252.5] and port [12345]`

2) You can terminate the server end program and all its associated connections by pressing ```Ctrl+C``` in the command prompt.

3) Sampling Frequency can be set with `-r <frequency>` (Default = 11025)

## Client-Side
To start the client-side software, perform the following: 

1) Run ```chat_client.py``` by calling ```python chat_client.py --ip <ip> --port <port>```, where the IP and port can be read from the server side.

    - Use the token ```-h``` to get hints on the arguments.
    - Use the token ```-l``` to show logs of all communication between server and client.

<details>
<summary>Functionalities:</summary>

1) Users can click on 'new room' button to enter the name of the room now.
![](readme_res/image-1.png)
2) users can click on the room names to join the room directly now.
![](readme_res/image.png)
3) Users can mute/unmute his/her voices, and also quit room now.
![](readme_res/image-2.png)

</details>

## Logs

<details>
<summary>Example of server side log:</summary>

    Initializing Chat Server at IP [10.13.252.5] and port [12345]
    Starting server...
    Accepted request from: 10.13.252.5 port 1749
    I/list                  : 10.13.252.5 1749      : {'action': 'list'}
    O/list_rooms            : 10.13.252.5 1749      : {'rooms': []}
    I/create                : 10.13.252.5 1749      : {'action': 'create', 'room': 'hello'}
    O/created_room          : 10.13.252.5 1749      : {'status': 'ok', 'room': 'hello'}
    I/list                  : 10.13.252.5 1749      : {'action': 'list'}
    O/list_rooms            : 10.13.252.5 1749      : {'rooms': ['hello']}
    I/create                : 10.13.252.5 1749      : {'action': 'create', 'room': 'world'}
    O/created_room          : 10.13.252.5 1749      : {'status': 'ok', 'room': 'world'}
    I/list                  : 10.13.252.5 1749      : {'action': 'list'}
    O/list_rooms            : 10.13.252.5 1749      : {'rooms': ['hello', 'world']}
    I/join                  : 10.13.252.5 1749      : {'action': 'join', 'room': 'world'}
    O/join_room             : 10.13.252.5 1749      : {'status': 'room already joined', 'room': 'world'}
    I/exit                  : 10.13.252.5 1749      : {'action': 'exit'}
    Ended request from: 10.13.252.5 port 1749
    Accepted request from: 10.13.252.5 port 1819
    I/list                  : 10.13.252.5 1819      : {'action': 'list'}
    O/list_rooms            : 10.13.252.5 1819      : {'rooms': ['hello', 'world']}
    Accepted request from: 10.13.252.5 port 1829
    I/list                  : 10.13.252.5 1829      : {'action': 'list'}
    O/list_rooms            : 10.13.252.5 1829      : {'rooms': ['hello', 'world']}
    I/exit                  : 10.13.252.5 1829      : {'action': 'exit'}
    Ended request from: 10.13.252.5 port 1829
    I/exit                  : 10.13.252.5 1819      : {'action': 'exit'}
    Ended request from: 10.13.252.5 port 1819

</details>

<details>
<summary>Example of client side log:</summary>

    O/list                  : {'action': 'list'}
    I/list_rooms            : {'rooms': ['hello', 'world']}
    O/create                : {'action': 'create', 'room': 'room 4'}
    O/list                  : {'action': 'list'}
    I/created_room          : {'status': 'ok', 'room': 'room 4'}
    Room 'room 4' created successfully.
    I/list_rooms            : {'rooms': ['hello', 'world', 'room 4']}
    O/join                  : {'action': 'join', 'room': 'world'}
    I/join_room             : {'status': 'ok', 'room': 'world'}
    Joined room 'world' successfully.
    O/join                  : {'action': 'join', 'room': 'world'}
    I/join_room             : {'status': 'room already joined', 'room': 'world'}
    Room already joined.
    O/create                : {'action': 'create', 'room': 'room 4'}
    O/list                  : {'action': 'list'}
    I/created_room          : {'status': 'room already exists', 'room': 'room 4'}
    Failed to create room.
    I/list_rooms            : {'rooms': ['hello', 'world', 'room 4']}
    
</details>