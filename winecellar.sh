#!/usr/bin/env sh
set -eu

APP_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if [ -f "$APP_DIR/.env" ]; then
  set -a
  . "$APP_DIR/.env"
  set +a
fi

PYTHON=${PYTHON:-python3}
HOST=${HOST:-0.0.0.0}
PORT=${PORT:-4173}
PID_FILE=${PID_FILE:-"$APP_DIR/winecellar.pid"}
LOG_FILE=${LOG_FILE:-"$APP_DIR/winecellar.log"}

is_running() {
  [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null
}

start() {
  if is_running; then
    echo "Wine Cellar is already running with PID $(cat "$PID_FILE")."
    return 0
  fi

  cd "$APP_DIR"
  nohup "$PYTHON" server.py --host "$HOST" --port "$PORT" >> "$LOG_FILE" 2>&1 &
  echo $! > "$PID_FILE"
  echo "Wine Cellar started on http://$HOST:$PORT/ with PID $(cat "$PID_FILE")."
  echo "Logs: $LOG_FILE"
}

stop() {
  if ! is_running; then
    rm -f "$PID_FILE"
    echo "Wine Cellar is not running."
    return 0
  fi

  PID=$(cat "$PID_FILE")
  kill "$PID"
  rm -f "$PID_FILE"
  echo "Wine Cellar stopped."
}

status() {
  if is_running; then
    echo "Wine Cellar is running with PID $(cat "$PID_FILE")."
  else
    echo "Wine Cellar is not running."
  fi
}

case "${1:-start}" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  restart)
    stop
    start
    ;;
  status)
    status
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 2
    ;;
esac
