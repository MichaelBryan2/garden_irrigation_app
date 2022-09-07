import RPi.GPIO as GPIO
from valve import Valve
from datetime import datetime
import time, signal, threading
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, request        #, session, flash
from w1thermsensor import W1ThermSensor
import Adafruit_DHT

app = Flask(__name__)
#app.secret_key = "super secret key"

scheduler = BackgroundScheduler() # Creates a job scheduler for automatic watering
AutoMode = False
GPIO.setmode(GPIO.BCM)

V1 = Valve('Garden valve 1', 18)
V2 = Valve('Garden valve 2', 23)
V3 = Valve('Garden valve 3', 24)
V4 = Valve('Garden valve 4', 25)
valves = [V1, V2, V3, V4]  # list of valves

# Add jobs for each valve in scheduler and sets GPIO
for valve in valves:
    GPIO.setup(valve.pin, GPIO.OUT)
    GPIO.output(valve.pin, GPIO.HIGH)
    scheduler.add_job(valve.OpenFor, args=[10], trigger='cron', minute=2, id='V{}job'.format(valves.index(valve)+1))
    scheduler.pause_job(job_id='V{}job'.format(valves.index(valve)+1))  
scheduler.start()
scheduler.print_jobs()

sensor = W1ThermSensor()
sensorDHT = Adafruit_DHT.DHT22
DHT_PIN = 17

@app.route("/")
def main():
    templateData = {'valves': valves, 'AutoMode': AutoMode}
    return render_template('main.html', **templateData)

@app.route("/auto/")
def to_auto():
    templateData = {'valves': valves}
    return render_template('auto.html', **templateData)
    
@app.route("/main/")
def to_main():
    AutoMode = False
    for valve in valves:
        AutoMode = AutoMode or (valve.job == 'running') # if any job is still running AutoMode is set to True
    templateData = {'valves': valves, 'AutoMode': AutoMode}    
    return render_template('main.html', **templateData)

@app.route("/sensors/")
def sensor_page():
    try:
        air = sensor.get_temperature()
    except:
        air = '-'
    humidity, temperature = Adafruit_DHT.read_retry(sensorDHT, DHT_PIN)
    if humidity is None:
        humidity = '-'
    if temperature is None:
        temperature = '-'
    water = 22
    templateData = {'air_temp': air, 'water_temp': temperature, 'humidity': humidity}
    return render_template('sensors.html', **templateData)

@app.route("/<ValveNum>/<action>")
def action(ValveNum, action):
    i = int(ValveNum)-1
    if action == 'on':
        valves[i].Open()    
    if action == 'off':
        valves[i].Close()
    AutoMode = False
    for valve in valves:
        AutoMode = AutoMode or (valve.job == 'running') # if any job is still running AutoMode is set to True
    templateData = {'valves': valves, 'AutoMode': AutoMode}    
    return render_template('main.html', **templateData)

@app.route("/setJob/<ValveNum>", methods = ["GET", "POST"]) # Povolme metody GET a POST
def setJob(ValveNum): 
    try:
        i = int(ValveNum)     
        time = request.args.get("scheduled_time") # Ziskame hodnotu z GET requestu
        valves[i-1].sched_time = time
        duration = int(request.args.get("duration"))
        valves[i-1].duration = duration
        period = int(request.args.get("period"))
        time = datetime.strptime(time, "%H:%M")
        h = time.hour
        m = time.minute
        scheduler.resume()
        scheduler.reschedule_job( job_id='V{}job'.format(i), trigger='cron', day='*/{}'.format(period), hour=h, minute=m)
        scheduler.modify_job( job_id='V{}job'.format(i), args=[duration])
        scheduler.resume_job( job_id='V{}job'.format(i))
        AutoMode = True
        valves[i-1].job = 'running'
    except:
        message = 'Wrong input'
    templateData = {'valves': valves}
    return render_template('auto.html', **templateData)

@app.route("/pauseJob/<ValveNum>")    
def pauseJob(ValveNum):
    i = int(ValveNum)
    scheduler.pause_job( job_id='V{}job'.format(i))
    valves[i-1].job = 'paused'
    templateData = {'valves': valves}
    return render_template('auto.html', **templateData)

@app.route("/resumeJob/<ValveNum>")
def resumeJob(ValveNum):
    i = int(ValveNum)
    scheduler.resume_job( job_id='V{}job'.format(i))
    valves[i-1].job = 'running'
    templateData = {'valves': valves}
    return render_template('auto.html', **templateData)

@app.route("/pauseSched/")
def pauseScheduler():
    scheduler.pause()
    Automode = False
    for valve in valves:
        scheduler.pause_job(job_id='V{}job'.format(valves.index(valve)+1))
        valve.job = 'disabled'
    templateData = {'valves': valves, 'AutoMode': AutoMode}    
    return render_template('main.html', **templateData)

def exit_handler(signum, frame):
    for valve in valves:
        while valve.state == 'opening':   #If the valve is opening, waits for it to fully open
            time.sleep(2)
        valve.Close()
    for valve in valves:    
        while not valve.state == 'closed':   #Waits for all valves to close
            time.sleep(2)
    print('All valves closed')
    GPIO.cleanup()
    print('GPIO cleaned')
    scheduler.shutdown()
    sys.exit(0)
    return

signal.signal(signal.SIGINT, exit_handler)
signal.signal(signal.SIGTERM, exit_handler)
    
if __name__ == "__main__":
   app.run(host='0.0.0.0', port=80, debug=True)