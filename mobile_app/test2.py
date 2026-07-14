import kivy
kivy.require("2.3.1")

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
from kivy.core.text import LabelBase

import sqlite3
import threading as trd
import bcrypt
from datetime import datetime
import schedule
import time
import random
import json
import os

import arabic_reshaper
from bidi.algorithm import get_display

Window.size = (1100,700)

DB_PATH="medicine_mobile.db"
SETTINGS_FILE="settings.json"



# ---------------- FONT ----------------

FONT="Roboto"

LabelBase.register(
    name=FONT,
    fn_regular="C:/Windows/Fonts/tahoma.ttf"
)


# ---------------- RTL ----------------

def fa(text):
    if text is None:
        return ""

    text=str(text)

    reshaped=arabic_reshaper.reshape(text)

    return get_display(reshaped)


# ---------------- LABEL ----------------

class FLabel(Label):

    def __init__(self,**kwargs):

        if "text" in kwargs:
            kwargs["text"]=fa(kwargs["text"])

        kwargs.setdefault("font_name",FONT)

        super().__init__(**kwargs)


# ---------------- BUTTON ----------------

class FButton(Button):

    def __init__(self,**kwargs):

        if "text" in kwargs:
            kwargs["text"]=fa(kwargs["text"])

        kwargs.setdefault("font_name",FONT)

        super().__init__(**kwargs)


# ---------------- TEXTINPUT ----------------

class FTextInput(TextInput):

    def __init__(self,**kwargs):

        kwargs.setdefault("font_name",FONT)

        super().__init__(**kwargs)


# ---------------- ColoredLabel ----------------

class ColoredLabel(FLabel):

    def __init__(self,**kwargs):

        super().__init__(**kwargs)

        self.color=get_color_from_hex("#333333")

        self.font_size=dp(14)


# ---------------- ColoredButton ----------------

class ColoredButton(FButton):

    def __init__(self,**kwargs):

        super().__init__(**kwargs)

        self.background_color=get_color_from_hex("#00cec9")

        self.color=get_color_from_hex("#000000")

        self.font_size=dp(14)

        self.size_hint_y=None

        self.height=dp(44)
        
