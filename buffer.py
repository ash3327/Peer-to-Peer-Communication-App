
import json

class Buffer:
    def __init__(self):
        self.sep = '\r\n'
        self.buffer = ''

    def read(self, socket, handler):
        data = socket.recv(4096).decode('utf-8')
        if not data:
            return None
        self.buffer += data
        results = self.buffer.split(self.sep)
        
        self.buffer = results[-1]
        for response in results[:-1]:
            handler(json.loads(response), socket)
    
    def send(self, socket, command):
        socket.send((json.dumps(command)+self.sep).encode('utf-8'))