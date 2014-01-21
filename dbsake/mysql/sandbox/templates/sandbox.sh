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

version="{{distribution.version}}"
mysqld_safe={{distribution.mysqld_safe}}
mysql={{distribution.mysql}}
datadir={{datadir}}
defaults_file={{defaults_file}}

[ -f /etc/sysconfig/${NAME} ] && . /etc/sysconfig/${NAME}

mysqld_safe_args="
--defaults-file=$defaults_file
--ledir={{distribution.libexecdir}}
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
    nohup $mysqld_safe $mysqld_safe_args "$@" 0<&- &>/dev/null &
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
        shift
        sandbox_start "$@"
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
    shell|mysql)
        shift
        MYSQL_PS1="mysql[sandbox]> " $mysql --defaults-file=$defaults_file "$@"
        ;;
    mysqldump)
        shift
        ${mysql}dump --defaults-file=$defaults_file "$@"
        ;;
    install-service)
        name=${2:-mysql-$version}
        if [[ -e /etc/init.d/${name} ]]; then
            echo "/etc/init.d/${name} already exists. Aborting."
            exit 1
        fi

        if [[ $(type -p chkconfig) ]]; then
            install_cmd="$(type -p chkconfig) --add ${name} && $(type -p chkconfig) ${name} on"
        elif [[ $(type -p update-rc.d) ]]; then
            install_cmd="$(type -p update-rc.d) ${name} defaults"
        else
            echo "Neither chkconfig or update-rc.d was found. Not installing service."
            exit 1
        fi

        echo "+ $(type -p cp) ${0} /etc/init.d/${name}"
        $(type -p cp) ${0} /etc/init.d/${name} || { echo "copying init script failed"; exit 1; }
        echo "+ $install_cmd"
        eval $install_cmd || { echo "installing init script failed"; exit 1; }
        echo "Service installed in /etc/init.d/${name} and added to default runlevels"
        exit 0
        ;;
    *)
        echo "Usage: $0 {start|stop|status|restart|condrestart|try-restart|reload|force-reload}"
        exit 2
        ;;
esac
exit $?
