import RPi.GPIO as GPIO
import time

# GPIO setup
PUMP_PIN = 22
STATUS_FILE = "pump_status.txt"

GPIO.setmode(GPIO.BCM)
GPIO.setup(PUMP_PIN, GPIO.OUT)

def set_pump(state):
    if state == "on":
        GPIO.output(PUMP_PIN, GPIO.HIGH)
    else:
        GPIO.output(PUMP_PIN, GPIO.LOW)

    with open(STATUS_FILE, 'w') as f:
        f.write(state)

try:
    while True:
        choice = input("Pump control [on/off/exit]: ").strip().lower()

        if choice in ["on", "off"]:
            set_pump(choice)
            print(f"Pump turned {choice.upper()}.")
        elif choice == "exit":
            break
        else:
            print("Invalid input. Type 'on', 'off', or 'exit'.")

except KeyboardInterrupt:
    pass

finally:
    set_pump("off")
    GPIO.cleanup()
    print("Pump turned OFF. GPIO cleaned up.")

