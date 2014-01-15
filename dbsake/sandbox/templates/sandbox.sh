#!/bin/bash

### BEGIN INIT INFO
# Provides: mysql-sandbox
# Required-Start: $local_fs $network $remote_fs
# Required-Stop: $local_fs $network $remote_fs
# Default-Start:  2 3 4 5
# Default-Stop: 0 1 6
# Short-Description: start and stop a mysql sandboxed instance
# Description: Start mysql sandboxed instance setup by dbsake
### END INIT INFO

NAME=${0##*/}
if [[ ${NAME:0:1} = "S" || ${NAME:0:1} = "K" ]]
then
    NAME=${NAME:3}
fi
START_TIMEOUT=300
STOP_TIMEOUT=300

mysqld_safe={{mysqld_safe}}
mysql={{mysql}}
sandbox_root={{sandbox_root}}
datadir=$sandbox_root/data
defaults_file=$sandbox_root/my.sandbox.cnf

[ -f /etc/sysconfig/${NAME} ] && . /etc/sysconfig/${NAME}

mysqld_safe_args="
--defaults-file=$defaults_file
--datadir=$datadir
--pid-file=$datadir/mysql.pid
--socket=$datadir/mysql.sock
--log-error=$datadir/mysqld.log"

sandbox_start() {
    if [[ -s "${datadir}/mysqld.pid" ]]
    then
        echo "Starting sandbox: [OK]"
        return 0
    fi
    echo -n "Starting sandbox: "
    # close stdin (0) and redirect stdout/stderr to /dev/null
    nohup $mysqld_safe $mysqld_safe_args 0<&- &>/dev/null &
    local start_timeout=${START_TIMEOUT}
    until [[ -S "${datadir}/mysql.sock" || $start_timeout -le 0 ]]
    do
      sleep 1
      (( start_timeout-- ))
      kill -0 $! &>/dev/null || break
    done
    [[ -S "${datadir}/mysql.sock" ]]
    ret=$?
    [[ $ret -eq 0 ]] && echo "[OK]" || echo "[FAILED]"
    return $ret
}

sandbox_status() {
    if [[ -s "${datadir}/mysql.pid" ]]
    then
        { pid=$(<"${datadir}/mysql.pid"); } 2>/dev/null
    fi
    [[ -n "${pid}" ]] && kill -0 "${pid}" &>/dev/null
    ret=$?
    [[ $ret -eq 0 ]] && echo "mysqld ($pid) is running." || echo "mysqld is not running"
    return $ret
}

sandbox_stop() {
    if [[ -s "${datadir}/mysql.pid" ]]
    then
        { pid=$(<"${datadir}/mysql.pid"); } 2>/dev/null
    fi

    if [[ -z "$pid" ]]
    then
        echo "sandbox is stopped"
        return 0
    fi

    kill -TERM "$pid"
    local stop_timeout=${STOP_TIMEOUT}
    until [[ $stop_timeout -le 0 ]]
    do
        kill -0 "$pid" &>/dev/null || break
        sleep 1
        (( stop_timeout-- ))
    done
    ! kill -0 "$pid" &>/dev/null
    ret=$?
    [[ $ret -eq 0 ]] && echo "Stopping sandbox: [OK]" || echo "Stopping sandbox: [FAILED]"
    return $ret
}

case $1 in
    start)
        sandbox_start
        ;;
    status)
        sandbox_status
        ;;
    stop)
        sandbox_stop
        ;;
    restart|cond-restart|try-restart|force-reload)
        sandbox_stop
        sandbox_start
        ;;
    reload)
        exit 3
        ;;
    shell)
        shift
        MYSQL_PS1="mysql[sandbox]> " $mysql --defaults-file=$defaults_file "$@"
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart|condrestart|try-restart|reload|force-reload}"
        exit 2
        ;;
esac
exit $?
