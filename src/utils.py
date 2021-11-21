
import binascii, pickle, os, zmq
from time import sleep

def save_state(state, path, sleep_ms=250):
    while True:
        f = open(path, 'wb')
        pickle.dump(state, f)
        sleep(sleep_ms / 1000)

class Pipe:
    def __init__(self, context: zmq.Context):
        self.sock_in = context.socket(zmq.PAIR)
        self.sock_out = context.socket(zmq.PAIR)

        addr = 'inproc://%s' % binascii.hexlify(os.urandom(12))
        self.sock_in.bind(addr)
        self.sock_out.connect(addr)

class Message:
    def __init__(self, i: int, s: str):
        self.i = i
        self.s = s
    
    def __str__(self) -> str:
        return '[' + str(self.i) + '] - ' + self.s