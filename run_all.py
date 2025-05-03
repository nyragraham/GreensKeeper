import subprocess
import time

# Start each background service
bright = subprocess.Popen(["python3", "bright.py"])
humidity = subprocess.Popen(["python3", "humidity.py"])
pump = subprocess.Popen(["python3", "pump_control.py"])

# Delay to ensure background processes start
time.sleep(2)

# Start the Flask website
try:
    subprocess.run(["python3", "website.py"])
except KeyboardInterrupt:
    print("Shutting down...")

# Optional: terminate background processes when site exits
bright.terminate()
humidity.terminate()
pump.terminate()
