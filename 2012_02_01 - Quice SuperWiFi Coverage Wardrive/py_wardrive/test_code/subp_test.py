#!/usr/bin/python 

import subprocess, time, sys
from signal import *
    
# Process signal handler functions
def process_quit(signum, frame):
    exit(0)
def process_tstp(signum, frame):
    exit(0)
def process_sint(signum, frame):
    print "\n --> SIGINT ignored\n    Please use SIGTSTP (ctrl+z) instead ..."
def exit(code):
    print "\n--> Stopping ..."
    proc.terminate()
    print "    Done."
    sys.exit(code)

# Register callback functions with process signal listener
signal(SIGTSTP, process_tstp)
signal(SIGQUIT, process_quit)
signal(SIGINT, process_sint)

# Main code
exec_str = 'tcpdump -l -i war0 -n port 31585'
print "Running %s" % exec_str
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
    str = proc.stdout.readline()
    str.strip()
    # I can't figure out why strip() keeps leaving a newline char
    str = str[:-1]
    print "Stripped: %s" % str

exit(0)