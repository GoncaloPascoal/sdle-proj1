
import zmq
from argparse import ArgumentParser

def send_command(ip, port, args):
    context = zmq.Context()
    sock = context.socket(zmq.REQ)
    sock.connect(f'tcp://{ip}:{port}')

    sock.send_json(args)
    print(sock.recv_string())

def main():
    parser = ArgumentParser(description='Utility program to perform RPC on \
            Publisher and Subscriber processes.')

    subparsers = parser.add_subparsers(
        description='Methods offered by the RPC utility.',
        help='name of the method to call',
        dest='method',
        required=True,
    )

    parser_put   = subparsers.add_parser('PUT'  , help='publish one (1) message to a topic')
    parser_get   = subparsers.add_parser('GET'  , help='consume one (1) message from a topic')
    parser_sub   = subparsers.add_parser('SUB'  , help='subscribe to a specific topic')
    parser_unsub = subparsers.add_parser('UNSUB', help='unsubscribe to a specific topic')

    parser_put.add_argument('port', help='port of target publisher')
    parser_put.add_argument('message', help='message to send')
    parser_put.add_argument('--ip', help='ip of target publisher (defaults to localhost)', default='127.0.0.1')

    for subparser in [parser_get, parser_sub, parser_unsub]:
        subparser.add_argument('port', help='port of target subscriber')
        subparser.add_argument('topic', help='topic identifier')
        subparser.add_argument('--ip', help='ip of target subscriber (defaults to localhost)', default='127.0.0.1')

    args = parser.parse_args()

    method_args = {}
    for k in set(vars(args).keys()).difference(['ip', 'port']):
        method_args[k] = getattr(args, k)

    send_command(args.ip, args.port, method_args)

if __name__ == '__main__':
    main()