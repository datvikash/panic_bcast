#!/usr/bin/python2.7
# Copyright (c) 2012, Niklas Femerstrand <nik@qnrq.se>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
# Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
# Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS
# IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO,
# THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR
# PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR
# CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL,
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO,
# PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS;
# OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR
# OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF
# ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
import re
import os
import socket
import threading
import BaseHTTPServer
from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer

# Basic HTTP server that listens to GET /panic and triggers panic.
# Written to provide a standardized interface for panic triggering.
# To trigger panic through HTTP simply request http://localhost:8080/panic
class panicHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		if self.path == "/\x70\x61\x6e\x69\x63":
			sendSignal()

def httpd():
	s = HTTPServer(('', 8080), panicHandler)
	s.serve_forever()

# TODO: Extend with a C lib that iterates through used physmem addresses and
#       overwrites values in a prio order before triggering poweroff.
# TODO: Use mountedDrives() to iterate and eject (crypto) mounts
def treatPanic():
	os.popen("killall truecrypt")
	# Linux, possibly more
	os.popen("shutdown -P now")
	# FreeBSD, possibly more
	os.popen("shutdown -p now")

def sigListener():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	s.bind(("", 1337)) # Listen on all devices

	while 1:
		try:
			message, address = s.recvfrom(5)
			if message == "\x70\x61\x6e\x69\x63":
				treatPanic()
		except:
			pass

# Extracts mounted device names and mount points. Intended to work on
# everything UNIX. Tested on Linux and FreeBSD (UFS2 and ZFS).
def mountedDrives():
	drives = []
	mount = os.popen("mount | grep -o \".* on .* (\"").read()
	for m in mount.split("\n"):
		matches = re.match("(.*) on (.*) \(", m)
		if matches:
			drives.append({ matches.group(1) : matches.group(2) })

	return drives

def bcast():
	bcast = os.popen("ifconfig | grep -o \"broadcast [0-9]*\.[0-9]*\.[0-9]*\.[0-9]*\"").read()
	bcast = bcast.replace("broadcast ", "")

	return bcast
	
def sendSignal():
	s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
	s.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
	s.sendto("\x70\x61\x6e\x69\x63", (bcast(), 1337))
	s.close()

	return 0

httpd = threading.Thread(name="httpd", target=httpd)
httpd.start()
sigListener = threading.Thread(name="sigListener", target=sigListener)
sigListener.start()
