#!/usr/bin/env bash

red="\e[1;31m"
green="\e[1;32m"
cyan="\e[1;36m"
purple="\e[1;35m"
reset="\e[0m"

pcolor () {
    echo -e "${2}$1${reset}"
}

pub_port=4000
sub_port=3000

p_rpc_port=5000
s_rpc_port=2000

pcolor "--- EXPERIMENT 6: GET OPERATION WHILE SERVICE IS DOWN ---\n" $purple

python3 proxy.py $pub_port $sub_port &
svc_pid=$(echo $!)
python3 publisher.py $p_rpc_port $pub_port &
pub_pid=$(echo $!)
python3 subscriber.py 1 $s_rpc_port $sub_port &
sub_pid=$(echo $!)
sleep 1
(
    pcolor "\nSubscribing to topic...\n" $cyan
    python3 rpc.py SUB $s_rpc_port test 1>/dev/null
    sleep 0.3

    pcolor "\nPutting 3 messages...\n" $cyan
    python3 rpc.py PUT $p_rpc_port test -i 3 1>/dev/null
    sleep 0.5

    kill $svc_pid
    pcolor "\nKilled service..." $red

    pcolor "\nReceiving 3 messages...\n" $cyan
    python3 rpc.py GET $s_rpc_port test -i 3 1>/dev/null
    
    pcolor "\nCleaning up..." $cyan
    kill $pub_pid $sub_pid
    ./clean.sh
    exit
)
