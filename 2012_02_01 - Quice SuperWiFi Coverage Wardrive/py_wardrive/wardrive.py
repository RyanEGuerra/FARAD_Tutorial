#!/usr/bin/python
"""
wardrive.py
Ryan E. Guerra (war@rice.edu)
Feb 1, 2012
	broadcast or listen for wardrive packets
	on all interfaces. When a packet is received,
	the location and RSSI should be logged

	Depends on gpsd and rngbox software for coord
	and RSSI measurements	
"""
import socket, string, json, argparse, sys, os, time, random, datetime, threading, subprocess
from signal import *

"""
	a great package for parsing arguments and making sure everything is correct
"""
parser = argparse.ArgumentParser(
	description='Broadcast or listen for wardrive packets.',
	epilog='Good luck, please do not crash!')
parser.add_argument('--version', action='version', version='%(prog)s 0.1')
parser.add_argument('-s', '--isserver', nargs='?', default=False, const=True,
	help='Flags this instance as a server; must provide an interface addr to broadcast on if specified. Default mode is client')
parser.add_argument('-t', '--interval', nargs='?', default=2, type=int,
	help='For servers, specifies the interval (seconds) between broadcast packets. Default: 2')
parser.add_argument('-R', '--modrate', nargs='?', default=1, type=int,
	help='For servers, specifies the modulation (Mbps) rate of broadcast packets. Default: 1')
parser.add_argument('-T', '--txpwr', nargs='?', default=20, type=int,
	help='For servers, specifies the transmit power (dBm) of broadcast packets. Default: 20')
parser.add_argument('-b', '--host', nargs='?', default='',
	help='For servers, a required broadcast IP to transmit on.')
parser.add_argument('-i', '--iface', nargs='?', default='wlan0',
	help='For servers, a required network device interface to broadcast on.')
parser.add_argument('-p', '--port', nargs='?', default=31585, type=int,
	help='Optional argument for the port to transmit/receive packets on. Default: 31585')
parser.add_argument('-o', '--outfile', nargs='?', type=argparse.FileType('w'), default=sys.stdout,
	help='Optional output file to store results from the client. Default to 	.')
parser.add_argument('-l', '--plen', nargs='?', default=1000, type=int,
	help='Optional length of broadcast UDP packets for channel sounding by server. Default to 1000 bytes.')
args = parser.parse_args()
print args

# Global Variables
bcast_sock = {}
#gps_lock = threading.RLock()

# Check arguments for consistency
if args.isserver and args.host == '':
	print "\nERROR: must provide a target IP addr when starting a server!\n       Try using the -b <addr> flag.  Exiting...\n"
	sys.exit(1)

"""
Pretty Print a Dict Object
"""
def print_dict(my_dict):
	print json.dumps(my_dict, sort_keys=True, indent=4)

"""
Current Time in Seconds
"""
def get_ts_seconds():
	now = datetime.datetime.now()
	tot_secs = now.second + 60*now.minute + 60*60*now.hour
	return tot_secs

"""
Open GPSD Sockets
	Make a new TCP connection to the GPSD daemon and return the connected socket.
"""
def open_gpsd_socket():
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
		print "  > Received gpsd info packet:"
		print "    rel %s rev %s" %(gpsd_info['release'], gpsd_info['rev'])
	except socket.error, msg:
		print 'ERROR: socket error - %s' % msg
	return gps_sock

"""
Main Loop
	Open sockets, set radio settings, and then start the server/client loops.
"""
def main():
	# perform the activity loops for either role: client/server
	if args.isserver:
		server_loop()
	else:
		client_loop()

