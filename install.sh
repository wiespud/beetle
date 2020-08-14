#!/bin/bash

scp *.py pi@beetle-front.local:~/ > /dev/null
scp *.py pi@beetle-back.local:~/ > /dev/null
