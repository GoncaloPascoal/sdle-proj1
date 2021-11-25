
Disclaimer: the service was tested using Python 3.8.10. Using an earlier version
of Python may cause issues.

--- PREREQUISITES ---

Install the pyzmq package using Pip (Python's package manager), by executing the
following command:

- GNU/LINUX:
pip3 install pyzmq

- WINDOWS
pip install pyzmq

--- RUNNING THE APPLICATIONS ---

Since we implemented our service using Python, which is an intepreted language, 
no compilation is required.

Our service consists of four main applications: the service (proxy.py), the
publisher client (publsiher.py), the subscriber client (subscriber.py) and the
test application (rpc.py).

Information about the command line arguments of each application can be displayed
using the following command (replace app_name with one of the four file names
mentioned previously):

- GNU/LINUX:
python3 app_name.py -h

- WINDOWS:
python app_name.py -h

--- COMMAND LINE ARGUMENTS ---

This section contains a list of the command line arguments of each program.
Be careful not to reuse bound ports when running several programs on the same
machine, and be aware that the service will also bind the port given by 
subscriber_port + 1 (for crash recovery).

- Service (proxy.py)
proxy.py [-h] [-q QUEUE_SIZE] publisher_port subscriber_port

- Publisher (publisher.py)
publisher.py [-h] [--proxy_addr ADDR] port proxy_port

- Subscriber (subscriber.py)
subscriber.py [-h] [--proxy_addr ADDR] id port proxy_port

- Test Application (rpc.py)
rpc.py [-h] {PUT,GET,SUB,UNSUB} ...
    rpc.py PUT [-h] [--ip ADDR] [-i I] [-d D] port message
    rpc.py GET [-h] [--ip ADDR] [-i I] [-d D] port topic
    rpc.py SUB [-h] [--ip ADDR] port topic
    rpc.py UNSUB [-h] [--ip ADDR] port topic