#!/usr/bin/python
import socket, time

bind_addr='172.16.11.50'
bcast_addr='172.16.11.255'
port=31585
msg='DEADBEEF'

my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
while 1:
	my_socket.sendto(msg, (bcast_addr, port))
	time.sleep(5)

