
import zmq
from argparse import ArgumentParser
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

    # Poller to read from the sockets
    poller = zmq.Poller()
    poller.register(sock_proxy, zmq.POLLIN)
    poller.register(sock_rpc  , zmq.POLLIN)

    commands = {'GET', 'SUB', 'UNSUB'}
    # pool = ThreadPoolExecutor(NUM_THREADS) # TODO: make sure the sockets are thread safe
    
    print(f'Subscriber #{args.id} online...')

    while True:
        events = poller.poll()

        for event in events:
            socket = event[0]

            if socket is sock_proxy:
                msg: str = sock_proxy.recv_string()

                for t, q in topic_to_msgs.items():
                    if msg.startswith(t):
                        q.put(msg)
            elif socket is sock_rpc:
                command = sock_rpc.recv_json()

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
                #pool.submit(handle_command, context, args.port, args.proxy_addr, args.proxy_port, command)


if __name__ == '__main__':
    main()
