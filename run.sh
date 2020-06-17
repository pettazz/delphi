#!/usr/bin/env bash

export DISPLAY=:0.0

_term() { 
  kill -TERM "$child" 2>/dev/null
}

trap _term SIGTERM

python3 delphi.py > clocko.stdout 2>&1 &

child=$! 
wait "$child"