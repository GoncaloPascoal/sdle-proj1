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
s1_rpc_port=2000
s2_rpc_port=2500

pcolor "--- EXPERIMENT 5: SUBSCRIBER RECOVERS WITH NO MESSAGE RECEIVED PREVIOUSLY ---\n" $purple

python3 proxy.py $pub_port $sub_port &
svc_pid=$(echo $!)
python3 publisher.py $p_rpc_port $pub_port &
pub_pid=$(echo $!)
python3 subscriber.py 1 $s1_rpc_port $sub_port &
sub1_pid=$(echo $!)
python3 subscriber.py 2 $s2_rpc_port $sub_port &
sub2_pid=$(echo $!)
sleep 1
(
    pcolor "\nSubscribing to topic (sub1)..." $cyan
    python3 rpc.py SUB $s1_rpc_port test 1>/dev/null
    sleep 0.3

    pcolor "\nPutting 3 messages..." $cyan
    python3 rpc.py PUT $p_rpc_port test_before2 -i 3 1>/dev/null

    pcolor "\nSubscribing to topic (sub2)..." $cyan
    python3 rpc.py SUB $s2_rpc_port test 1>/dev/null
    sleep 0.3

    pcolor "\nKilling sub2..." $red
    kill $sub2_pid

    pcolor "\nPutting 4 messages..." $cyan
    python3 rpc.py PUT $p_rpc_port test_after2 -i 4 1>/dev/null

    pcolor "\nReviving sub2..." $green
    python3 subscriber.py 2 $s2_rpc_port $sub_port &
    sub2_pid=$(echo $!)
    sleep 0.1

    pcolor "\nGetting 4 messages (sub2)..." $cyan
    python3 rpc.py GET $s2_rpc_port -i 4 test 1>/dev/null

    pcolor "\nCleaning up..." $cyan
    kill $svc_pid $pub_pid $sub1_pid $sub2_pid
    ./clean.sh
    exit
)
