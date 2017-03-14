#!/bin/bash
cd $(dirname `readlink -f "$0"`)
./process.py >bedasstats.html
scp bedasstats.html jose1711@freeshell.de:public_html/
scp *.png jose1711@freeshell.de:public_html/
scp input_data.xlsx jose1711@freeshell.de:public_html/
scp -r /tmp/players jose1711@freeshell.de:public_html/
