import os
import time
import subprocess
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)

PIN_MODE = 23   # Pin 16
PIN_ACTION = 24 # Pin 18

GPIO.setup(PIN_MODE, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(PIN_ACTION, GPIO.IN, pull_up_down=GPIO.PUD_UP)

RAW_DIR = "./raw"
LIRC_DEV = "/dev/lirc0"

def raw_path(name: str) -> str:
    return os.path.join(RAW_DIR, f"{name}.raw")

def send_raw(name: str) -> bool:
    path = raw_path(name)
    if not os.path.exists(path):
        print(f"[WARN] Path not found: {path}")
        return False

    # ir-ctl -d /dev/lirc0 --send <archivo>
    subprocess.run(["ir-ctl", "-d", LIRC_DEV, "--send", path], check=False)
    return True

class Mode:
    name = "base"
    def on_enter(self): pass
    def on_exit(self): pass
    def tick(self, dt: float): pass
    def on_action_change(self, pressed: bool): pass

class AutoMode(Mode):
    name = "automatic"
    def __init__(self):
        self.colors = ["blue", "yellow", "white", "green"]
        self.idx = 0
        self.timer = 0.0

    def on_enter(self):
        self.idx = 0
        self.timer = 0.0
        print("[MODE] Automatic")

        send_raw(self.colors[self.idx])

    def tick(self, dt: float):
        self.timer += dt
        if self.timer >= 1.0:
            self.timer = 0.0
            self.idx = (self.idx + 1) % len(self.colors)
            send_raw(self.colors[self.idx])

class ManualMode(Mode):
    name = "manual"

    def on_enter(self):
        print("[MODE] Manual")
        send_raw("off")

    def on_action_change(self, pressed: bool):
        if pressed:
            send_raw("blue")
        else:
            ok = send_raw("off")
            if not ok:
                print("[ERROR] off.raw not found")
MODES = [
    AutoMode(),
    ManualMode(),
]

DEBOUNCE_SEC = 0.18

last_mode_press = 0.0
prev_action_pressed = False

def is_pressed(pin: int) -> bool:
    return GPIO.input(pin) == GPIO.LOW

def next_mode(current_index: int) -> int:
    return (current_index + 1) % len(MODES)

def main():
    global last_mode_press, prev_action_pressed

    mode_idx = 0
    current_mode = MODES[mode_idx]
    current_mode.on_enter()

    prev_action_pressed = is_pressed(PIN_ACTION)
    last_time = time.monotonic()

    try:
        while True:
            now = time.monotonic()
            dt = now - last_time
            last_time = now

            if is_pressed(PIN_MODE):
                if now - last_mode_press > DEBOUNCE_SEC:
                    last_mode_press = now
                    current_mode.on_exit()
                    mode_idx = next_mode(mode_idx)
                    current_mode = MODES[mode_idx]
                    current_mode.on_enter()

                    time.sleep(0.05)

            action_pressed = is_pressed(PIN_ACTION)
            if action_pressed != prev_action_pressed:
                prev_action_pressed = action_pressed
                current_mode.on_action_change(action_pressed)

            current_mode.tick(dt)

            time.sleep(0.01)

    finally:
        GPIO.cleanup()

if __name__ == "__main__":
    main()
