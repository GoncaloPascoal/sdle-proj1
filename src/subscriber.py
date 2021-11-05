
from argparse import ArgumentParser

def main():
    parser = ArgumentParser(description='Process that subscribes to topics and receives messages.')
    parser.add_argument('id', help='id of the subscriber')

    args = parser.parse_args()

    print(f'Subscriber #{args.id} online...')

if __name__ == '__main__':
    main()
