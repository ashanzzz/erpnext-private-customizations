@echo off
title 启动 Edge 调试模式 (端口 9222)
echo 正在启动 Edge 调试模式...
start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --remote-debugging-port=9222 --user-data-dir="C:\edge_debug_profile" "http://192.168.8.11:6888/desk/my-business"
echo Edge 调试模式已启动，请在打开的 Edge 窗口中操作。
exit
