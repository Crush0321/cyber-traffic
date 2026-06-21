#!/bin/bash
# Wrapper script for launchd — runs Cyber Traffic
export PYTHONPATH="/Volumes/Fanxiang/workspace/cyber-traffic"
exec /opt/homebrew/bin/python3 -m cyber_traffic.app
