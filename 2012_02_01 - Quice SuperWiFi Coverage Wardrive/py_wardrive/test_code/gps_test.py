#!/usr/bin/python
import socket, json

def print_dict(my_dict):
	print json.dumps(my_dict, sort_keys=True, indent=4)

try:
	gps_host = 'localhost'
	gps_port = 2947
	gps_host = socket.gethostbyname(gps_host)
	gps_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	print "--> Connecting on %s:%d" % (gps_host, gps_port)
	gps_sock.connect((gps_host, gps_port))
	# get information pkt send upon connect from gpsd
	data = gps_sock.recv(1024)
	gpsd_info = json.loads(data)
	print "Received gpsd info packet:"
	print_dict(gpsd_info)
except socket.error, msg:
	print 'ERROR: socket error - %s' % msg

print "--> Issuing gpsd WATCH command and waiting for response ..."
gps_sock.send('?WATCH={"enable":true,"json":true}')
data = gps_sock.recv(1024)
print "  > got ACK, waiting for device ..."
data = gps_sock.recv(1024)
gps_devs = json.loads(data)
print "  > GPS device activated:"
print_dict(gps_devs)

# Endless loop to get GPS data
while 1:
	data = gps_sock.recv(1024)
	gps_report = json.loads(data)
	if 'class' in gps_report:
		if gps_report['class'] == 'TPV':
			if gps_report['mode'] == 1:
				print "  > waiting for fix ..."
			elif gps_report['mode'] == 2:
				print "  > 2D fix lat: %f, lon: %f" % (
					gps_report['lat'], gps_report['lon'])
			elif gps_report['mode'] == 3:
				print "  > 3D fix lat: %f, lon: %f, alt: %f" % (
					gps_report['lat'], gps_report['lon'], gps_report['alt'])
			else:
				print "  > Unexpected report encountered:"
				print_dict(gps_report)
		elif gps_report['class'] == 'SKY':	
			if 'satellites' in gps_report:
				print "  > Satellites found: %d" % (len(gps_report['satellites']))
			#else:
				#print "  > SKY report with no satellites ignored ..."
		else:
			print "  > Unexpected report encountered:"
			print_dict(gps_report)
	else:
		print "  > Unexpected report encountered:"
		print_dict(gps_report)

print "--> Stopping gpsd WATCH command ..."
gps_sock.send('?WATCH={"enable":false}')
gps_sock.close()
