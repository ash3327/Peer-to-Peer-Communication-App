## Developer Notes:
1) Please __update the requirements.txt__ when a new library is installed. 
2) Please __include the installation steps in README.md__ when a new library is installed not using conda or pip, especially when ```git clone``` calls are used, or when users have to manually download some packages themselves from websites.
3) Please leave comments on how each function is used, including the parameters and arguments it receive.

> [!CAUTION]
> 1) Encountered Potential Bug: When the requests are sent too frequently, two requests can got mixed up into one section of length 1024, which can then cause error in reading the commands.
>    - In the log, this sometimes show up as follows:
>    - ```E/error                 : 10.13.252.5 39993     : {"action": "create", "room": "bye"}{"action": "list"}```
>    - Note: This error is NOT HANDLED YET. I temporarily skipped those packets that caused problems. This may cause losing of packages in later implementations of functions.
>    - Thoughts on how to fix: Use a buffer. [Reference: first reply of https://stackoverflow.com/questions/67825653/how-can-i-properly-receive-data-with-a-tcp-python-socket-until-a-delimiter-is-fo]

> [!NOTE]
> Problem: When a client terminates connection, the reference of the client socket inside the list of room members is not removed.

## To Do:

1) Chat Room Creation and Joining (In progress)
    - Note: For the GUI, please try to put all the image and color references in the ```resources.py``` file.

2) Multi-user Voice Chat

3) Recording

## Enhancements (?): 

1) Real-time video streaming:

2) Karaoke system

3) Voice change

4) Virtual characters

## Notes:

1) Checking IP: Run ```netstat -ano | findStr "12345"``` in command prompt for checking the existence of port 12345.

## Developer Notes:

1) Threads with ```deamon=True``` as parameter will kill itself when the main thread terminates.