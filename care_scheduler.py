from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import time
import json
import board
import busio
from adafruit_pca9685 import PCA9685
import RPi.GPIO as GPIO

# --- Setup ---
scheduler = BackgroundScheduler()

with open("plant_database.json", "r") as f:
    plant_db = json.load(f)["plants"]

shelf_assignments = {1: "basil"}

GPIO.setmode(GPIO.BCM)
PUMP_PIN = 22
GPIO.setup(PUMP_PIN, GPIO.OUT)

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

# --- Helpers ---
def read_file_value(path, default="off"):
    try:
        with open(path, "r") as f:
            return f.read().strip()
    except:
        return default

def write_file_value(path, value):
    with open(path, "w") as f:
        f.write(str(value))

def update_last_watered(slot=1):
    try:
        with open("last_watered.json", "r") as f:
            data = json.load(f)
    except:
        data = {}
    data[str(slot)] = datetime.now().isoformat()
    with open("last_watered.json", "w") as f:
        json.dump(data, f)

# --- Tasks ---
def care_task():
    slot = 1
    plant_key = shelf_assignments.get(slot)
    plant = plant_db.get(plant_key)
    if not plant:
        return

    now = datetime.now()
    interval = plant.get("watering_interval_days", 3)

    try:
        with open("last_watered.json", "r") as f:
            data = json.load(f)
        last_str = data.get(str(slot), "")
        last = datetime.fromisoformat(last_str) if last_str else now - timedelta(days=interval + 1)
    except:
        last = now - timedelta(days=interval + 1)

    if (now - last).days >= interval:
        print(f"[AUTO] Watering {plant['name']}")
        GPIO.output(PUMP_PIN, GPIO.HIGH)
        time.sleep(2)
        GPIO.output(PUMP_PIN, GPIO.LOW)
        update_last_watered(slot)
        write_file_value("pump_status.txt", "off")

def turn_on_light():
    slot = 1
    plant_key = shelf_assignments.get(slot)
    plant = plant_db.get(plant_key)
    if not plant:
        return

    level = plant.get("light_level", "high")
    duration = plant.get("sunlight_hours", 6)

    print(f"[AUTO] Turning light ON ({level}) for {duration} hrs")
    pca.channels[LIGHT_CHANNEL].duty_cycle = brightness_levels.get(level, 0)
    write_file_value("light_status.txt", level)

    off_time = datetime.now() + timedelta(hours=duration)
    scheduler.add_job(turn_off_light, 'date', run_date=off_time)

def turn_off_light():
    print("[AUTO] Turning light OFF")
    pca.channels[LIGHT_CHANNEL].duty_cycle = 0
    write_file_value("light_status.txt", "off")

# --- Schedule Jobs ---
scheduler.add_job(care_task, 'interval', minutes=30)
scheduler.add_job(turn_on_light, 'cron', hour=9, minute=0)

# --- Start ---
scheduler.start()

try:
    while True:
        time.sleep(1)
except (KeyboardInterrupt, SystemExit):
    pca.deinit()
    GPIO.cleanup()