# ================= LOGIN SCREEN =================
class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.db = App.get_running_app().db
        self.build_ui()
        self.generate_captcha()

    def build_ui(self):
        layout = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(30)
        )

        title = FLabel(
            text="یادآور هوشمند دارو",
            font_size=dp(28),
            bold=True,
            color=get_color_from_hex("#1a237e")
        )
        layout.add_widget(title)

        form = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(350)
        )

        form.add_widget(
            FLabel(
                text="نام کاربری:",
                size_hint_y=None,
                height=dp(30)
            )
        )

        self.username_input = FTextInput(
            multiline=False,
            size_hint_y=None,
            height=dp(40)
        )
        form.add_widget(self.username_input)

        form.add_widget(
            FLabel(
                text="رمز عبور:",
                size_hint_y=None,
                height=dp(30)
            )
        )

        self.password_input = FTextInput(
            multiline=False,
            password=True,
            size_hint_y=None,
            height=dp(40)
        )

        form.add_widget(self.password_input)

        captcha_layout = BoxLayout(
            orientation="vertical",
            spacing=dp(5),
            size_hint_y=None,
            height=dp(100)
        )

        self.captcha_label = FLabel(
            text="",
            size_hint_y=None,
            height=dp(30),
            font_size=dp(16)
        )

        captcha_layout.add_widget(self.captcha_label)

        row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(40)
        )

        self.captcha_input = FTextInput(
            multiline=False,
            size_hint_x=.7
        )

        refresh_btn = FButton(
            text="🔄",
            size_hint_x=.3,
            background_color=get_color_from_hex("#4fc3f7")
        )

        refresh_btn.bind(
            on_press=lambda x: self.generate_captcha()
        )

        row.add_widget(self.captcha_input)
        row.add_widget(refresh_btn)

        captcha_layout.add_widget(row)

        form.add_widget(captcha_layout)

        layout.add_widget(form)

        btns = BoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(50)
        )

        login_btn = ColoredButton(text="ورود")
        login_btn.bind(on_press=self.do_login)

        nurse_btn = FButton(
            text="ثبت پرستار",
            background_color=get_color_from_hex("#0984e3"),
            color=(1,1,1,1)
        )
        nurse_btn.bind(
            on_press=lambda x:self.register("nurse")
        )

        patient_btn = FButton(
            text="ثبت بیمار",
            background_color=get_color_from_hex("#00b894"),
            color=(1,1,1,1)
        )
        patient_btn.bind(
            on_press=lambda x:self.register("patient")
        )

        btns.add_widget(login_btn)
        btns.add_widget(nurse_btn)
        btns.add_widget(patient_btn)

        layout.add_widget(btns)

        layout.add_widget(Widget())

        self.add_widget(layout)

    def generate_captcha(self):
        self.num1 = random.randint(1,20)
        self.num2 = random.randint(1,20)

        self.captcha_label.text = fa(
            f"کد امنیتی : {self.num1} + {self.num2} = ؟"
        )

    def register(self, role):
        username = self.username_input.text.strip()
        password = self.password_input.text.strip()

        if not username or not password:
            self.show_popup(
                "خطا",
                "نام کاربری و رمز عبور را وارد کنید."
            )
            return

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(20)
        )

        content.add_widget(
            FLabel(text="نام کامل خود را وارد کنید:")
        )

        fullname_input = FTextInput(
            multiline=False,
            size_hint_y=None,
            height=dp(40)
        )

        content.add_widget(fullname_input)

        row = BoxLayout(
            orientation="horizontal",
            spacing=dp(10),
            size_hint_y=None,
            height=dp(45)
        )

        ok = FButton(
            text="تایید",
            background_color=get_color_from_hex("#00cec9")
        )

        cancel = FButton(
            text="انصراف",
            background_color=get_color_from_hex("#d63031")
        )

        row.add_widget(ok)
        row.add_widget(cancel)

        content.add_widget(row)

        popup = Popup(
            title=fa("ثبت نام"),
            content=content,
            size_hint=(.8,.5)
        )

        def save(instance):

            fullname = fullname_input.text.strip()

            if fullname == "":
                self.show_popup("خطا","نام کامل را وارد کنید.")
                return

            if self.db.register(
                username,
                password,
                role,
                fullname
            ):

                popup.dismiss()

                self.show_popup(
                    "موفق",
                    "ثبت نام انجام شد."
                )

            else:

                self.show_popup(
                    "خطا",
                    "این نام کاربری قبلاً ثبت شده است."
                )

        ok.bind(on_press=save)
        cancel.bind(on_press=lambda x: popup.dismiss())

        popup.open()

    def do_login(self, instance):

        try:

            if int(self.captcha_input.text)!=self.num1+self.num2:

                self.show_popup(
                    "خطا",
                    "کد امنیتی اشتباه است."
                )

                self.generate_captcha()

                self.captcha_input.text=""

                return

        except:

            self.show_popup(
                "خطا",
                "کد امنیتی را وارد کنید."
            )

            return

        result=self.db.login(
            self.username_input.text,
            self.password_input.text
        )

        if result is None:

            self.show_popup(
                "خطا",
                "نام کاربری یا رمز عبور اشتباه است."
            )

            return

        role,fullname=result

        app=App.get_running_app()

        app.user=self.username_input.text
        app.fullname=fullname
        app.role=role

        app.scheduler=Scheduler(
            app.db,
            app.user,
            fullname,
            app
        )

        app.root.current="dashboard"

    def show_popup(self,title,message):

        content=BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(20)
        )

        content.add_widget(
            FLabel(text=message)
        )

        btn=FButton(
            text="باشه",
            size_hint_y=None,
            height=dp(40),
            background_color=get_color_from_hex("#00cec9")
        )

        popup=Popup(
            title=fa(title),
            content=content,
            size_hint=(.6,.4)
        )

        btn.bind(on_press=popup.dismiss)

        content.add_widget(btn)

        popup.open()
        

