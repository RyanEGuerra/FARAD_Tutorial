#!/usr/bin/python

import threading, time

class StoreStuff(threading.Thread):    
    def __init__(self, new_data):
        threading.Thread.__init__(self)
        print "Object made!"
        self.info = 'I\' got this info!'
        self.data = new_data
        
        self.state_lock = threading.Condition()
        self.am_done = False
        
    def run(self):
        print "Object running!"
        counter = 0
        while 1:
            print "%s %s" %(self.info, self.data)
            time.sleep(1)
            counter += 1
            if counter > 5:
                self.state_lock.acquire()
                self.am_done = True
                self.state_lock.notifyAll()
                self.state_lock.release()
                
    def wait_for_timeout(self):
        self.state_lock.acquire()
        while not self.am_done:
            self.state_lock.wait(30)
        self.state_lock.release()

    def set_data(self, new_data):
        print "Setting new data!"
        self.data = new_data
        
    def get_data(self):
        return "Got data: %s" % self.data
        
def main():
    obj = StoreStuff(1)
    #obj.setDaemon(True)
    obj.start()
    print "Main sleeping..."
    time.sleep(3)
    print "Main awoke!"
    obj.set_data(5)
    print "Waiting for lock..."
    obj.wait_for_timeout()
    print "Done waiting!"
    while 1:
        print obj.get_data()
        time.sleep(1)
    
main()