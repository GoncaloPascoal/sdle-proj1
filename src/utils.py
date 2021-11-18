
import binascii, os, zmq

class Pipe:
    def __init__(self, context):
        self.sock_in = context.socket(zmq.PAIR)
        self.sock_out = context.socket(zmq.PAIR)

        addr = 'inproc://%s' % binascii.hexlify(os.urandom(12))
        self.sock_in.bind(addr)
        self.sock_out.connect(addr)