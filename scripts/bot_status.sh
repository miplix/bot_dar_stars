#!/bin/bash
PID=$(ps aux | grep '[s]rc.bot' | awk '{print $2}')
if [ -z "$PID" ]; then
    echo "❌ Бот не запущен"
    exit 1
else
    echo "✅ Бот активен"
    echo "PID: $PID"
    ps -p $PID -o pid,command,etime,status 2>/dev/null
    echo "---"
    tail -n 3 bot.log 2>/dev/null || echo "Лог недоступен"
fi
