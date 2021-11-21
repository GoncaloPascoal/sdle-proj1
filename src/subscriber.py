
import zmq

import pickle, os, copyreg, threading
from threading import Thread
from argparse import ArgumentParser
from concurrent.futures import ThreadPoolExecutor
from queue import Queue

from utils import Message, save_state

NUM_THREADS = 20

def pickle_queue(q):
    q_dct = q.__dict__.copy()
    del q_dct['mutex']
    del q_dct['not_empty']
    del q_dct['not_full']
    del q_dct['all_tasks_done']
    return Queue, (), q_dct

def unpickle_queue(state):
    q = state[0]()
    q.mutex = threading.Lock()
    q.not_empty = threading.Condition(q.mutex)
    q.not_full = threading.Condition(q.mutex)
    q.all_tasks_done = threading.Condition(q.mutex)
    q.__dict__ = state[2]
    return q

class TopicInfo:
    def __init__(self):
        self.last_id = -1
        self.queue = Queue()

class SubscriberState:
    def __init__(self):
        self.topic_to_msgs = {}

state = SubscriberState()

def get(topic: str) -> bool:
    global state

    if topic in state.topic_to_msgs:
        msg = state.topic_to_msgs[topic].queue.get()

        print(f'GET message: {msg}')
        return True

    return False

def sub(sock_proxy: zmq.Socket, topic: str) -> bool:
    global state

    sock_proxy.send(b'\x01' + bytes(topic, 'utf-8'))

    if topic not in state.topic_to_msgs:
        state.topic_to_msgs[topic] = TopicInfo()

    print(f'SUB to topic: {topic}')

def unsub(sock_proxy: zmq.Socket, topic: str) -> bool:
    global state

    sock_proxy.send(b'\x00' + bytes(topic, 'utf-8'))

    if topic in state.topic_to_msgs:
        del state.topic_to_msgs[topic]

    print(f'UNSUB from topic: {topic}')

def handle_get_command(context: zmq.Context, topic: str):
    # Open a Socket for inter-thread comunication
    socket = context.socket(zmq.PUSH)
    socket.connect('inproc://get-socket')

    # Handle the get command
    if not get(topic):
        socket.send_string(f'Error: not subscribed to topic: {topic}')
    else:
        socket.send_string('OK')
    
    socket.close()

def route_msg_to_queues(msg):
    for k, v in state.topic_to_msgs.items():
        if msg.s.startswith(k) and msg.i > v.last_id:
            v.queue.put(msg)
            v.last_id = msg.i

def main():
    global state

    copyreg.pickle(Queue, pickle_queue, unpickle_queue)

    parser = ArgumentParser(description='Process that subscribes to topics and receives messages.')
    
    parser.add_argument('id', help='id of the subscriber')
    parser.add_argument('port', help='subscriber listening port')
    parser.add_argument('proxy_addr', help='address of the proxy to connect to')
    parser.add_argument('proxy_port', type=int, help='port of the proxy to connect to')

    args = parser.parse_args()

    request_backup = False
    path = f'sub{args.id}.obj'
    if os.path.exists(path):
        f = open(path, 'rb')
        state = pickle.load(f)

        if state.topic_to_msgs:
            # Recovered from crash and was subscribed to at least one topic.
            request_backup = True

    context = zmq.Context()

    # Connect to proxy
    sock_proxy = context.socket(zmq.XSUB)
    sock_proxy.connect(f'tcp://{args.proxy_addr}:{args.proxy_port}')
    
    # Restore subscription to topics
    for topic in state.topic_to_msgs:
        sock_proxy.send(b'\x01' + bytes(topic, 'utf-8'))

    if request_backup:
        sock_backup = context.socket(zmq.REQ)
        sock_backup.connect(f'tcp://{args.proxy_addr}:{args.proxy_port + 1}')
        obj = {topic: info.last_id for topic, info in state.topic_to_msgs.items()}
        sock_backup.send_json(obj)
        msgs = sorted(list(sock_backup.recv_pyobj()), key=lambda x: x.i)

        for msg in msgs:
            route_msg_to_queues(msg)

    # Socket for listening to commands
    sock_rpc = context.socket(zmq.REP)
    sock_rpc.bind(f'tcp://*:{args.port}')

    # Socket for listening to get threads
    sock_get = context.socket(zmq.PULL)
    sock_get.bind('inproc://get-socket')

    # Poller to read from the sockets
    poller = zmq.Poller()
    poller.register(sock_proxy, zmq.POLLIN)
    poller.register(sock_rpc  , zmq.POLLIN)
    poller.register(sock_get  , zmq.POLLIN)

    thread_state = Thread(target=save_state, args=(state, f'sub{args.id}.obj'))
    thread_state.start()

    commands = {'GET', 'SUB', 'UNSUB'}
    pool = ThreadPoolExecutor(NUM_THREADS)
    
    print(f'Subscriber #{args.id} online...')

    while True:
        events = poller.poll()

        for event in events:
            socket = event[0]

            if socket is sock_proxy:
                msg_str: str = sock_proxy.recv_string()
                sep_idx = msg_str.rindex(':')
                msg = Message(int(msg_str[sep_idx + 1:]), msg_str[:sep_idx])
                sock_proxy.send(b'\x02' + bytes(args.id + ' ' + str(msg.i), 'utf-8'))
                route_msg_to_queues(msg)
            elif socket is sock_rpc:
                command = sock_rpc.recv_json()

                if (isinstance(command, dict)
                    and set(['method', 'topic']).issubset(command.keys())
                    and command['method'] in commands):
                    method = command['method']
                    topic = command['topic']

                    if method == 'GET':
                        pool.submit(handle_get_command, context, topic)
                        continue
                    elif method == 'SUB':
                        sub(sock_proxy, topic)
                    elif method == 'UNSUB':
                        unsub(sock_proxy, topic)
                    
                    sock_rpc.send_string('OK')
                else:
                    sock_rpc.send_string('Error: malformed command')
            elif socket is sock_get:
                msg: str = sock_get.recv_string()
                sock_rpc.send_string(msg)

if __name__ == '__main__':
    main()
