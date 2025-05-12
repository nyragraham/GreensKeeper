# GreensKeeper Website Code (Updated for nested 'plants' key in JSON)

from flask import Flask, render_template, Response, jsonify, redirect, url_for, request
import cv2
import json
import os
import time
import board
import busio
from adafruit_pca9685 import PCA9685
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn
import adafruit_ads1x15.ads1115 as ADS
import RPi.GPIO as GPIO
from datetime import datetime


app = Flask(__name__)

# Load plant database (now nested under 'plants')
with open('plant_database.json', 'r') as f:
    plant_data = json.load(f)
    print("Loaded JSON keys:", plant_data.keys())
    plant_db = plant_data['plants']

# Initialize shelf assignments
shelf_assignments = {
    1: 'basil',
    2: 'mint',
    3: 'rosemary'
}

# Set up GPIO for pump control
GPIO.setmode(GPIO.BCM)
PUMP_PIN = 22
GPIO.setup(PUMP_PIN, GPIO.OUT)

# Set up PWM for grow light using PCA9685
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 1000
LIGHT_CHANNEL = 15

brightness_levels = {
    "off": 0,
    "low": int(0x1999),
    "medium": int(0x7FFF),
    "high": int(0xCCCC)
}

# Set up ADC for humidity sensor
ads = ADS.ADS1115(i2c)
chan = AnalogIn(ads, ADS.P0)

MIN_VOLTAGE = 0.6
MAX_VOLTAGE = 2.7

def voltage_to_percent(v):
    v = max(min(v, MAX_VOLTAGE), MIN_VOLTAGE)
    return round(100 * (MAX_VOLTAGE - v) / (MAX_VOLTAGE - MIN_VOLTAGE), 1)

TIMER_FILE = "light_runtime.txt"
start_time = None

camera = cv2.VideoCapture(0)

def generate_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def read_last_watered(slot):
    try:
        with open("last_watered.json", "r") as f:
            data = json.load(f)
            time_str = data.get(str(slot))
            if time_str:
                dt = datetime.fromisoformat(time_str)
                days_ago = (datetime.now() - dt).days
                return f"{days_ago} days ago"
    except:
        pass
    return "N/A"

def update_last_watered(slot=1):
    try:
        with open("last_watered.json", "r") as f:
            data = json.load(f)
    except:
        data = {}
    data[str(slot)] = datetime.now().isoformat()
    with open("last_watered.json", "w") as f:
        json.dump(data, f)

@app.route('/')
def index():
    statuses = get_status()
    light_seconds = int(read_file_value(TIMER_FILE, default="0"))
    light_hours = round(light_seconds / 3600, 2)
    humidity = read_humidity()
    return render_template('index.html', shelf_assignments=shelf_assignments, plant_db=plant_db,
                           statuses=statuses, light_runtime=light_hours, humidity=humidity)

@app.route('/plant/<int:plant_id>')
def plant_page(plant_id):
    plant_key = shelf_assignments.get(plant_id)
    plant = plant_db.get(plant_key)
    if not plant:
        return "Plant not found", 404

    humidity = read_humidity()
    light_seconds = int(read_file_value(TIMER_FILE, default="0"))
    light_hours = round(light_seconds / 3600, 2)

    light_status = read_file_value("light_status.txt", "off")
    light_display = f"{light_status.capitalize()} ({light_hours} hrs)" if light_status != "off" else "Off"
    last_watered = read_last_watered(plant_id)
    watering_now = read_file_value("pump_status.txt", "off") == "on"



    return render_template('plant.html', plant=plant, plant_id=plant_id, humidity=humidity, light_runtime=light_display, last_watered=last_watered, watering_now=watering_now)

@app.route('/manual')
def manual_control():
    statuses = get_status()
    light_seconds = int(read_file_value(TIMER_FILE, default="0"))
    light_hours = round(light_seconds / 3600, 2)
    return render_template('manual.html', statuses=statuses, light_runtime=light_hours)

@app.route('/assign', methods=['GET', 'POST'])
def assign_plant():
    if request.method == 'POST':
        slot = int(request.form['slot'])
        plant_key = request.form['plant']
        shelf_assignments[slot] = plant_key
        return redirect(url_for('index'))
    return render_template('assign.html', shelf_assignments=shelf_assignments, plant_db=plant_db)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/pump_on')
def pump_on():
    with open("pump_status.txt", "w") as f:
        f.write("on")  # set immediately

    GPIO.output(PUMP_PIN, GPIO.HIGH)
    time.sleep(2)
    GPIO.output(PUMP_PIN, GPIO.LOW)

    with open("pump_status.txt", "w") as f:
        f.write("off")  # set to off afterward

    update_last_watered(slot=1)
    return redirect(url_for('manual_control'))

@app.route('/pump_off')
def pump_off():
    with open("pump_status.txt", "w") as f:
        f.write("off")
    GPIO.output(PUMP_PIN, GPIO.LOW)
    return redirect(url_for('manual_control'))


@app.route('/light/<level>')
def light_control(level):
    global start_time
    if level in brightness_levels:
        with open("light_status.txt", "w") as f:
            f.write(level)
        duty = brightness_levels[level]
        pca.channels[LIGHT_CHANNEL].duty_cycle = duty

        if level != "off":
            start_time = time.time()
        else:
            start_time = None
            with open(TIMER_FILE, 'w') as f:
                f.write("0")
    return redirect(url_for('manual_control'))

@app.route('/sensor_data/<int:plant_id>')
def sensor_data(plant_id):
    humidity = read_humidity()
    light = read_file_value("light_status.txt", default="off")
    return jsonify({"humidity": humidity, "light": light})

def get_status():
    current_status = read_file_value("light_status.txt", "off")
    if current_status != "off" and start_time:
        elapsed = int(time.time() - start_time)
        with open(TIMER_FILE, 'w') as f:
            f.write(str(elapsed))

    emoji_map = {
        "off": "\U0001F311",
        "low": "\u2601\ufe0f",
        "medium": "\u26c5",
        "high": "\u2600\ufe0f"
    }

    return {
        "pump1": read_file_value("pump_status.txt", "off"),
        "light1": current_status,
        "light_emoji": emoji_map.get(current_status, "\U0001F311")
    }

def read_file_value(path, default=""):
    try:
        with open(path, 'r') as f:
            return f.read().strip()
    except:
        return default

def read_humidity():
    voltage = chan.voltage
    return voltage_to_percent(voltage)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
    pca.deinit()
    GPIO.cleanup()