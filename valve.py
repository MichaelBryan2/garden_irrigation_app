import time
import threading
import RPi.GPIO as GPIO

class Valve:
    t2op = 15    #Time to open in seconds
    def __init__(self, name, pin, state='closed', job='disabled', sched_time='04:00', duration=10):
        self.name = name     #e.g. 'Lower garden valve'
        self.pin = pin       #integer
        self.state = state   #closed, opening, open, closing
        self.job = job       #disabled, running, paused (active)
        self.sched_time = sched_time #
        self.duration = duration #
        
    def Open(self):
        op = threading.Thread(target=self.opening)
        op.start()
        return '{} is opening'.format(self.name)
        
    def Close(self):
        cl = threading.Thread(target=self.closing)
        cl.start()
        return '{} is closing'.format(self.name)
        
    def OpenFor(self, duration):
        sduration = float(60*duration) #converts minutes to seconds
        oac = threading.Thread(target=self.openandclose, args=[sduration])
        oac.start()
        #op = threading.Thread(target=self.opening)
        #op.start()
        #time.sleep(float(60*duration))
        #op.join()                           # This waits for 'opening' to finish before closing starts
        #cl = threading.Thread(target=self.closing)
        #cl.start()
    
    def opening(self):
        if self.state == 'closed':
            GPIO.output(self.pin, GPIO.LOW) #LOW trigger
            self.state = 'opening'  
            #print('{} is opening'.format(self.name))
            time.sleep(self.t2op)
            self.state = 'open'
            #print('{} is now open'.format(self.name))
            return 'Valve is now open'
            
    def closing(self):
        if self.state == 'open':
            GPIO.output(self.pin, GPIO.HIGH) #LOW trigger
            self.state = 'closing'
            #print('{} is closing'.format(self.name))
            time.sleep(self.t2op)
            self.state = 'closed'
            #print('{} is now closed'.format(self.name))
            return "Valve is now closed"
        
    def openandclose(self, duration):
        if self.state == 'closed':
            GPIO.output(self.pin, GPIO.LOW) #LOW trigger
            self.state = 'opening'
            #print('{} is opening'.format(self.name))
            time.sleep(self.t2op)
            self.state = 'open'
            #print('{} is now open'.format(self.name))
            if duration>self.t2op:  # Checks if the is longer then time needed for valves to open
                time.sleep(duration-self.t2op)  # Leaves the valves open for defined duration
            GPIO.output(self.pin, GPIO.HIGH) #LOW trigger
            self.state = 'opening'
            self.state = 'closing'
            #print('{} is closing'.format(self.name))
            time.sleep(self.t2op)
            self.state = 'closed'
            #print('{} is now closed'.format(self.name))
            return "Valve is now closed"
        
    def __str__(self):  # Returns a string if called as a self, e.g. print(Valve)
        return '{} is now {}'.format(self.name, self.state)