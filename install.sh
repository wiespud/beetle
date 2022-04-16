#!/bin/bash

scp *.py pi@beetle-front.local:~/ > /dev/null
scp *.py pi@beetle-back.local:~/ > /dev/null
scp html_beetle/* pi@beetle-front.local:/var/www/html/ > /dev/null
scp html_beetle/* pi@beetle-back.local:/var/www/html/ > /dev/null
scp html_home/* pi@basement.local:/var/www/html/beetle/ > /dev/null
