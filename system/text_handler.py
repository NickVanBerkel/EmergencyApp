from plyer import sms
import sqlite3
from datetime import datetime

from config.config import DB_FILE, EMERGENCY_TEXT_MESSAGE, EMERGENCY_TEXT_SUCCESS_MESSAGE, EMERGENCY_TEXT_PARTIAL_SUCCESS_MESSAGE, EMERGENCY_TEXT_FAIL_MESSAGE, EMERGENCY_TEXT_FAIL_NO_CONTACTS_MESSAGE
from system.battery_handler import BatteryHandler
from system.contact_handler import ContactHandler


class EmergencyTextHandler:

    def __init__(self):
        self.db = sqlite3.connect(DB_FILE)
        self.battery_handler = BatteryHandler()
        self.contact_handler = ContactHandler()

    def execute_emergency_text_action(self):
        recipients = self.contact_handler.get_phone_numbers()
        if len(recipients):
            battery_percentage, charging = self.battery_handler.get_battery_status()
            emergency_text_action_id = self.save_emergency_text_action(battery_percentage, charging)
            message = EMERGENCY_TEXT_MESSAGE.format(battery_percentage)

            success = 0
            for recipient in recipients:
                text_result = self.send_emergency_text(recipient, message)
                self.save_emergency_text(emergency_text_action_id, recipient, text_result)
                success += int(text_result)

            if success == len(recipients):
                return True, EMERGENCY_TEXT_SUCCESS_MESSAGE.format(str(success))
            elif 0 < success < len(recipients):
                return True, EMERGENCY_TEXT_PARTIAL_SUCCESS_MESSAGE.format(str(success), str(len(recipients) - success))
            else:
                return False, EMERGENCY_TEXT_FAIL_MESSAGE
        else:
            return False, EMERGENCY_TEXT_FAIL_NO_CONTACTS_MESSAGE

    def send_emergency_text(self, recipient, message):
        result = False
        try:
            sms.send(recipient=recipient, message=message)
            result = True
        finally:
            return result

    def save_emergency_text(self, emergency_text_action_id, contact_id, result):
        cursor = self.db.cursor()

        text_log_tuple = (None, emergency_text_action_id, contact_id, result)
        query = f"""
                INSERT INTO emergency_text_sent VALUES (?, ?, ?, ?)
                """

        cursor.execute(query, text_log_tuple)
        self.db.commit()
        cursor.close()

    def save_emergency_text_action(self, battery_percentage, charging):
        cursor = self.db.cursor()

        action_log_tuple = (None, battery_percentage, charging)
        query = f"""
        INSERT INTO emergency_text_action VALUES (?, ?, ?, datetime('now', 'localtime'))
        """

        cursor.execute(query, action_log_tuple)
        emergency_text_action_id = cursor.lastrowid
        self.db.commit()
        cursor.close()

        return emergency_text_action_id

    def get_last_text_sent(self):
        cursor = self.db.cursor()

        query = """
        SELECT max(created_at) FROM emergency_text_action
        """

        cursor.execute(query)
        result = cursor.fetchone()[0]
        if result:
            return datetime.strptime(result, '%Y-%m-%d %H:%M:%S')
        else:
            return None

# handler = EmergencyTextHandler()
# handler.execute_emergency_text_action()