from kivy.clock import Clock
from plyer import notification
from os.path import join
from os import getcwd

from system.battery_handler import BatteryHandler


class NotificationHandler:

    def __init__(self):
        self.battery_handler = BatteryHandler()
        self.notification_block = False
        self.check_emergency_notification_conditions(0)
        self.notification_event = Clock.schedule_interval(self.check_emergency_notification_conditions, 15)

    def cancel_schedule_emergency_notification(self):
        self.notification_event.cancel()

    def check_emergency_notification_conditions(self, dt):
        battery_percentage, charging = self.battery_handler.get_battery_status()
        if not battery_percentage:
            pass
        elif not self.notification_block and not charging and battery_percentage <= 5:
            self.send_emergency_notification(battery_percentage)
            self.notification_block = True
        elif battery_percentage > 5:
            self.notification_block = False

    def send_emergency_notification(self, battery_percentage):
        cur_battery = str(battery_percentage)
        title = "Send text to emergency contacts"
        message = f"Your battery has dropped to {cur_battery}%. Click here if you want to send out a text to your emergency contacts"

        app_name = "EmergencyActionApp"
        kwargs = {'title': title, 'message': message, 'app_name': app_name,
                  'app_icon': join(getcwd(),
                                   'media/alarm.png')}

        notification.notify(**kwargs)
