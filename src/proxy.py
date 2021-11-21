
import zmq

import pickle, os
from collections import deque
from threading import Thread
from argparse import ArgumentParser
from typing import List, Tuple

from utils import Message, save_state

class ServiceState:
    def __init__(self):
        self._counter = 0
        self.topic_queues = {}
        self.topic_pointers = {}
    
    def next_id(self) -> int:
        i = self._counter
        self._counter += 1
        return i

def binary_search(lst: List[Message], val: int) -> int:
    low = 0
    high = len(lst) - 1
    mid = 0

    while low <= high:
        mid = (low + high) // 2

        if lst[mid].i < val:
            low = mid + 1
        elif lst[mid].i > val:
            high = mid - 1
        else:
            return mid

    mid = mid + 1 if lst and lst[-1].i < val else mid
    return mid

def parse_msg(parts: list) -> Tuple[int, str]:
    r_id = int.from_bytes(parts[0], byteorder='big')
    msg = parts[1].decode('utf-8')

    return r_id, msg

def listen(pipe_end: zmq.Socket):
    while True:
        try:
            msg = pipe_end.recv()
            print(f'Message: {msg}')
        except zmq.ZMQError as e:
            if e.errno == zmq.ETERM:
                break

def main():
    parser = ArgumentParser(description='Proxy that acts as an intermediary \
            between publishers and subscribers, so that subscribers and \
            publishers do not need to know about each other.')

    parser.add_argument('publisher_port', type=int, help='port where publishers \
            can connect to')
    parser.add_argument('subscriber_port', type=int, help='port where subscribers \
            can connect to')
    parser.add_argument('-q', '--queue_size', type=int, default=1000, help='maximum \
            queue size for each topic')

    args = parser.parse_args()

    if args.queue_size <= 0:
        print('Error: queue_size argument must be a positive value')
        exit(1)
    
    if args.publisher_port == args.subscriber_port:
        print('Error: publisher port and subscriber port cannot be the same')
        exit(1)

    state = ServiceState()
    if os.path.exists('service.obj'):
        f = open('service.obj', 'rb')
        state = pickle.load(f)

    context = zmq.Context()

    # Socket for publishers
    sock_pub = context.socket(zmq.ROUTER)
    sock_pub.bind(f'tcp://*:{args.publisher_port}')
    
    # Socket for subscribers
    sock_sub = context.socket(zmq.XPUB)
    sock_sub.bind(f'tcp://*:{args.subscriber_port}')

    sock_recover = context.socket(zmq.REP)
    sock_recover.bind(f'tcp://*:{args.subscriber_port + 1}')

    poller = zmq.Poller()
    poller.register(sock_pub, zmq.POLLIN)
    poller.register(sock_sub, zmq.POLLIN)
    poller.register(sock_recover, zmq.POLLIN)

    thread_state = Thread(target=save_state, args=(state, 'service.obj'))
    thread_state.start()

    while True:
        events = poller.poll()

        for event in events:
            socket = event[0]

            if socket is sock_pub:
                parts = sock_pub.recv_multipart()
                _, msg_str = parse_msg(parts)

                msg = Message(state.next_id(), msg_str)
                print(msg)
                sock_sub.send_string(msg.s + ':' + str(msg.i))

                for t, q in state.topic_queues.items():
                    if msg.s.startswith(t):
                        if len(q) == args.queue_size:
                            q.popleft()
                        q.append(msg)

                parts[1] = b''
                sock_pub.send_multipart(parts)
            elif socket is sock_sub:
                msg_b = sock_sub.recv()
                
                if msg_b[0] == 1:
                    # Subscription
                    topic = msg_b[1:].decode('utf-8')
                    state.topic_queues.setdefault(topic, deque())
                elif msg_b[0] == 2:
                    parts = msg_b[1:].decode('utf-8').split(' ')
                    sub_id, msg_id = parts[0], parts[1]
                    print(f'{sub_id} acked message {msg_id}')
            elif socket is sock_recover:
                msg = sock_recover.recv_json()

                r = set()
                for k, v in msg.items():
                    queue = list(state.topic_queues[k])
                    r = r.union(queue[binary_search(queue, v):])
                
                sock_recover.send_pyobj(r)

if __name__ == '__main__':
    main()