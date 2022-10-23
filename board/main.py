# This is your main script.

import time
import ujson

from marax import get_sensor
from shot_timer import get_shot_timer

marax = get_sensor()
shot_timer = get_shot_timer()


PUBLISH_INTERVAL_MS = 2000
last_update_ticks = time.ticks_ms() - PUBLISH_INTERVAL_MS

DISPLAY_UPDATE_INTERVAL_MS = 250
last_display_update_ticks = time.ticks_ms() - DISPLAY_UPDATE_INTERVAL_MS

marax.connect()

last_result = None


def wait_for_activity():
    while True:
        line = marax.recv_line()
        if line is not None:
            # It's okay to drop the line, we'll grab the next one
            break
        time.sleep_ms(1000)
        print('Waiting for machine to power on..')


last_valid_result = None

def update_display(r: dict):
    display.fill(0)
    if r is None:
        display.text("ERROR", 0, 0, 1)
    elif r.get("missing_water", 0):
        display.text("Refill water tank!", 0, 0, 1)
    else:
        display.text(r['mode'], 0, 0, 1)
        display.text("HX: {}".format(r['hx_temp']), 0, 10, 1)
        display.text(
            "Boiler: {}/{}".format(r['boiler_temp'], r['boiler_target']), 0,
            20, 1)
        if shot_timer.elapsed is not None:
            # also need to display the shot timer
            display.text('TIMER: ' + str(shot_timer.elapsed) + 's', 0, 64 - 20,
                        1)
        if r['heating_element_state'] == True:
            display.text("HEATING...", 0, 64 - 10, 1)

        display.show()


reported_offline = True


def machine_is_online(line: str) -> bool:
    global reported_offline
    if line is None:
        if marax.is_offline():
            if mqtt is not None:
                print('MaraX is offline!')
                mqtt.publish(MQTT_TOPIC_STATUS, 'offline')
            reported_offline = True
            display.fill(0)
            display.text("MaraX OFF", 0, 0, 1)
            display.show()
            time.sleep(10)
            display.poweroff()
            wait_for_activity()
    else:
        if reported_offline is not None and reported_offline:
            reported_offline = None
            mqtt.publish(MQTT_TOPIC_STATUS, 'online')
            print('MaraX is online!')
            display.poweron()
            display.fill(0)
            display.text("MaraX ON", 0, 0, 1)
            display.show()
    return line is not None


try:
    while True:
        line = marax.recv_line()
        if not machine_is_online(line):
            continue
        try:
            r = marax.parse(line)
            last_valid_result = r
        except Exception as e:
            print('parsing failure for line: {}'.format(line))
            import sys
            sys.print_exception(e)
            continue
        shot_timer.check(r)
        # append the pump status to the resuly
        r["shot"] = int(shot_timer.elapsed is not None)

        # publish to mqtt topic
        if mqtt is not None and time.ticks_ms() - last_update_ticks >= PUBLISH_INTERVAL_MS:
            print('publishing')
            mqtt.publish(MQTT_TOPIC_SENSOR, ujson.dumps(r))
            last_update_ticks = time.ticks_ms()

        if time.ticks_ms() - last_display_update_ticks >= DISPLAY_UPDATE_INTERVAL_MS:
            update_display(r)
            last_display_update_ticks = time.ticks_ms()

except Exception as e:
    display.fill(0)
    display.text("EXCEPTION!!!", 0, 10, 1)
    display.text(str(type(e).__name__), 0, 20, 1)
    display.show()
    import sys
    while True:
        sys.print_exception(e)
        time.sleep_ms(1000)
