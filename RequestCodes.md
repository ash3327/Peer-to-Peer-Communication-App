# List of Request Codes

Please update this document if you have added any request codes.

## Client -> Server

This section is mainly handled by the method ```send_command``` on the client side and ```handle_client``` on the server side.

label | usage | params
---| --- | ---
create | create chat room | room
list | requests a list of chat rooms
join | user joins chat room | room
quit_room | quit the current room | room
request_user_name | request for changing a user name | user_name<br>room
voice | stream audio | audio_data, room_name
record_start | start recording | room_name
record_end | end recording | room_name
request_sample_rate | request for the sample rate used
screen_start_watching | | room
screen_stop_watching | | room
exit | inform the server to terminate the connection thread

## Server -> Client

This section is mainly handled by the method ```send_data``` on the server side and ```handle``` on the client side.

*Note that on the client side, ```listen``` function specified that the response passed should be encoded in the format of ```utf-8```. Developers need to CHANGE THIS DESCRIPTION DOCUMENT if he changed this implementation.

label | usage | params
--- | --- | ---
created_room | response to action of creating chat room | status [ok, room already exits]<br>room
list_rooms | response to request of list of chat rooms | rooms (dict in the format {room_name: is_member})
join_room | response to action of joining chat room | status [ok, room not found, room already joined]<br>room
voice | stream audio | audio data
response_user_name | response for changing a user name | status<br>user_name
update_room_users | update the list of users in that room | room<br>users
record_start | start recording notification | room_name
record_end | end recording notification | room_name
response_sample_rate | response for the sample rate used | sample_rate
response_screen_data | | screen_data<br>room
terminate | notify the client that the server is going offline



