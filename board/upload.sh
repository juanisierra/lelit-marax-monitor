#!/bin/sh

if [ -z $ESP_PORT ]; then
    echo "Please define ESP_PORT"
    exit 1
fi


if [ ! -f config.py ]; then
    echo "Missing config.py, you can use config.py.template to create one"
    exit 1
fi


AMPY="esp32/bin/ampy --port $ESP_PORT --baud 115200"

putfile () {
    local file=$1
    $AMPY put $file
    echo "copied ${file}.."
}


putfile boot.py
putfile main.py
putfile marax.py
putfile config.py
putfile ssh1106.py
putfile shot_timer.py