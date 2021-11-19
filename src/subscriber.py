
import zmq
from argparse import ArgumentParser
from threading import Thread
from concurrent.futures import ThreadPoolExecutor
from queue import SimpleQueue

NUM_THREADS = 20

topic_to_msgs = {}

def get(topic: str) -> bool:
    if topic in topic_to_msgs:
        msg = topic_to_msgs[topic].get()
        print(f'GET message: {msg}')
        return True

    return False

def sub(sock_proxy: zmq.Socket, topic: str) -> bool:
    sock_proxy.setsockopt_string(zmq.SUBSCRIBE, topic)

    if topic not in topic_to_msgs:
        topic_to_msgs[topic] = SimpleQueue()

    print(f'SUB to topic: {topic}')

def unsub(sock_proxy: zmq.Socket, topic: str) -> bool:
    sock_proxy.setsockopt_string(zmq.UNSUBSCRIBE, topic)

    if topic in topic_to_msgs:
        del topic_to_msgs[topic]

    print(f'UNSUB from topic: {topic}')

def handle_command(sock_rpc: zmq.Socket, sock_proxy: zmq.Socket, command: dict):
    commands = {'GET', 'SUB', 'UNSUB'}

    if (isinstance(command, dict)
        and set(['method', 'topic']).issubset(command.keys())
        and command['method'] in commands):
        method = command['method']
        topic = command['topic']

        if method == 'GET':
            if not get(topic):
                sock_rpc.send_string(f'Error: not subscribed to topic: {topic}')
                return
        elif method == 'SUB':
            sub(sock_proxy, topic)
        elif method == 'UNSUB':
            unsub(sock_proxy, topic)
        
        sock_rpc.send_string('OK')
    else:
        sock_rpc.send_string('Error: malformed command')

def rpc_listen(sock_rpc: zmq.Socket, sock_proxy: zmq.Socket):
    pool = ThreadPoolExecutor(NUM_THREADS)

    while True:
        command = sock_rpc.recv_json()
        pool.submit(handle_command(sock_rpc, sock_proxy, command))

def main():
    parser = ArgumentParser(description='Process that subscribes to topics and receives messages.')
    
    parser.add_argument('id', help='id of the subscriber')
    parser.add_argument('port', help='subscriber listening port')
    parser.add_argument('proxy_addr', help='address of the proxy to connect to')
    parser.add_argument('proxy_port', type=int, help='port of the proxy to connect to')

    args = parser.parse_args()

    context = zmq.Context()

    # Connect to proxy
    sock_proxy = context.socket(zmq.SUB)
    sock_proxy.connect(f'tcp://{args.proxy_addr}:{args.proxy_port}')
    
    # Socket for listening to commands
    sock_rpc = context.socket(zmq.REP)
    sock_rpc.bind(f'tcp://*:{args.port}')

    rpc_thread = Thread(target=rpc_listen, args=(sock_rpc, sock_proxy))
    rpc_thread.start()

    print(f'Subscriber #{args.id} online...')

    while True:
        msg: str = sock_proxy.recv_string()

        for t, q in topic_to_msgs.items():
            if msg.startswith(t):
                q.put(msg)


if __name__ == '__main__':
    main()