# =========================== Client ================================
"""
Client Loop
	Get GPS coordinates in intervals.
	Each GPS update triggers a check of inbound packets in the last <interval> seconds
	as reported in dmesg.
"""
def client_loop():
	global args
	global proc
	global dump_file
	
	
	filename = "./data/wardrive_dump_%d" % random.randint(100,10000)
	print "--> Opening file %s for writing" % filename
	dump_file = open(filename, 'w')
	
	proc = None
	# Start a GPSd listener
	gps = GPSWatcher()
	gps.setDaemon(True)
	gps.start()
	# Block until a GPS signal lock is acquired
	gps.wait_for_gps_lock()
	
	# We use tcpdump to listen for incoming packets
	# We have to make a monitor interface in order to get SNR
	create_monitor_iface('phy0')

	# create line-buffered monitor interface using tcpdump :)
	exec_str = 'tcpdump -l -i war0 -n port %d' % args.port
	print "--> Running \"%s\" ..." % exec_str
	proc = subprocess.Popen(exec_str,
	                        shell=True,
	                        executable="/bin/bash",
	                        stdout=subprocess.PIPE,
	                        stdin=subprocess.PIPE
	                        )
	
	counter = 0
	while 1:
	    # Read in a line from the tcpdump process stdout
	    # this appears to be blocking until content appears--great!
	    pkt_dat = proc.stdout.readline()
	    pkt_dat.strip()
	    # I can't figure out why strip() keeps leaving a newline char
	    # so here's a hack to get rid of the damned thing (last char)
	    pkt_dat = pkt_dat[:-1]
	    loc_dat = gps.get_gps_data_string()
	    pkt_dat = "%s %s" % (pkt_dat, loc_dat)
	    dump_file.write(pkt_dat + "\n")
	    counter += 1
	    print "%6d: %s" % (counter, pkt_dat)
	
	# Should never get here.
	exit(1)
	
"""
Create Monitor
	Create a monitor interface on the host PC and print results to target file
"""
def create_monitor_iface(iface):
	global args
	
	exec_str = "iw phy %s interface add war0 type monitor" % iface
	os.system(exec_str)
	exec_str = "ifconfig war0 up"
	os.system(exec_str)

"""
GPS Watcher
	Sits and watches the GPS object. Update the gps_coords dict
	with current data after acquiring gps_lock
"""
class GPSWatcher(threading.Thread):
	
	def __init__(self):
		threading.Thread.__init__(self)
		self.debug = False
		self.has_gps_sig_lock = False
		self.state_lock = threading.Condition()
		self.gps_lock = threading.RLock()
		if self.debug:
			self.gps_coords={'lat' : '10.10', 'lon' : '20.20', 'alt' : '500', 'ts' : 12345678}
		else:
			self.gps_coords={'lat' : '--', 'lon' : '--', 'alt' : '--', 'ts' : 0}
	
	def run(self):
		print '----> Connecting to GPS device via gpsd ...'
		# Open a connection to the attached GPS device via gpsd
		gps_sock = open_gpsd_socket()
		print "----> Issuing gpsd WATCH command and waiting for response ..."
		gps_sock.send('?WATCH={"enable":true,"json":true}')
		data = gps_sock.recv(1024)
		#print "  > got ACK, waiting for device ..."
		while 1:
			# Wait for GPS fix reports
			try:
				data = gps_sock.recv(1024)
			except socket.error as (errno, msg):
				if errno != 4:
						raise
				print "    > Continuing program ..."
			gps_report = json.loads(data)
			if 'class' in gps_report:
				# Update the current GPS coordinates, including timestamp
				if gps_report['class'] == 'TPV':
					if gps_report['mode'] == 1:
						print "    waiting for fix ..."
						self.update_sig_lock(False)
						self.gps_lock.acquire(True)
						if not self.debug:
							self.gps_coords['lat'] = '--'
							self.gps_coords['lon'] = '--'
							self.gps_coords['alt'] = '--'
						self.gps_coords['ts'] = get_ts_seconds()
						self.gps_lock.release()
					elif gps_report['mode'] == 2:
						self.update_sig_lock(True)
						self.gps_lock.acquire(True)
						self.gps_coords['lat'] = gps_report['lat']
						self.gps_coords['lon'] = gps_report['lon']
						self.gps_coords['alt'] = '--'
						self.gps_coords['ts'] = get_ts_seconds()
						self.gps_lock.release()
						if self.debug:
							print "    > 2D fix lat: %f, lon: %f, ts: %d" % (
								self.gps_coords['lat'], self.gps_coords['lon'],
								self.gps_coords['ts'])
					elif gps_report['mode'] == 3:
						self.update_sig_lock(True)
						self.gps_lock.acquire(True)
						self.gps_coords['lat'] = gps_report['lat']
						self.gps_coords['lon'] = gps_report['lon']
						self.gps_coords['alt'] = gps_report['alt']
						self.gps_coords['ts'] = get_ts_seconds()
						self.gps_lock.release()
						if self.debug:
							print "    > 3D fix lat: %f, lon: %f, alt: %f, ts: %d" % (
								self.gps_coords['lat'], self.gps_coords['lon'],
								self.gps_coords['alt'], self.gps_coords['ts'])
					else:
						print "    > Unexpected report encountered:"
						print_dict(gps_report)
				# Satellite reports are cool, but they should be silent
				#elif gps_report['class'] == 'SKY':
				#	if 'satellites' in gps_report:
				#		print "  > Satellites found: %d" % (len(gps_report['satellites']))
				elif gps_report['class'] == 'DEVICE':
					print "    > Device found at: %s" % (gps_report['path'])
				elif not gps_report['class'] == 'SKY':
					print "    > Unexpected report encountered:"
					print_dict(gps_report)
		# Because the loop never ends, we should never get here.
		exit(1)
		
	def update_sig_lock(self, state):
		self.state_lock.acquire()
		self.has_gps_sig_lock = state
		self.state_lock.notifyAll()
		self.state_lock.release()
		
	def wait_for_gps_lock(self):
		print "--> Main thread waiting for GPS signal lock ..."
		self.state_lock.acquire()
		while not self.has_gps_sig_lock:
			self.state_lock.wait(None)
		self.state_lock.release()
		print "  > GPS signal lock acquired!"
	
	def get_gps_data_string(self):		
		# don't try to print any fields that are blank!
		if self.debug:
			print "  > Fetching GPS data ..."
		ret_str = ""
		self.gps_lock.acquire(True)
		if self.gps_coords['lat'] != None:
			ret_str += "lat %s lon %s" % (self.gps_coords['lat'], self.gps_coords['lon'])
		if self.gps_coords['alt'] != None:
			ret_str += " alt %s" % self.gps_coords['alt']
		if self.gps_coords['ts'] != None:
			ret_str += " ts %d" % self.gps_coords['ts']
		self.gps_lock.release()
		if self.debug:
			print "    Got: %s" % ret_str
		return ret_str
	
