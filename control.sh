#!/bin/bash

export PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin

PID_FILE="/data/app/logviewer/logview.pid"  # pid文件
ACCESS_LOG="/data/app/logviewer/access.log"  # accesslog日志
ERROR_LOG="/data/app/logviewer/error.log"    # 错误日志

usage() {
    echo "Usage: $0 [start|stop|reload|restart]"
    exit 1
}

if [ $# -ne 1 ];then
    usage
fi

start() {
    gunicorn -w 4 --bind 0.0.0.0:8000 main:app -D --max-requests 1000 \
        --error-log=$ERROR_LOG -p $PID_FILE --access-logfile=$ACCESS_LOG
}

reload() {
    kill -1 $(cat $PID_FILE)
}

stop() {
    kill $(cat $PID_FILE)
}

restart() {
    stop
    sleep 2
    start
}

case $1 in
start)
    start
    ;;
stop)
    stop
    ;;
reload)
    reload
    ;;
restart)
    restart
    ;;
*)
    usage
    ;;
esac

