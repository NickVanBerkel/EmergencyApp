from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import StringProperty, ObjectProperty, NumericProperty
from kivymd.app import MDApp
from kivymd.uix.behaviors import RoundedRectangularElevationBehavior
from kivymd.uix.card import MDCard
from kivymd.uix.list import MDList, TwoLineAvatarIconListItem
from kivymd.uix.button import MDRoundFlatIconButton, MDFlatButton, MDRaisedButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.snackbar import Snackbar
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.stacklayout import MDStackLayout
from plyer.utils import platform
import sqlite3

from config.config import DB_FILE
from system.battery_handler import BatteryHandler
from system.text_handler import EmergencyTextHandler
from system.notification_handler import NotificationHandler
from system.contact_handler import ContactHandler

if platform == 'android':
    from android.permissions import request_permissions, Permission

    request_permissions([Permission.SEND_SMS])

__version__ = "0.2.1"


class BatteryStatusCard(MDCard, RoundedRectangularElevationBehavior):
    battery_percentage_lbl = StringProperty()
    battery_percentage_icon = ObjectProperty("battery-unknown")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.battery_handler = BatteryHandler()
        self.battery_event = Clock.schedule_interval(self.update_battery_level, 5)
        self.update_battery_level(0)

    def update_battery_level(self, dt):
        battery_percentage, charging = self.battery_handler.get_battery_status()
        if battery_percentage:
            self.battery_percentage_lbl = str(int(battery_percentage)) + "%"
            icon_percentage = int(battery_percentage - (battery_percentage % 10))

            is_charging = ""
            if charging:
                is_charging = "-charging"

            if icon_percentage < 10 and not charging:
                self.battery_percentage_icon = "battery-alert"
            else:
                self.battery_percentage_icon = f"battery{is_charging}-{str(icon_percentage)}"
        else:
            self.battery_percentage_lbl = "N.A."
            self.battery_percentage_icon = "battery-unknown"


class EmergencyContactList(MDList):
    contact_handler = ContactHandler()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.update_emergency_contacts()

    def update_emergency_contacts(self):
        if len(self.children):
            self.clear_widgets()
        emergency_contacts = self.contact_handler.get_emergency_contacts()
        for contact in emergency_contacts:
            cntct = EmergencyContactListItem(text=str(contact[1]), secondary_text=str(contact[2]), emergency_contact_id=contact[0])
            self.add_widget(cntct)

class EmergencyContactListItem(TwoLineAvatarIconListItem):
    emergency_contact_id = NumericProperty()


class EmergencyTextCard(MDCard, RoundedRectangularElevationBehavior):
    last_text_sent_lbl = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text_handler = EmergencyTextHandler()
        self.last_text_sent = None
        self.update_last_text_sent()

    def update_last_text_sent(self):
        update = self.text_handler.get_last_text_sent()
        self.last_text_sent = update
        if self.last_text_sent:
            self.last_text_sent_lbl = f"[b]{update.date().strftime('%d %B').lstrip('0')}[/b] - {update.time().strftime('%H:%M')}"


class EmergencyTextButton(MDRoundFlatIconButton):

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.text_handler = EmergencyTextHandler()

    def initiate_emergency_text_action(self):
        result, message = self.text_handler.execute_emergency_text_action()

        action_result_toast = Snackbar(text=message,
                                              radius=[10, 10, 10, 10],
                                              snackbar_x="10dp",
                                              snackbar_y="10dp",
                                              size_hint_x=.5)
        action_result_toast.size_hint_x = (
                                                         Window.width - (action_result_toast.snackbar_x * 2)
                                                 ) / Window.width
        action_result_toast.open()

        for child in self.parent.children:
            if type(child).__name__ == 'EmergencyTextCard':
                child.update_last_text_sent()

class HomeView(MDStackLayout):
    pass

class AddEmergencyContactsContent(MDGridLayout):
    pass

class EmergencyContactsView(MDFloatLayout):
    dialog = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.contact_handler = ContactHandler()

    def open_add_contact_dialog(self):
        if not self.dialog:
            self.dialog = MDDialog(
                title='Add emergency contact',
                type="custom",
                content_cls=AddEmergencyContactsContent(),
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        text_color=self.parent.theme_cls.primary_color,
                        on_release=self.close_contact_dialog
                    ),
                    MDRaisedButton(
                        text="ACCEPT",
                        on_release=self.add_new_contact
                    )]
            )
            self.dialog.open()

    def open_delete_contact_dialog(self, contact_id, contact_name):
        if not self.dialog:
            self.dialog = MDDialog(
                text=f'Delete {contact_name} from emergency contacts?',
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        theme_text_color="Custom",
                        text_color=self.parent.theme_cls.primary_color,
                        on_release=self.close_contact_dialog
                    ),
                    MDRaisedButton(
                        text="DELETE",
                        on_release=lambda *args: self.delete_contact(contact_id, contact_name, *args)
                    )]
            )
            self.dialog.open()

    def close_contact_dialog(self, *args):
        self.dialog.dismiss(force=True)
        self.dialog = None

    def remove_error_message(self, *args):
        self.dialog.content_cls.ids.phone_number_input.helper_text = ""
        self.dialog.content_cls.ids.phone_number_input.error = False

    def add_new_contact(self, *args):
        contact_name = self.dialog.content_cls.ids.contact_name_input.text
        phone_number = self.dialog.content_cls.ids.phone_number_input.text
        result, message = self.contact_handler.add_emergency_contact(contact_name, phone_number)
        if result:
            self.close_contact_dialog()
            add_contact_toast = Snackbar(text=message.format(contact_name),
                                                  radius=[10, 10, 10, 10],
                                                  snackbar_x="10dp",
                                                  snackbar_y="10dp",
                                                  size_hint_x=.5)
            add_contact_toast.size_hint_x = (
                                                             Window.width - (add_contact_toast.snackbar_x * 2)
                                                     ) / Window.width
            add_contact_toast.open()
            self.ids.emergency_contacts.update_emergency_contacts()
        else:
            self.dialog.content_cls.ids.phone_number_input.helper_text = message
            self.dialog.content_cls.ids.phone_number_input.error = True
            Clock.schedule_once(self.remove_error_message, 3)

    def delete_contact(self, contact_id, contact_name, *args):
        self.close_contact_dialog()
        result, message = self.contact_handler.delete_emergency_contact(contact_id)
        delete_contact_toast = Snackbar(text=message.format(contact_name),
                                              radius=[10, 10, 10, 10],
                                              snackbar_x="10dp",
                                              snackbar_y="10dp",
                                              size_hint_x=.5)
        delete_contact_toast.size_hint_x = (
                                                         Window.width - (delete_contact_toast.snackbar_x * 2)
                                                 ) / Window.width
        delete_contact_toast.open()
        self.ids.emergency_contacts.update_emergency_contacts()

class EmergencyActionApp(MDApp):

    def build(self):
        return Builder.load_file('EmergencyAction.kv')

    def on_start(self):
        self.load_database()
        self.notification_handler = NotificationHandler()
        self.root.ids.home_screen.add_widget(HomeView())
        self.root.ids.emergency_contacts_screen.add_widget(EmergencyContactsView())

    def load_database(self):
        db = sqlite3.connect(DB_FILE)
        cursor = db.cursor()

        with open('data/init.sql', 'r') as sql_file:
            init = sql_file.read()
        sql_file.close()

        for create_table in init.split(';'):
            cursor.execute(create_table)

        db.commit()
        db.close()


EmergencyActionApp().run()