# =========================== Server ================================
"""
Server Loop
	Constantly send out packets on the given interface
	at the given interval until the cows come home.
"""
def server_loop():
	global args
	global bcast_sock
	
	cur_seqno = 0
	max_seqno = 100000
	cur_time = get_ts_seconds()
	
	print "--> Setting radio parameters for SERVER - Modrate: %d, TxPwr: %d ..." % (args.modrate, args.txpwr)
	os.system('/sbin/iwconfig %s rate %dM fixed' % (args.iface, args.modrate))
	os.system('/sbin/iwconfig %s txpower %d fixed' % (args.iface, args.txpwr))
	os.system('/etc/rng/scripts/ani.sh off')
	
	print "--> Starting new SERVER broadcasting on Host: %s, Port: %d ..." % (args.host, args.port)
	header_str = " %10d %10d " % (cur_seqno, cur_time) 
	rand_data = ''
	for i in range(args.plen - len(header_str)):
		rand_data = rand_data + chr(random.randint(0,255))
		
	bcast_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	bcast_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST,1)
	while 1:
		cur_seqno = cur_seqno + 1
		if cur_seqno > max_seqno:
			cur_seqno = 0
		elif cur_seqno % 1000 == 0:
			print "  > Transmitted 1000 pkts ..."
		cur_time = get_ts_seconds()
		header_str = " %10d %10d " % (cur_seqno, cur_time) 
		data = header_str + rand_data
		bcast_sock.sendto(data, (args.host, args.port))
		time.sleep(args.interval)
		
	# Since this loop never ends, we should never reach this point
	# Sockets are closed gracefully upon script interruption
	print '--> Done.'

"""
Close Sockets
	Close any open sockets for nice exiting behavior
"""
def close_sockets():
	global bcast_sock
	
	bcast_sock.close()		
		
"""
Exit
"""
def exit(code):
	global proc
	global args
	global dump_file
	
    #print '\n--> Stopping ...'
	if args.isserver:
		close_sockets()
	else:
		if proc != None:
			proc.terminate()
		os.system("ifconfig war0 down")
		os.system("iw war0 del")
		dump_file.close()
	print "    Done."
	sys.exit(code)
    
# =========================== Signal Handlers ================================
# Process signal handler functions
def process_quit(signum, frame):
    exit(0)
def process_tstp(signum, frame):
    exit(0)
def process_sint(signum, frame):
    print "\n --> SIGINT ignored\n    Please use SIGTSTP (ctrl+z) instead ..."

# Register callback functions with process signal listener
signal(SIGTSTP, process_tstp)
signal(SIGQUIT, process_quit)
signal(SIGINT, process_sint)

# Launch main() when this script is called.
main()


