
import zmq
from argparse import ArgumentParser
from time import sleep

def send_command(ip, port, args, it, delay_ms):
    context = zmq.Context()
    sock = context.socket(zmq.REQ)
    sock.connect(f'tcp://{ip}:{port}')

    for _ in range(it):
        sock.send_json(args)
        print(sock.recv_string())
        sleep(delay_ms / 1000)

    sock.close()
    context.destroy()

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
    parser_put.add_argument('--ip', help='ip of target publisher (defaults to localhost)',
        default='127.0.0.1', metavar='ADDR')

    for subparser in [parser_get, parser_sub, parser_unsub]:
        subparser.add_argument('port', help='port of target subscriber')
        subparser.add_argument('topic', help='topic identifier')
        subparser.add_argument('--ip', help='ip of target subscriber (defaults to localhost)',
            default='127.0.0.1', metavar='ADDR')

    for subparser in [parser_get, parser_put]:
        subparser.add_argument('-i', '--iter', type=int, help='number of iterations', default=1, metavar='I')
        subparser.add_argument('-d', '--delay', type=int, help='delay between iterations (in ms)', default=0, metavar='D')

    args = parser.parse_args()

    if args.iter < 1:
        print('Error: number of iterations must be higher than 0')
        exit(1)
    
    if args.delay < 0:
        print('Error: delay between iterations must be positive')
        exit(1)

    method_args = {}
    for k in set(vars(args).keys()).difference(['ip', 'port', 'iter', 'delay']):
        method_args[k] = getattr(args, k)

    send_command(args.ip, args.port, method_args, args.iter, args.delay)

if __name__ == '__main__':
    main()