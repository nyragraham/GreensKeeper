import time
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn
import board
import busio
import adafruit_ads1x15.ads1115 as ADS

# File to write humidity percentage
HUMIDITY_FILE = "humidity1.txt"

# Create I2C bus
i2c = busio.I2C(board.SCL, board.SDA)

# Create ADS1115 ADC
ads = ADS.ADS1115(i2c)

# Use channel 0 (A0)
chan = AnalogIn(ads, ADS.P0)

# Sensor calibration range (adjust as needed)
MIN_VOLTAGE = 0.6   # dry
MAX_VOLTAGE = 2.7   # wet

def voltage_to_percent(v):
    # Clamp voltage range
    v = max(min(v, MAX_VOLTAGE), MIN_VOLTAGE)
    return round(100 * (MAX_VOLTAGE - v) / (MAX_VOLTAGE - MIN_VOLTAGE), 1)

try:
    while True:
        voltage = chan.voltage
        humidity = voltage_to_percent(voltage)

        with open(HUMIDITY_FILE, 'w') as f:
            f.write(str(humidity))

        print(f"Voltage: {voltage:.3f} V | Humidity: {humidity}%")
        time.sleep(2)

except KeyboardInterrupt:
    

finally:
    print("Stopped reading humidity.")
