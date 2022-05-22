from plyer import battery


class BatteryHandler:

    def __init__(self):
        pass

    def get_battery_status(self):
        if battery.status['percentage']:
            return int(battery.status['percentage']), battery.status['isCharging']
        else:
            return battery.status['percentage'], battery.status['isCharging']
