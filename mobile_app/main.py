# medicine_app_kivy.py
# نسخه کیوی از یادآور هوشمند دارو

import kivy
kivy.require('2.1.0')

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.checkbox import CheckBox
from kivy.uix.widget import Widget
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty, ListProperty
from kivy.logger import Logger
Logger.setLevel("DEBUG")
import sqlite3
import threading as trd
import bcrypt
from datetime import datetime
import schedule
import time
import random
import json
import os

# تنظیم اندازه پنجره برای دسکتاپ
Window.size = (1100, 700)

DB_PATH = "medicine_mobile.db"
SETTINGS_FILE = "settings.json"

# ================= DATABASE =================
class DBManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH)
        self.cur = self.conn.cursor()
        self.setup()

    def setup(self):
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS users(
            username TEXT PRIMARY KEY,
            password BLOB,
            role TEXT,
            fullname TEXT
        )""")
        self.cur.execute("""
        CREATE TABLE IF NOT EXISTS meds(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user TEXT,
            patient TEXT,
            nurse TEXT,
            name TEXT,
            time TEXT,
            days TEXT
        )""")
        self.conn.commit()

    def register(self, u, p, role, fullname):
        try:
            hashed = bcrypt.hashpw(p.encode(), bcrypt.gensalt())
            self.cur.execute(
                "INSERT INTO users VALUES (?,?,?,?)",
                (u, hashed, role, fullname)
            )
            self.conn.commit()
            return True
        except:
            return False

    def login(self, u, p):
        self.cur.execute(
            "SELECT password,role,fullname FROM users WHERE username=?",
            (u,)
        )
        row = self.cur.fetchone()
        if not row:
            return None
        db_hash = row[0]
        if bcrypt.checkpw(p.encode(), db_hash):
            return row[1], row[2]
        return None

    def add_med(self, data):
        self.cur.execute("""INSERT INTO meds(user,patient,nurse,name,time,days)
                            VALUES(?,?,?,?,?,?)""",
                         (data["user"], data["patient"], data["nurse"],
                          data["name"], data["time"], ",".join(data["days"])))
        self.conn.commit()

    def get_user_meds(self, user):
        self.cur.execute("SELECT * FROM meds WHERE user=?", (user,))
        return self.cur.fetchall()

    def delete_med(self, id):
        self.cur.execute("DELETE FROM meds WHERE id=?", (id,))
        self.conn.commit()


# ================= SCHEDULER =================
class Scheduler:
    def __init__(self, db, user, fullname, app):
        self.db = db
        self.user = user
        self.fullname = fullname
        self.app = app
        self.reload()
        trd.Thread(target=self.loop, daemon=True).start()

    def notify(self, patient, nurse, name):
        text = f"Nurse: {nurse} | Patient: {patient} | Medicine: {name}"
        Clock.schedule_once(lambda dt: self.app.show_notification(text), 0)

    def reload(self):
        schedule.clear()
        meds = self.db.get_user_meds(self.user)
        for m in meds:
            t = datetime.strptime(m[5], "%H:%M").strftime("%H:%M")
            for d in m[6].split(","):
                getattr(schedule.every(), d).at(t).do(self.notify, m[2], m[3], m[4])

    def loop(self):
        while True:
            schedule.run_pending()
            time.sleep(20)


# ================= CUSTOM WIDGETS =================
class ColoredLabel(Label):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.color = get_color_from_hex('#333333')
        self.font_size = dp(14)


class ColoredButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = get_color_from_hex('#00cec9')
        self.color = get_color_from_hex('#000000')
        self.font_size = dp(14)
        self.size_hint_y = None
        self.height = dp(44)
        

# ================= LOGIN SCREEN =================
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = App.get_running_app().db
        self.build_ui()
        self.generate_captcha()

    def build_ui(self):
        layout = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(30))
        
        # عنوان
        title = Label(
            text='یادآور هوشمند دارو',
            font_size=dp(28),
            bold=True,
            color=get_color_from_hex('#1a237e')
        )
        layout.add_widget(title)
        
        # فرم ورود
        form = BoxLayout(orientation='vertical', spacing=dp(10), size_hint_y=None, height=dp(350))
        form.pos_hint = {'center_x': 0.5}
        
        form.add_widget(Label(text='نام کاربری:', font_size=dp(14), size_hint_y=None, height=dp(30)))
        self.username_input = TextInput(multiline=False, font_size=dp(14), size_hint_y=None, height=dp(40))
        form.add_widget(self.username_input)
        
        form.add_widget(Label(text='رمز عبور:', font_size=dp(14), size_hint_y=None, height=dp(30)))
        self.password_input = TextInput(password=True, multiline=False, font_size=dp(14), size_hint_y=None, height=dp(40))
        form.add_widget(self.password_input)
        
        # کپچا
        captcha_layout = BoxLayout(orientation='vertical', spacing=dp(5), size_hint_y=None, height=dp(100))
        self.captcha_label = Label(text='', font_size=dp(16), size_hint_y=None, height=dp(30))
        captcha_layout.add_widget(self.captcha_label)
        
        captcha_input_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(40))
        self.captcha_input = TextInput(multiline=False, font_size=dp(14), size_hint_x=0.7)
        refresh_btn = Button(text='🔄', size_hint_x=0.3, background_color=get_color_from_hex('#4fc3f7'))
        refresh_btn.bind(on_press=lambda x: self.generate_captcha())
        captcha_input_layout.add_widget(self.captcha_input)
        captcha_input_layout.add_widget(refresh_btn)
        captcha_layout.add_widget(captcha_input_layout)
        form.add_widget(captcha_layout)
        
        layout.add_widget(form)
        
        # دکمه‌ها
        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))
        
        login_btn = ColoredButton(text='ورود')
        login_btn.bind(on_press=self.do_login)
        btn_layout.add_widget(login_btn)
        
        nurse_btn = Button(text='ثبت پرستار', background_color=get_color_from_hex('#0984e3'), color=get_color_from_hex('#ffffff'))
        nurse_btn.bind(on_press=lambda x: self.register('nurse'))
        btn_layout.add_widget(nurse_btn)
        
        patient_btn = Button(text='ثبت بیمار', background_color=get_color_from_hex('#00b894'), color=get_color_from_hex('#ffffff'))
        patient_btn.bind(on_press=lambda x: self.register('patient'))
        btn_layout.add_widget(patient_btn)
        
        layout.add_widget(btn_layout)
        layout.add_widget(Widget())  # Spacer
        
        self.add_widget(layout)

    def generate_captcha(self):
        self.num1 = random.randint(1, 20)
        self.num2 = random.randint(1, 20)
        self.captcha_label.text = f'کد امنیتی: {self.num1} + {self.num2} = ؟'

    def register(self, role):
        username = self.username_input.text
        password = self.password_input.text
        if not username or not password:
            self.show_popup('خطا', 'نام کاربری و رمز عبور را وارد کنید')
            return
        
        # نمایش پاپ‌آپ برای وارد کردن نام کامل
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        content.add_widget(Label(text='نام کامل خود را وارد کنید:', font_size=dp(14)))
        fullname_input = TextInput(multiline=False, font_size=dp(14), size_hint_y=None, height=dp(40))
        content.add_widget(fullname_input)
        
        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))
        ok_btn = Button(text='تایید', background_color=get_color_from_hex('#00cec9'))
        cancel_btn = Button(text='انصراف', background_color=get_color_from_hex('#d63031'))
        btn_layout.add_widget(ok_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(title='ثبت نام', content=content, size_hint=(0.8, 0.5))
        
        def on_ok(instance):
            fullname = fullname_input.text
            if not fullname:
                return
            if self.db.register(username, password, role, fullname):
                popup.dismiss()
                self.show_popup('موفق', 'ثبت نام با موفقیت انجام شد')
            else:
                self.show_popup('خطا', 'این نام کاربری از قبل ثبت شده است')
        
        def on_cancel(instance):
            popup.dismiss()
        
        ok_btn.bind(on_press=on_ok)
        cancel_btn.bind(on_press=on_cancel)
        popup.open()

    def do_login(self, instance):
        try:
            if int(self.captcha_input.text) != self.num1 + self.num2:
                self.show_popup('خطا', 'کد امنیتی اشتباه است')
                self.generate_captcha()
                self.captcha_input.text = ''
                return
        except:
            self.show_popup('خطا', 'کد امنیتی را وارد کنید')
            return
        
        result = self.db.login(self.username_input.text, self.password_input.text)
        if not result:
            self.show_popup('خطا', 'نام کاربری یا رمز عبور اشتباه است')
            return
        
        role, fullname = result
        app = App.get_running_app()
        app.user = self.username_input.text
        app.fullname = fullname
        app.role = role
        
        # راه‌اندازی زمان‌بندی
        app.scheduler = Scheduler(app.db, app.user, app.fullname, app)
        
        # رفتن به صفحه داشبورد
        app.root.current = 'dashboard'

    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        content.add_widget(Label(text=message, font_size=dp(14)))
        btn = Button(text='باشه', size_hint_y=None, height=dp(40), background_color=get_color_from_hex('#00cec9'))
        popup = Popup(title=title, content=content, size_hint=(0.6, 0.4))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()


# ================= DASHBOARD SCREEN =================
class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.build_ui()
        
    def build_ui(self):
        main_layout = BoxLayout(orientation='horizontal')
        
        # سایدبار راست
        sidebar = BoxLayout(orientation='vertical', size_hint_x=0.2, spacing=dp(5), padding=dp(10))
        sidebar_background = get_color_from_hex('#151522')
        
        # دکمه‌های سایدبار
        btn_data = [
            ('💊 افزودن دارو', self.show_add_med),
            ('📋 لیست داروها', self.refresh_table),
            ('📊 آمار', self.show_stats),
            ('❓ راهنما', self.show_help),
            ('ℹ️ درباره ما', self.show_about),
            ('🎨 تغییر تم', self.toggle_theme),
            ('🗑️ حذف انتخاب', self.delete_med),
            ('🚪 خروج', self.logout),
        ]
        
        for text, cmd in btn_data:
            btn = Button(
                text=text,
                size_hint_y=None,
                height=dp(44),
                background_color=get_color_from_hex('#2d2d44') if self.app.dark_mode else get_color_from_hex('#dddddd'),
                color=get_color_from_hex('#ffffff') if self.app.dark_mode else get_color_from_hex('#000000'),
                font_size=dp(12)
            )
            btn.bind(on_press=cmd)
            sidebar.add_widget(btn)
        
        sidebar.add_widget(Widget())  # Spacer
        
        # محتوای اصلی
        content = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        
        # عنوان
        title_text = f'{self.app.role.upper()} PANEL - {self.app.fullname}'
        title = Label(
            text=title_text,
            font_size=dp(22),
            bold=True,
            color=get_color_from_hex('#1a237e'),
            size_hint_y=None,
            height=dp(50)
        )
        content.add_widget(title)
        
        # جدول داروها
        self.table = ScrollView()
        self.table_layout = GridLayout(cols=5, spacing=dp(2), size_hint_y=None)
        self.table_layout.bind(minimum_height=self.table_layout.setter('height'))
        
        # هدر جدول
        headers = ['شناسه', 'بیمار', 'دارو', 'ساعت', 'روزها']
        for h in headers:
            lbl = Label(
                text=h,
                bold=True,
                size_hint_y=None,
                height=dp(30),
                color=get_color_from_hex('#1a237e'),
                font_size=dp(13)
            )
            self.table_layout.add_widget(lbl)
        
        self.table.add_widget(self.table_layout)
        content.add_widget(self.table)
        
        main_layout.add_widget(content)
        main_layout.add_widget(sidebar)
        self.add_widget(main_layout)
        
        # بارگذاری داده‌ها
        Clock.schedule_once(lambda dt: self.refresh_table(None), 0.1)
    
    def refresh_table(self, instance):
        # پاک کردن ردیف‌های قبلی (به جز هدر)
        children = self.table_layout.children[:]
        for child in children:
            if child.text not in ['شناسه', 'بیمار', 'دارو', 'ساعت', 'روزها']:
                self.table_layout.remove_widget(child)
        
        # بارگذاری داده‌های جدید
        if self.app.user:
            meds = self.app.db.get_user_meds(self.app.user)
            days_persian = {
                "monday": "دوشنبه", "tuesday": "سه‌شنبه", "wednesday": "چهارشنبه",
                "thursday": "پنج‌شنبه", "friday": "جمعه", "saturday": "شنبه", "sunday": "یکشنبه"
            }
            
            for m in meds:
                days_list = [days_persian.get(d.strip(), d.strip()) for d in m[6].split(",")]
                days_str = "،".join(days_list)
                values = [str(m[0]), m[2], m[4], m[5], days_str]
                
                for val in values:
                    lbl = Label(
                        text=val,
                        size_hint_y=None,
                        height=dp(30),
                        font_size=dp(12),
                        color=get_color_from_hex('#333333')
                    )
                    self.table_layout.add_widget(lbl)
                
                # ذخیره ID برای حذف
                id_btn = Button(
                    text='انتخاب',
                    size_hint_y=None,
                    height=dp(30),
                    background_color=get_color_from_hex('#4fc3f7'),
                    font_size=dp(10)
                )
                id_btn.med_id = m[0]
                id_btn.bind(on_press=self.select_med)
                self.table_layout.add_widget(id_btn)
    
    def select_med(self, instance):
        self.selected_med_id = instance.med_id
        self.show_popup('انتخاب', f'دارو با شناسه {instance.med_id} انتخاب شد')
    
    def show_add_med(self, instance):
        if not self.app.user:
            self.show_popup('خطا', 'وارد حساب کاربری خود شوید')
            return
        
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        
        content.add_widget(Label(text='نام بیمار:', font_size=dp(14)))
        patient_input = TextInput(multiline=False, font_size=dp(14), size_hint_y=None, height=dp(40))
        content.add_widget(patient_input)
        
        content.add_widget(Label(text='نام دارو:', font_size=dp(14)))
        name_input = TextInput(multiline=False, font_size=dp(14), size_hint_y=None, height=dp(40))
        content.add_widget(name_input)
        
        content.add_widget(Label(text='زمان (HH:MM):', font_size=dp(14)))
        time_input = TextInput(multiline=False, font_size=dp(14), size_hint_y=None, height=dp(40))
        content.add_widget(time_input)
        
        content.add_widget(Label(text='روزهای مصرف:', font_size=dp(14)))
        
        # روزهای هفته
        days_layout = GridLayout(cols=4, spacing=dp(5), size_hint_y=None, height=dp(200))
        days_persian = {
            "monday": "دوشنبه", "tuesday": "سه‌شنبه", "wednesday": "چهارشنبه",
            "thursday": "پنج‌شنبه", "friday": "جمعه", "saturday": "شنبه", "sunday": "یکشنبه"
        }
        days_vars = {}
        
        for d, label in days_persian.items():
            day_box = BoxLayout(orientation='horizontal', size_hint_y=None, height=dp(30))
            var = BooleanProperty(False)
            days_vars[d] = {'var': var, 'checkbox': None}
            
            cb = CheckBox(size_hint_x=0.3)
            days_vars[d]['checkbox'] = cb
            day_box.add_widget(cb)
            day_box.add_widget(Label(text=label, font_size=dp(12), size_hint_x=0.7))
            days_layout.add_widget(day_box)
        
        content.add_widget(days_layout)
        
        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))
        save_btn = Button(text='ذخیره', background_color=get_color_from_hex('#00cec9'))
        cancel_btn = Button(text='انصراف', background_color=get_color_from_hex('#d63031'))
        btn_layout.add_widget(save_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(title='افزودن دارو', content=content, size_hint=(0.8, 0.9))
        
        def on_save(instance):
            selected_days = [d for d, data in days_vars.items() if data['checkbox'].active]
            if not selected_days:
                self.show_popup('خطا', 'حداقل یک روز را انتخاب کنید')
                return
            
            data = {
                "user": self.app.user,
                "patient": patient_input.text,
                "nurse": self.app.fullname,
                "name": name_input.text,
                "time": time_input.text,
                "days": selected_days
            }
            self.app.db.add_med(data)
            if self.app.scheduler:
                self.app.scheduler.reload()
            popup.dismiss()
            self.refresh_table(None)
            self.show_popup('موفق', 'دارو با موفقیت اضافه شد')
        
        def on_cancel(instance):
            popup.dismiss()
        
        save_btn.bind(on_press=on_save)
        cancel_btn.bind(on_press=on_cancel)
        popup.open()
    
    def delete_med(self, instance):
        if not hasattr(self, 'selected_med_id'):
            self.show_popup('خطا', 'لطفاً یک دارو را انتخاب کنید')
            return
        
        def confirm_delete(instance):
            self.app.db.delete_med(self.selected_med_id)
            if self.app.scheduler:
                self.app.scheduler.reload()
            self.refresh_table(None)
            popup.dismiss()
            self.show_popup('موفق', 'دارو با موفقیت حذف شد')
            delattr(self, 'selected_med_id')
        
        def cancel_delete(instance):
            popup.dismiss()
        
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        content.add_widget(Label(text='آیا از حذف این دارو مطمئن هستید؟', font_size=dp(14)))
        
        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))
        ok_btn = Button(text='بله', background_color=get_color_from_hex('#d63031'))
        cancel_btn = Button(text='خیر', background_color=get_color_from_hex('#00cec9'))
        btn_layout.add_widget(ok_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(title='تایید حذف', content=content, size_hint=(0.6, 0.4))
        ok_btn.bind(on_press=confirm_delete)
        cancel_btn.bind(on_press=cancel_delete)
        popup.open()
    
    def show_stats(self, instance):
        if not self.app.user:
            self.show_popup('خطا', 'وارد حساب کاربری خود شوید')
            return
        
        meds = self.app.db.get_user_meds(self.app.user)
        patients = set(m[2] for m in meds)
        total_meds = len(meds)
        total_patients = len(patients)
        
        # محاسبه یادآوری‌های فعال امروز
        active_reminders = 0
        today = datetime.now().strftime("%A").lower()
        for m in meds:
            days = m[6].split(",")
            if today in days:
                active_reminders += 1
        
        stats_text = (
            f'📊 آمار داروها\n\n'
            f'تعداد کل داروها: {total_meds}\n'
            f'تعداد بیماران: {total_patients}\n'
            f'یادآوری فعال امروز: {active_reminders}'
        )
        self.show_popup('آمار', stats_text)
    
    def show_help(self, instance):
        help_text = (
            '📖 راهنمای استفاده\n\n'
            '1️⃣ وارد حساب کاربری خود شوید\n'
            '2️⃣ از طریق دکمه "افزودن دارو" داروی جدید اضافه کنید\n'
            '3️⃣ زمان و روزهای مصرف را مشخص کنید\n'
            '4️⃣ در زمان تعیین شده، یادآوری دریافت خواهید کرد\n'
            '5️⃣ برای حذف دارو، روی دکمه "انتخاب" کلیک کرده و "حذف انتخاب" را بزنید'
        )
        self.show_popup('راهنما', help_text)
    
    def show_about(self, instance):
        about_text = (
            '💊 یادآور هوشمند دارو\n'
            'نسخه 2.0 (Kivy)\n\n'
            'طراحی شده برای مدیریت و یادآوری زمان مصرف دارو\n'
            'با قابلیت ثبت پرستار و بیمار\n\n'
            'ساخته شده با ❤️ در پایتون'
        )
        self.show_popup('درباره ما', about_text)
    
    def toggle_theme(self, instance):
        app = App.get_running_app()
        app.dark_mode = not app.dark_mode
        app.save_settings()
        self.build_ui()
    
    def logout(self, instance):
        def confirm_logout(instance):
            app = App.get_running_app()
            app.user = None
            app.fullname = None
            app.role = None
            if app.scheduler:
                schedule.clear()
            app.root.current = 'login'
            popup.dismiss()
        
        def cancel_logout(instance):
            popup.dismiss()
        
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        content.add_widget(Label(text='از حساب خود خارج می‌شوید؟', font_size=dp(14)))
        
        btn_layout = BoxLayout(orientation='horizontal', spacing=dp(10), size_hint_y=None, height=dp(50))
        ok_btn = Button(text='بله', background_color=get_color_from_hex('#d63031'))
        cancel_btn = Button(text='خیر', background_color=get_color_from_hex('#00cec9'))
        btn_layout.add_widget(ok_btn)
        btn_layout.add_widget(cancel_btn)
        content.add_widget(btn_layout)
        
        popup = Popup(title='خروج', content=content, size_hint=(0.6, 0.4))
        ok_btn.bind(on_press=confirm_logout)
        cancel_btn.bind(on_press=cancel_logout)
        popup.open()
    
    def show_popup(self, title, message):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        content.add_widget(Label(text=message, font_size=dp(14)))
        btn = Button(text='باشه', size_hint_y=None, height=dp(40), background_color=get_color_from_hex('#00cec9'))
        popup = Popup(title=title, content=content, size_hint=(0.6, 0.4))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()


# ================= MAIN APP =================
class MedicineApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = DBManager()
        self.scheduler = None
        self.user = None
        self.fullname = None
        self.role = None
        self.dark_mode = True
        self.load_settings()
    
    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    self.dark_mode = json.load(f).get("dark_mode", True)
            except:
                pass
    
    def save_settings(self):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({"dark_mode": self.dark_mode}, f)
    
    def show_notification(self, text):
        content = BoxLayout(orientation='vertical', spacing=dp(10), padding=dp(20))
        content.add_widget(Label(text='⏰ زمان مصرف دارو فرا رسیده!', font_size=dp(16), bold=True))
        content.add_widget(Label(text=text, font_size=dp(14)))
        btn = Button(text='باشه', size_hint_y=None, height=dp(40), background_color=get_color_from_hex('#00cec9'))
        popup = Popup(title='یادآوری دارو', content=content, size_hint=(0.7, 0.5))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        popup.open()
    
    def build(self):
        sm = ScreenManager()
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(DashboardScreen(name='dashboard'))
        return sm


# ================= RUN =================
if __name__ == '__main__':
    MedicineApp().run()