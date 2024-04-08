
import json

class Buffer:
    def __init__(self):
        self.sep = '\r\n'
        self.buffer = ''

    def read(self, socket, handler):
        try:
            data = socket.recv(4096).decode('utf-8')
            if not data:
                return None
            self.buffer += data
            results = self.buffer.split(self.sep)
            
            self.buffer = results[-1]
            for response in results[:-1]:
                try:
                    res = json.loads(response)
                except Exception:
                    continue
                handler(res, socket)
        except:
            pass
    
    def send(self, socket, command):
        try:
            socket.send((self.sep+json.dumps(command)+self.sep).encode('utf-8'))
        except Exception as e:
            print('Error 31:',e)