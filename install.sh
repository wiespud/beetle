#!/bin/bash

scp *.py pi@192.168.0.30:~/ > /dev/null
scp *.py pi@192.168.0.8:~/ > /dev/null
scp html_beetle/* pi@192.168.0.30:/var/www/html/ > /dev/null
scp html_beetle/log.php pi@192.168.0.8:/var/www/html/ > /dev/null
scp html_home/* pi@basement.local:/var/www/html/beetle/ > /dev/null
