import time
import os
from adafruit_pca9685 import PCA9685
import board
import busio

# Set up I2C and PCA9685
i2c = busio.I2C(board.SCL, board.SDA)
pca = PCA9685(i2c)
pca.frequency = 1000  # 1kHz PWM

# Use channel 0 for the grow light
channel = pca.channels[0]

# Status file paths
STATUS_FILE = "light_status.txt"
TIMER_FILE = "light_runtime.txt"

# Load timer if already running
start_time = None
if os.path.exists(STATUS_FILE):
    with open(STATUS_FILE, 'r') as f:
        state = f.read().strip().lower()
        if state != 'off':
            start_time = time.time()

# Function to update runtime counter
def update_runtime(start_time):
    if start_time:
        elapsed = int(time.time() - start_time)
        with open(TIMER_FILE, 'w') as f:
            f.write(str(elapsed))
    else:
        with open(TIMER_FILE, 'w') as f:
            f.write("0")

# Brightness levels
brightness_levels = {
    "off": 0,
    "low": int(0x1999),    # ~20%
    "medium": int(0x7FFF), # ~50%
    "high": int(0xCCCC)    # ~80%
}

try:
    while True:
        choice = input("Choose brightness: [low], [medium], [high], [off]\n> ").strip().lower()
        if choice in brightness_levels:
            duty = brightness_levels[choice]
            channel.duty_cycle = duty

            # Save current status
            with open(STATUS_FILE, 'w') as f:
                f.write(choice)

            # Start or stop timer
            if choice != "off":
                start_time = time.time()
            else:
                start_time = None
                with open(TIMER_FILE, 'w') as f:
                    f.write("0")

            print(f"Brightness set to {choice.upper()}")

        elif choice == "exit":
            break

        else:
            print("Invalid choice.")

        # Update runtime file
        update_runtime(start_time)
        time.sleep(1)

except KeyboardInterrupt:
    pass

finally:
    channel.duty_cycle = 0
    pca.deinit()
    print("Light off. PCA9685 shutdown.")

