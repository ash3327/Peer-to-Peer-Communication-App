# List of Request Codes

Please update this document if you have added any request codes.

## Client -> Server

This section is mainly handled by the method ```send_command``` on the client side and ```handle_client``` on the server side.

label | usage | params
---| --- | ---
create | create chat room | room
list | requests a list of chat rooms
join | user joins chat room | room
exit | inform the server to terminate the connection thread

## Server -> Client

This section is mainly handled by the method ```send_data``` on the server side and ```handle``` on the client side.

*Note that on the client side, ```listen``` function specified that the response passed should be encoded in the format of ```utf-8```. Developers need to CHANGE THIS DESCRIPTION DOCUMENT if he changed this implementation.

label | usage | params
--- | --- | ---
created_room | response to action of creating chat room | status [ok, room already exits]<br>room
list_rooms | response to request of list of chat rooms | rooms (list)
join_room | response to action of joining chat room | status [ok, room not found]<br>room



