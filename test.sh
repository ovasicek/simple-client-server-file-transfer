#!/bin/bash

# start the server in the background

rm -rf uploaded_files
python server.py > /dev/null &
PID="$!"
echo "server at $PID"
echo
sleep 1


# test file uploads

rm -f uploaded_files/*

echo -n "file.txt         "
python client.py test_files/file.txt > /dev/null || true
if diff -q uploaded_files/file.txt test_files/file.txt > /dev/null; then echo "PASS"; else echo "FAIL"; fi
rm -f uploaded_files/file.txt

echo -n "file-empty.txt   "
python client.py test_files/file-empty.txt > /dev/null || true
if diff -q uploaded_files/file-empty.txt test_files/file-empty.txt > /dev/null; then echo "PASS"; else echo "FAIL"; fi
rm -f uploaded_files/file-empty.txt

echo -n "picture.png      "
python client.py test_files/picture.png > /dev/null || true
if diff -q uploaded_files/picture.png test_files/picture.png > /dev/null; then echo "PASS"; else echo "FAIL"; fi
rm -f uploaded_files/picture.png

echo -n "file-50mb.txt   "
python client.py test_files/file-50mb.txt > /dev/null || true
if diff -q uploaded_files/file-50mb.txt test_files/file-50mb.txt > /dev/null; then echo "PASS"; else echo "FAIL"; fi
rm -f uploaded_files/file-50mb.txt

echo
echo "killing the server"
kill $PID