#!/bin/bash

APP_NAME="ComfyUI_Workflow_Backend"
APP_DIR="/c/workspace/create_iamge_project/ComfyUI_Workflow_Backend"
VENV_DIR="$APP_DIR/.venv"
PYTHON="$VENV_DIR/bin/python"
UVICORN="$VENV_DIR/bin/uvicorn"
LOGFILE="$APP_DIR/server.log"
PIDFILE="$APP_DIR/uvicorn.pid"
HOST="0.0.0.0"
PORT="9001"

start() {
  echo "▶ Starting $APP_NAME..."
  cd $APP_DIR
  source $VENV_DIR/bin/activate
  nohup $UVICORN app.main:app --host $HOST --port $PORT > "$LOGFILE" 2>&1 &
  echo $! > "$PIDFILE"
  echo "✅ Started with PID $(cat $PIDFILE)"
}

stop() {
  echo "⏹ Stopping $APP_NAME..."
  if [ -f "$PIDFILE" ]; then
    kill -9 $(cat "$PIDFILE") && rm -f "$PIDFILE"
    echo "✅ Stopped"
  else
    echo "⚠️ PID file not found"
  fi
}

restart() {
  echo "🔄 Restarting $APP_NAME..."
  stop
  sleep 1
  start
}

git_pull() {
  echo "🔄 Git pulling..."
  cd $APP_DIR
  git pull origin main
}

status() {
  if [ -f "$PIDFILE" ]; then
    PID=$(cat "$PIDFILE")
    if ps -p $PID > /dev/null; then
      echo "✅ $APP_NAME is running (PID: $PID)"
    else
      echo "⚠️ $APP_NAME is not running (stale PID file)"
      rm -f "$PIDFILE"
    fi
  else
    echo "❌ $APP_NAME is not running"
  fi
}

logs() {
  if [ -f "$LOGFILE" ]; then
    tail -f "$LOGFILE"
  else
    echo "⚠️ Log file not found"
  fi
}

case "$1" in
  start) start ;;
  stop) stop ;;
  restart) restart ;;
  status) status ;;
  logs) logs ;;
  pull|git-pull) git_pull ;;
  *) echo "Usage: $0 {start|stop|restart|status|logs|pull}" ;;
esac 