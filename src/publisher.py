
from argparse import ArgumentParser

def main():
    parser = ArgumentParser(description='Process that publishes messages to topics.')
    parser.add_argument('id', help='id of the publisher')

    args = parser.parse_args()
    
    print(f'Publisher #{args.id} online...')


if __name__ == '__main__':
    main()