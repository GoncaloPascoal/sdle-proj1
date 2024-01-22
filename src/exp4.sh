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

pcolor "--- EXPERIMENT 4: SERVICE DROPS QUEUES FOR INACTIVE TOPICS ---\n" $purple

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
    pcolor "\nSubscribing to topic (sub2)..." $cyan
    python3 rpc.py SUB $s2_rpc_port test 1>/dev/null
    sleep 0.3

    pcolor "\nKilling sub1..." $red
    kill $sub1_pid

    pcolor "Unsubscribing from topic (sub2)..." $cyan
    python3 rpc.py UNSUB $s2_rpc_port test 1>/dev/null

    pcolor "\nPutting 3 messages..." $cyan
    python3 rpc.py PUT $p_rpc_port test_msg -i 3 1>/dev/null

    pcolor "\nReviving sub1..." $green
    python3 subscriber.py 1 $s1_rpc_port $sub_port &
    sub1_pid=$(echo $!)

    pcolor "\nGetting 2 messages (sub1)..." $cyan
    python3 rpc.py GET $s1_rpc_port -i 2 test 1>/dev/null

    pcolor "\nUnsubscribing from topic (sub1)..." $cyan
    python3 rpc.py UNSUB $s1_rpc_port test 1>/dev/null

    sleep 0.3

    pcolor "\nPutting message (topic inactive, will be discarded)..." $cyan
    python3 rpc.py PUT $p_rpc_port test_inactive 1>/dev/null

    pcolor "\nCleaning up..." $cyan
    kill $svc_pid $pub_pid $sub1_pid $sub2_pid
    ./clean.sh
    exit
)
