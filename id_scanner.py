import subprocess
import time
import tempfile
import os
import RPi.GPIO as GPIO

DEV = "/dev/lirc0"

BASE = [
    1400,1400,700,700,700,1400,700,2800,
    700,2100,1400,700,700,700,700,1400,
    1400,2800,1400,2800,700
]

VALUES = [700, 1400, 2100, 2800]

GPIO.setmode(GPIO.BCM)
PIN_ACTION = 24  # pin 18
GPIO.setup(PIN_ACTION, GPIO.IN, pull_up_down=GPIO.PUD_UP)

DEBOUNCE = 0.25  # segundos
last_press = 0.0

def action_pressed() -> bool:
    return GPIO.input(PIN_ACTION) == GPIO.LOW

def send(pattern):
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        for i, t in enumerate(pattern):
            f.write(("pulse " if i % 2 == 0 else "space ") + str(t) + "\n")
        name = f.name

    subprocess.run(
        ["ir-ctl", "-d", DEV, "--send", name],
        check=False
    )
    os.remove(name)

def variants():
    for idx in range(len(BASE)):
        for v in VALUES:
            if BASE[idx] == v:
                continue
            test = BASE.copy()
            test[idx] = v
            yield idx, v, test

def main():
    print("Scanner initiated.")
    print("Press the ACTION button to send each ID variant.")
    print("CTRL+C to exit.\n")

    try:
        for idx, v, pattern in variants():
            print(f"Ready to test: index={idx}, value={v}")

            while True:
                if action_pressed():
                    now = time.monotonic()
                    if now - last_press > DEBOUNCE:
                        break
                time.sleep(0.01)

            print(f"Sending ID (idx={idx}, val={v})")
            send(pattern)

            while action_pressed():
                time.sleep(0.01)

            time.sleep(0.15)

    except KeyboardInterrupt:
        pass
    finally:
        GPIO.cleanup()
        print("\nScanner stopped.")

if __name__ == "__main__":
    main()
