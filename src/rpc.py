
from argparse import ArgumentParser

def main():
    parser = ArgumentParser(description='Utility program to perform RPC on \
            Publisher and Subscriber processes.')
    
    subparsers = parser.add_subparsers(
        description='Methods offered by the RPC utility.',    
        help='name of the method to call',
        dest='method',
    )

    parser_put   = subparsers.add_parser('PUT'  , help='publish one (1) message to a topic')
    parser_get   = subparsers.add_parser('GET'  , help='consume one (1) message from a topic')
    parser_sub   = subparsers.add_parser('SUB'  , help='subscribe to a specific topic')
    parser_unsub = subparsers.add_parser('UNSUB', help='unsubscribe to a specific topic')

    parser_put.add_argument('publisher_id', help='id of the publisher')
    parser_put.add_argument('topic_id', help='id of the topic')
    parser_put.add_argument('message', help='message to send')

    for subparser in [parser_get, parser_sub, parser_unsub]:
        subparser.add_argument('ip', help='ip of target client')
        subparser.add_argument('port', help='port of target client')
        subparser.add_argument('subscriber_id', help='id of the subscriber')
        subparser.add_argument('topic_id', help='id of the topic')

    args = parser.parse_args()

if __name__ == '__main__':
    main()