#!/usr/bin/env bash

red="\e[1;31m"
green="\e[1;32m"
blue="\e[1;34m"
purple="\e[1;35m"
cyan="\e[1;36m"
reset="\e[0m"

pcolor () {
    echo -e "${2}$1${reset}"
}

pub_port=4000
sub_port=3000

exp1 () {
    p_rpc_port=5000
    s_rpc_port=2000

    pcolor "--- EXPERIMENT 1: DURABLE SUBSCRIPTIONS ---\n" $purple

    python3 proxy.py $pub_port $sub_port &
    svc_pid=$(echo $!)
    python3 publisher.py $p_rpc_port $pub_port &
    pub_pid=$(echo $!)
    python3 subscriber.py 1 $s_rpc_port $sub_port &
    sub_pid=$(echo $!)
    (
        sleep 1
        pcolor "\nSubscribing to topic and sending first message...\n" $cyan

        python3 rpc.py SUB $s_rpc_port test 1>/dev/null
        python3 rpc.py PUT $p_rpc_port test1 1>/dev/null
        python3 rpc.py GET $s_rpc_port test 1>/dev/null
        sleep 0.3
        kill $sub_pid
        pcolor "\nKilled subscriber..." $red
        
        sleep 0.5

        pcolor "Reviving subscriber...\n" $green
        python3 subscriber.py 1 $s_rpc_port $sub_port &
        (
            sub_pid=$(echo $!)
            sleep 0.5

            pcolor "\nPutting second message...\n" $cyan

            python3 rpc.py PUT $p_rpc_port test2 1>/dev/null
            python3 rpc.py GET $s_rpc_port test 1>/dev/null

            pcolor "\nUnsubscribing from topic and sending third message...\n" $cyan

            python3 rpc.py UNSUB $s_rpc_port test 1>/dev/null
            python3 rpc.py PUT $p_rpc_port test3 1>/dev/null
            python3 rpc.py GET $s_rpc_port test
            
            pcolor "\nCleaning up..." $cyan
            kill $svc_pid $pub_pid $sub_pid
            ./clean.sh
            exit
        )
    )
}

exp2 () {
    p_rpc_port=5000
    s_rpc_port=2000

    pcolor "--- EXPERIMENT 2: RECOVER LOST MESSAGES ---\n" $purple

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

        pcolor "Putting 2 messages...\n" $cyan
        python3 rpc.py PUT $p_rpc_port test -i 2

        pcolor "\nReceiving 2 messages...\n" $cyan
        python3 rpc.py GET $s_rpc_port test -i 2
        sleep 0.3

        kill $sub_pid
        pcolor "\nKilled subscriber..." $red

        pcolor "Putting 4 messages...\n" $cyan
        python3 rpc.py PUT $p_rpc_port test_lost -i 4

        pcolor "\nReviving subscriber...\n" $green
        python3 subscriber.py 1 $s_rpc_port $sub_port &
        sub_pid=$(echo $!)
        sleep 0.5

        pcolor "\nReceiving 4 messages...\n" $cyan
        python3 rpc.py GET $s_rpc_port test -i 4
        
        pcolor "\nCleaning up..." $cyan
        kill $svc_pid $pub_pid $sub_pid
        ./clean.sh
        exit
    )
}

exp3 () {
    p_rpc_port=5000
    s_rpc_port=2000

    pcolor "--- EXPERIMENT 3: SERVICE CRASH ---\n" $purple

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
        sleep 0.2

        pcolor "\nPutting the first message...\n" $cyan
        python3 rpc.py PUT $p_rpc_port test1 1>/dev/null
        sleep 0.3
        
        kill $svc_pid
        pcolor "\nKilled service..." $red
        
        pcolor "\nPutting second message (in background)..." $cyan
        python3 rpc.py PUT $p_rpc_port test2 1>/dev/null &

        pcolor "Receiving both messages (in background)...\n" $cyan
        python3 rpc.py GET $s_rpc_port test -i 2 1>/dev/null &

        pcolor "Reviving service...\n" $green
        python3 proxy.py $pub_port $sub_port &
        svc_pid=$(echo $!)
        sleep 0.5

        pcolor "\nCleaning up..." $cyan
        kill $svc_pid $pub_pid $sub_pid
        ./clean.sh
        exit
    )
}

exp4 () {
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
}

exp5 () {
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
}

exp6 () {
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
}

pcolor "Enter the experiment number (1-6)" $blue
echo -n "> "
read exp

case $exp in
    1)
        exp1
        ;;
    2)
        exp2
        ;;
    3)
        exp3
        ;;
    4)
        exp4
        ;;
    5)
        exp5
        ;;
    6)
        exp6
        ;;
    *)
        pcolor "Invalid experiment number!" $red 
        ;;
esac
