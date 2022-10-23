import time
from machine import Pin

try:
    from config import SHOT_TIMER
except ImportError:
    SHOT_TIMER = ''


class ShotTimerBase:
    _GRACE_TIMEOUT_MS = 666

    def __init__(self):
        self.start_time = None
        self.stop_time = None

    @property
    def elapsed(self):
        if self.start_time is not None:
            return (time.ticks_ms() - self.start_time) // 1000
        return None

    def start(self):
        print('[PUMP]: Pump detected! starting timer')
        self.start_time = time.ticks_ms()
        self.stop_time = None

    def stop(self):
        print('[PUMP] Shot timer stopped after {}s'.format(self.elapsed))
        self.start_time = None
        self.stop_time = None

    def check(self, marax_data: dict):
        pump_detected = self.detect_pump(marax_data)

        timer_started = self.start_time is not None

        if pump_detected and not timer_started:
            self.start()
        if not pump_detected and timer_started:
            if self.stop_time is None:
                self.stop_time = time.ticks_ms()
            elif time.ticks_ms() - self.stop_time > self._GRACE_TIMEOUT_MS:
                self.stop()
        else:
            self.stop_time = None

    def detect_pump(self, marax_data: dict) -> bool:
        raise NotImplemented


class ReedSwitchShotTimer(ShotTimerBase):
    def __init__(self):
        super().__init__()
        self.pin = Pin(0, Pin.IN, Pin.PULL_UP)
    
    def detect_pump(self, _marax_data: dict):
        return self.pin.value() == 0


class UartShotTimer(ShotTimerBase):
    def detect_pump(self, marax_data: dict) -> bool:
        assert marax_data["marax_version"] == "v2"
        return marax_data["pump_running"] == 1


class NoShotTimer(ShotTimerBase):
    def detect_pump(self, marax_data: dict) -> bool:
        return False


if SHOT_TIMER == 'reed':
    ShotTimerCls = ReedSwitchShotTimer
elif SHOT_TIMER == 'uart':
    ShotTimerCls = UartShotTimer
else:
    ShotTimerCls = NoShotTimer


_shot_timer_inst = None

def get_shot_timer() -> ShotTimerBase:
    global _shot_timer_inst
    if _shot_timer_inst is None:
        _shot_timer_inst = ShotTimerCls()
    return _shot_timer_inst
