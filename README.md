# csci3280_2

## Installation

To install this package, perform the following:

1) Execute ```pip3 install -r requirements.txt``` in command prompt.

Note:

1) The application currently only work with computers _in the same network_. 

## Server-Side
To start the server, perform the following:

1) Run ```chat_server.py``` by calling ```python chat_server.py --port <port>```. Use the token ```-h``` to get hints on the arguments.

Notes:

1) You should be able to read the server IP and the port as follows: 
`Initializing Chat Server at IP [10.13.252.5] and port [12345]`

2) You can terminate the server end program and all its associated connections by pressing ```Ctrl+C``` in the command prompt.

## Client-Side
To start the client-side software, perform the following: 

1) Run ```chat_client.py``` by calling ```python chat_client.py --ip <ip> --port <port>```, where the IP and port can be read from the server side.
