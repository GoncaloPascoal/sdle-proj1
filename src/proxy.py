
from argparse import ArgumentParser

def main():
    parser = ArgumentParser(description='Proxy that acts as an intermediary \
            between publishers and subscribers, so that subscribers and \
            publishers do not need to know about each other.')

    parser.add_argument('port', type=int, help='port where publishers and \
            subscribers can connect to')
    
    args = parser.parse_args()

if __name__ == '__main__':
    main()