# ================= DASHBOARD SCREEN =================
class DashboardScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app = App.get_running_app()
        self.selected_med_id = None
        self.build_ui()

    def build_ui(self):
        self.clear_widgets()

        main_layout = BoxLayout(orientation="horizontal")

        # ---------- Sidebar ----------
        sidebar = BoxLayout(
            orientation="vertical",
            size_hint_x=0.22,
            spacing=dp(8),
            padding=dp(10)
        )

        buttons = [
            ("💊 افزودن دارو", self.show_add_med),
            ("📋 لیست داروها", self.refresh_table),
            ("📊 آمار", self.show_stats),
            ("❓ راهنما", self.show_help),
            ("ℹ️ درباره ما", self.show_about),
            ("🎨 تغییر تم", self.toggle_theme),
            ("🗑 حذف انتخاب", self.delete_med),
            ("🚪 خروج", self.logout)
        ]

        for text, func in buttons:
            btn = ColoredButton(
                text=text,
                size_hint_y=None,
                height=dp(45)
            )
            btn.bind(on_press=func)
            sidebar.add_widget(btn)

        sidebar.add_widget(Widget())

        # ---------- Main Content ----------

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(15)
        )

        role = self.app.role if self.app.role else ""
        fullname = self.app.fullname if self.app.fullname else ""

        title = FLabel(
            text=f"پنل {role} | {fullname}",
            font_size=dp(24),
            bold=True,
            color=get_color_from_hex("#1565C0"),
            size_hint_y=None,
            height=dp(50)
        )

        content.add_widget(title)

        self.table = ScrollView()

        self.table_layout = GridLayout(
            cols=6,
            spacing=dp(2),
            size_hint_y=None
        )

        self.table_layout.bind(
            minimum_height=self.table_layout.setter("height")
        )

        headers = [
            "شناسه",
            "بیمار",
            "دارو",
            "ساعت",
            "روزها",
            "انتخاب"
        ]

        for h in headers:
            self.table_layout.add_widget(
                FLabel(
                    text=h,
                    bold=True,
                    font_size=dp(13),
                    color=get_color_from_hex("#0D47A1"),
                    size_hint_y=None,
                    height=dp(35)
                )
            )

        self.table.add_widget(self.table_layout)

        content.add_widget(self.table)

        main_layout.add_widget(content)
        main_layout.add_widget(sidebar)

        self.add_widget(main_layout)

        Clock.schedule_once(
            lambda dt: self.refresh_table(),
            0.2
        )

    # =====================================================

    def refresh_table(self, *args):

        while len(self.table_layout.children) > 6:
            self.table_layout.remove_widget(
                self.table_layout.children[0]
            )

        meds = self.app.db.get_user_meds(self.app.user)

        days_map = {
            "monday": "دوشنبه",
            "tuesday": "سه شنبه",
            "wednesday": "چهارشنبه",
            "thursday": "پنج شنبه",
            "friday": "جمعه",
            "saturday": "شنبه",
            "sunday": "یکشنبه"
        }

        for med in meds:

            days = " ، ".join(
                days_map.get(x.strip(), x)
                for x in med[6].split(",")
            )

            values = [
                med[0],
                med[2],
                med[4],
                med[5],
                days
            ]

            for value in values:

                self.table_layout.add_widget(
                    FLabel(
                        text=str(value),
                        size_hint_y=None,
                        height=dp(35)
                    )
                )

            btn = ColoredButton(
                text="انتخاب",
                size_hint_y=None,
                height=dp(35)
            )

            btn.med_id = med[0]

            btn.bind(on_press=self.select_med)

            self.table_layout.add_widget(btn)

    def select_med(self, instance):
        self.selected_med_id = instance.med_id

        self.show_popup(
            "انتخاب",
            f"داروی شماره {instance.med_id} انتخاب شد."
        )
        
        
    def show_add_med(self, instance):
        
        if not self.app.user:
            self.show_popup(
                "خطا",
                "ابتدا وارد حساب کاربری شوید."
            )
            return

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            padding=dp(20)
        )

    # ---------- Patient ----------

        content.add_widget(
            FLabel(text="نام بیمار")
        )

        patient_input = FTextInput(
            multiline=False,
            size_hint_y=None,
            height=dp(40)
        )

        content.add_widget(patient_input)

        # ---------- Medicine ----------

        content.add_widget(
            FLabel(text="نام دارو")
        )

        name_input = FTextInput(
            multiline=False,
            size_hint_y=None,
            height=dp(40)
        )

        content.add_widget(name_input)

        # ---------- Time ----------

        content.add_widget(
            FLabel(text="زمان مصرف (HH:MM)")
        )

        time_input = FTextInput(
            multiline=False,
            hint_text="08:30",
            size_hint_y=None,
            height=dp(40)
        )

        content.add_widget(time_input)

        # ---------- Days ----------

        content.add_widget(
            FLabel(text="روزهای مصرف")
        )

        days_grid = GridLayout(
            cols=2,
            spacing=dp(5),
            size_hint_y=None
        )

        days_grid.bind(
            minimum_height=days_grid.setter("height")
        )

        week = {
            "monday":"دوشنبه",
            "tuesday":"سه شنبه",
            "wednesday":"چهارشنبه",
            "thursday":"پنج شنبه",
            "friday":"جمعه",
            "saturday":"شنبه",
            "sunday":"یکشنبه"
        }

        day_checks = {}

        for key,value in week.items():

            row = BoxLayout(
                size_hint_y=None,
                height=dp(35)
            )

            cb = CheckBox()

            day_checks[key]=cb

            row.add_widget(cb)

            row.add_widget(
                FLabel(
                    text=value
                )
            )

            days_grid.add_widget(row)

        content.add_widget(days_grid)

        # ---------- Buttons ----------

        buttons = BoxLayout(
            spacing=dp(10),
            size_hint_y=None,
            height=dp(45)
        )

        save_btn = ColoredButton(
            text="ذخیره"
        )

        cancel_btn = FButton(
            text="انصراف",
            background_color=get_color_from_hex("#d63031"),
            color=(1,1,1,1)
        )

        buttons.add_widget(save_btn)
        buttons.add_widget(cancel_btn)

        content.add_widget(buttons)

        popup = Popup(
            title=fa("افزودن دارو"),
            content=content,
            size_hint=(0.85,0.9)
        )

    # ---------------- Save ----------------

    def save(instance):

        selected = [
            d for d,c in day_checks.items()
            if c.active
        ]

        if len(selected)==0:

            self.show_popup(
                "خطا",
                "حداقل یک روز را انتخاب کنید."
            )

            return

        self.app.db.add_med({

            "user":self.app.user,

            "patient":patient_input.text,

            "nurse":self.app.fullname,

            "name":name_input.text,

            "time":time_input.text,

            "days":selected

        })

        if self.app.scheduler:

            self.app.scheduler.reload()

        popup.dismiss()

        self.refresh_table()

        self.show_popup(
            "موفق",
            "دارو با موفقیت ثبت شد."
        )

    save_btn.bind(on_press=save)

    cancel_btn.bind(
        on_press=lambda x:popup.dismiss()
    )

    popup.open()
    
    def delete_med(self, instance):
    
        if self.selected_med_id is None:

            self.show_popup(
                "خطا",
                "ابتدا یک دارو را انتخاب کنید."
            )

        return

    content = BoxLayout(
        orientation="vertical",
        spacing=dp(15),
        padding=dp(20)
    )

    content.add_widget(
        FLabel(
            text="آیا از حذف این دارو مطمئن هستید؟",
            font_size=dp(16)
        )
    )

    btns = BoxLayout(
        spacing=dp(10),
        size_hint_y=None,
        height=dp(45)
    )

    yes_btn = FButton(
        text="بله",
        background_color=get_color_from_hex("#d63031"),
        color=(1,1,1,1)
    )

    no_btn = ColoredButton(
        text="خیر"
    )

    btns.add_widget(yes_btn)
    btns.add_widget(no_btn)

    content.add_widget(btns)

    popup = Popup(
        title=fa("حذف دارو"),
        content=content,
        size_hint=(0.6,0.35)
    )

    def yes(instance):

        self.app.db.delete_med(
            self.selected_med_id
        )

        if self.app.scheduler:

            self.app.scheduler.reload()

        popup.dismiss()

        self.selected_med_id = None

        self.refresh_table()

        self.show_popup(
            "موفق",
            "دارو با موفقیت حذف شد."
        )

    yes_btn.bind(on_press=yes)

    no_btn.bind(
        on_press=lambda x:popup.dismiss()
    )

    popup.open()
    
    def show_stats(self, instance):
    
        meds = self.app.db.get_user_meds(
            self.app.user
        )

    patients = len(set(m[2] for m in meds))

    today = datetime.now().strftime("%A").lower()

    today_count = 0

    for med in meds:

        if today in med[6].split(","):

            today_count += 1

    text = f"""

        📊 آمار برنامه

        تعداد داروها : {len(meds)}

        تعداد بیماران : {patients}

        یادآوری امروز : {today_count}

        """

    self.show_popup(
        "آمار",
        text
    )
    
    def show_help(self, instance):
    
        text = """

            📖 راهنمای استفاده

            ۱- ابتدا وارد حساب کاربری شوید.

            ۲- از منوی سمت راست روی
            «افزودن دارو» کلیک کنید.

            ۳- نام بیمار، دارو، ساعت و
            روزهای مصرف را وارد کنید.

            ۴- در ساعت مشخص شده
            برنامه به شما یادآوری می‌کند.

            ۵- برای حذف دارو،
            ابتدا روی «انتخاب» کلیک کنید
            و سپس «حذف انتخاب» را بزنید.

    """

    self.show_popup(
        "راهنما",
        text
    )
    
    def show_about(self, instance):
    
        text = """

            💊 Medicine Reminder

            نسخه 3.0

            طراحی شده با Python و Kivy

            ویژه جشنواره جوان خوارزمی

            طراحی و توسعه:
            طاها نعمتی
            علی اکبر اسدی
    """

    self.show_popup(
        "درباره برنامه",
        text
    )
    
    def toggle_theme(self, instance):
    
        self.app.dark_mode = not self.app.dark_mode

        self.app.save_settings()

        self.clear_widgets()

        self.build_ui()
    
    def logout(self, instance):
    
        content = BoxLayout(
            orientation="vertical",
            spacing=dp(15),
            padding=dp(20)
        )

        content.add_widget(
            FLabel(
                text="آیا از حساب کاربری خارج می‌شوید؟"
            )
        )

        btns = BoxLayout(
            spacing=dp(10),
            size_hint_y=None,
            height=dp(45)
        )

        yes = FButton(
            text="بله",
            background_color=get_color_from_hex("#d63031"),
            color=(1,1,1,1)
        )

        no = ColoredButton(
            text="خیر"
        )

        btns.add_widget(yes)
        btns.add_widget(no)

        content.add_widget(btns)

        popup = Popup(
            title=fa("خروج"),
            content=content,
            size_hint=(0.6,0.35)
        )

    def do_logout(instance):

        if self.app.scheduler:
            schedule.clear()

        self.app.user = None
        self.app.fullname = None
        self.app.role = None

        popup.dismiss()

        App.get_running_app().root.current = "login"

    yes.bind(on_press=do_logout)

    no.bind(
        on_press=lambda x: popup.dismiss()
    )

    popup.open()
    
    def show_popup(self, title, message):
    
        content = BoxLayout(
            orientation="vertical",
            spacing=dp(15),
            padding=dp(20)
        )

        content.add_widget(
            FLabel(
                text=message
            )
        )

        btn = ColoredButton(
            text="باشه"
        )

        popup = Popup(
            title=fa(title),
            content=content,
            size_hint=(0.6,0.4)
        )

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

    # ---------------- SETTINGS ----------------

    def load_settings(self):

        if os.path.exists(SETTINGS_FILE):

            try:

                with open(
                    SETTINGS_FILE,
                    "r",
                    encoding="utf-8"
                ) as f:

                    data = json.load(f)

                    self.dark_mode = data.get(
                        "dark_mode",
                        True
                    )

            except Exception:

                self.dark_mode = True

    def save_settings(self):

        try:

            with open(
                SETTINGS_FILE,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    {
                        "dark_mode": self.dark_mode
                    },
                    f,
                    ensure_ascii=False,
                    indent=4
                )

        except Exception as e:

            print(e)

    # ---------------- Notification ----------------

    def show_notification(self, text):

        content = BoxLayout(
            orientation="vertical",
            spacing=dp(15),
            padding=dp(20)
        )

        title = FLabel(
            text="⏰ زمان مصرف دارو فرا رسیده است.",
            bold=True,
            font_size=dp(18),
            color=get_color_from_hex("#d63031")
        )

        content.add_widget(title)

        content.add_widget(
            FLabel(
                text=text,
                font_size=dp(15)
            )
        )

        btn = ColoredButton(
            text="باشه"
        )

        popup = Popup(
            title=fa("یادآوری دارو"),
            content=content,
            size_hint=(0.7,0.45),
            auto_dismiss=False
        )

        btn.bind(on_press=popup.dismiss)

        content.add_widget(btn)

        popup.open()

    # ---------------- BUILD ----------------

    def build(self):

        self.title = "Medicine Reminder"

        sm = ScreenManager()

        sm.add_widget(
            LoginScreen(
                name="login"
            )
        )

        sm.add_widget(
            DashboardScreen(
                name="dashboard"
            )
        )

        return sm


# ================= RUN =================

if __name__ == "__main__":

    MedicineApp().run()