#!/bin/bash
# Repeatedly request url from the server and record success/delay

PORT=${PORT-9080}
LOG=${LOG-availability.log}
HOST=${HOST-localhost}
WAIT=60

function log()
{
# echo "$(date -Iseconds) $@"
echo "$(date -Iseconds) $@" >> $LOG
}

function on_sigint
{
log manual interrupt
exit 0
}

trap on_sigint SIGINT

URLS=(/obu_server.zip.sig /notexist /)

while true ; do
  url=$HOST:${PORT}${URLS[$((RANDOM*${#URLS[@]}/32768))]}
  log $url
  curl --connect-timeout 5 -sS "$url" >/dev/null
  rc=$?
  log rc=$rc
  sleep $WAIT
done
