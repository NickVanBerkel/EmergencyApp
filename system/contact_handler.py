import sqlite3
import phonenumbers
from config.config import DB_FILE, ADD_CONTACT_SUCCESS_MESSAGE, ADD_CONTACT_NUMBER_INVALID_MESSAGE, ADD_CONTACT_NUMBER_EXISTS_MESSAGE, DELETE_CONTACT_SUCCESS_MESSAGE, DELETE_CONTACT_FAIL_MESSAGE

class ContactHandler:

    def __init__(self):
        self.db = sqlite3.connect(DB_FILE)

    def add_emergency_contact(self, contact_name, phone_number):
        normalized_phone_number = phone_number.replace(' ', '')
        result, message = self.validate_phone_number(normalized_phone_number)
        if result:
            self.save_emergency_contact(contact_name, normalized_phone_number)
            return True, ADD_CONTACT_SUCCESS_MESSAGE
        else:
            return result, message

    def delete_emergency_contact(self, contact_id):
        try:
            self.soft_delete_emergency_contact(contact_id)
            return True, DELETE_CONTACT_SUCCESS_MESSAGE
        except:
            return False, DELETE_CONTACT_FAIL_MESSAGE

    def soft_delete_emergency_contact(self, contact_id):
        cursor = self.db.cursor()

        query = f"""
                        UPDATE emergency_contact
                        SET updated_at = datetime('now', 'localtime'), deleted_at = datetime('now', 'localtime')
                        WHERE id = {contact_id}
                        """

        cursor.execute(query)
        self.db.commit()
        cursor.close()

    def save_emergency_contact(self, contact_name, phone_number):
        cursor = self.db.cursor()

        contact_tuple = (None, contact_name, phone_number)
        query = f"""
                INSERT INTO emergency_contact VALUES (?, ?, ?, datetime('now', 'localtime'), null, null)
                """

        cursor.execute(query, contact_tuple)
        self.db.commit()
        cursor.close()

    def validate_phone_number(self, phone_number):
        try:
            number = phonenumbers.parse(phone_number, None)
            if not phonenumbers.is_possible_number(number):
                return False, ADD_CONTACT_NUMBER_INVALID_MESSAGE
            else:
                existing_phone_numbers = self.get_phone_numbers()
                if phone_number in existing_phone_numbers:
                    return False, ADD_CONTACT_NUMBER_EXISTS_MESSAGE
                else:
                    return True, None
        except:
            return False, ADD_CONTACT_NUMBER_INVALID_MESSAGE

    def get_phone_numbers(self):
        cursor = self.db.cursor()

        query = """
                SELECT phone_number FROM emergency_contact
                WHERE deleted_at IS NULL
                """

        cursor.execute(query)
        result = cursor.fetchall()
        contact_numbers = [row[0] for row in result]
        return contact_numbers

    def get_emergency_contacts(self):
        cursor = self.db.cursor()

        query = """
                SELECT id, name, phone_number FROM emergency_contact
                WHERE deleted_at IS NULL
                """

        cursor.execute(query)
        result = cursor.fetchall()
        return result

