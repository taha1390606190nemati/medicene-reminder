import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import sqlite3
import threading as trd
import bcrypt
import logging
from datetime import datetime, timedelta
import schedule
import time
from datetime import datetime
from PIL import Image, ImageTk
import os
import random
import json
import sys

try:
    from plyer import notification
    PLYER_AVAILABLE = True
except:
    PLYER_AVAILABLE = False
    
# ---------------- PATHS ----------------
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.dirname(os.path.abspath(__file__))

    return os.path.join(base_path, relative_path)


APP_DIR = os.path.join(
    os.getenv("LOCALAPPDATA"),
    "MedicineReminder"
)

os.makedirs(APP_DIR, exist_ok=True)

DB_PATH = os.path.join(APP_DIR, "medicine_mobile.db")
SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")


# ================= DATABASE =================
class DBManager:
    def __init__(self):
        self.conn = sqlite3.connect(
            DB_PATH,
            check_same_thread=False
)
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
    def __init__(self, db, user, fullname, root):
        self.db = db
        self.user = user
        self.fullname = fullname
        self.root = root
        self.reload()
        trd.Thread(target=self.loop, daemon=True).start()

    def alarm_popup(self, msg):
        def show():
            win = tk.Toplevel(self.root)
            win.title("زمان مصرف دارو فرا رسیده است!!!!")
            win.configure(bg="#1e1e2f")
            ttk.Label(win, text=msg, font=("Arial", 14), background="#1e1e2f", foreground="white").pack(padx=20, pady=20)

        self.root.after(0, show)

    def notify(self, patient, nurse, name):
        text = f"Nurse: {nurse} | Patient: {patient} | Medicine: {name}"

        if PLYER_AVAILABLE:
            try:
                notification.notify(title="Medicine Reminder", message=text, timeout=10)
            except Exception as e:
                print(e)
                self.alarm_popup(text)
        else:
            self.alarm_popup(text)

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
            time.sleep(1)


# ================= MAIN APP =================
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("یادآور هوشمند دارو")
        self.root.geometry("1100x700")
        
        self.db = DBManager()
        self.dark_mode = True
        self.load_settings()
        
        self.user = None
        self.fullname = None
        self.scheduler = None
        
        self.setup_style()
        self.login_screen()

    # ---------- SETTINGS ----------
    def load_settings(self):
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(
                    SETTINGS_FILE,
                    "w",
                    encoding="utf-8"
                ) as f:
                    self.dark_mode = json.load(f).get("dark_mode", True)
            except:
                pass

    def save_settings(self):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({"dark_mode": self.dark_mode}, f)

    # ---------- STYLE ----------
    def setup_style(self):
        if os.path.exists("medicine_icon.ico"):
            self.root.iconbitmap("medicine_icon.ico")

        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.style.configure("TFrame", background="#1e1e2f")
        self.style.configure("TLabel", background="#1e1e2f", foreground="white", font=("Segoe UI", 11))
        self.style.configure("TButton", font=("Segoe UI", 11, "bold"), padding=6)
        self.style.map("TButton", background=[("active", "#00b894")], foreground=[("active", "white")])
        self.style.configure("Green.TButton", background="#00cec9", foreground="black")
        self.style.configure("Red.TButton", background="#d63031", foreground="white")
        self.style.configure("Treeview", background="#2d2d44", foreground="white", fieldbackground="#2d2d44", rowheight=28)
        self.style.map("Treeview", background=[("selected", "#00cec9")])

    def get_colors(self):
        if self.dark_mode:
            return {
                "bg": "#1e1e2f",
                "fg": "white",
                "sidebar": "#151522",
                "entry_bg": "#2d2d44",
                "entry_fg": "white"
            }
        else:
            return {
                "bg": "#f4f4f4",
                "fg": "black",
                "sidebar": "#dddddd",
                "entry_bg": "white",
                "entry_fg": "black"
            }

    def apply_theme(self):
        colors = self.get_colors()
        self.root.configure(bg=colors["bg"])
        # به‌روزرسانی اجزای موجود در صورت وجود

    # ---------- CLEAR ----------
    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    # ---------- LOGIN ----------
    def login_screen(self):
        self.clear()
        colors = self.get_colors()
        self.root.configure(bg=colors["bg"])

        # لوگو
        logo_path = resource_path("medical_logo.png")
        if os.path.exists(logo_path):
            logo_img = Image.open(logo_path)
            logo_img = logo_img.resize((80, 80))
            self.logo = ImageTk.PhotoImage(logo_img)
            lbl_logo = tk.Label(self.root, image=self.logo, bg=colors["bg"])
            lbl_logo.pack(pady=10)

        # عنوان
        tk.Label(
            self.root,
            text="یادآور هوشمند دارو",
            font=("Segoe UI", 20, "bold"),
            bg=colors["bg"],
            fg=colors["fg"]
        ).pack(pady=10)

        # فرم ورود
        frame = tk.Frame(self.root, bg=colors["bg"])
        frame.pack(pady=20)

        tk.Label(frame, text="نام کاربری", bg=colors["bg"], fg=colors["fg"], font=("Segoe UI", 12)).pack(pady=5)
        self.e_user = tk.Entry(frame, font=("Segoe UI", 12), bg=colors["entry_bg"], fg=colors["entry_fg"], width=25)
        self.e_user.pack(pady=5)

        tk.Label(frame, text="رمز عبور", bg=colors["bg"], fg=colors["fg"], font=("Segoe UI", 12)).pack(pady=5)
        self.e_pass = tk.Entry(frame, show="*", font=("Segoe UI", 12), bg=colors["entry_bg"], fg=colors["entry_fg"], width=25)
        self.e_pass.pack(pady=5)

        # کپچا
        self.num1 = random.randint(1, 20)
        self.num2 = random.randint(1, 20)
        tk.Label(frame, text=f"کد امنیتی: {self.num1} + {self.num2} = ؟", 
                 bg=colors["bg"], fg=colors["fg"], font=("Segoe UI", 12)).pack(pady=5)
        self.e_captcha = tk.Entry(frame, font=("Segoe UI", 12), bg=colors["entry_bg"], fg=colors["entry_fg"], width=25)
        self.e_captcha.pack(pady=5)

        # دکمه‌ها
        btn_frame = tk.Frame(frame, bg=colors["bg"])
        btn_frame.pack(pady=15)

        tk.Button(btn_frame, text="ورود", command=self.do_login,
                  bg="#00cec9", fg="black", font=("Segoe UI", 12, "bold"), padx=20, pady=5).pack(side="left", padx=5)
        tk.Button(btn_frame, text="ثبت پرستار", command=lambda: self.register("nurse"),
                  bg="#0984e3", fg="white", font=("Segoe UI", 10), padx=15, pady=5).pack(side="left", padx=5)
        tk.Button(btn_frame, text="ثبت بیمار", command=lambda: self.register("patient"),
                  bg="#00b894", fg="white", font=("Segoe UI", 10), padx=15, pady=5).pack(side="left", padx=5)

    def register(self, role):
        u = self.e_user.get()
        p = self.e_pass.get()
        if not u or not p:
            messagebox.showerror("خطا", "نام کاربری و رمز عبور را وارد کنید")
            return
        fullname = simpledialog.askstring("نام کامل", "نام کامل خود را وارد کنید")
        if not fullname:
            return
        if self.db.register(u, p, role, fullname):
            messagebox.showinfo("OK", "ثبت نام با موفقیت انجام شد")
        else:
            messagebox.showerror("خطا", "این نام کاربری از قبل در سامانه ثبت شده است")

    def do_login(self):
        try:
            if int(self.e_captcha.get()) != self.num1 + self.num2:
                messagebox.showerror("خطا", "کد امنیتی اشتباه است.")
                self.login_screen()
                return
        except:
            messagebox.showerror("خطا", "کد امنیتی را وارد کنید.")
            return

        r = self.db.login(self.e_user.get(), self.e_pass.get())
        if not r:
            messagebox.showerror("خطا", "نام کاربری یا رمز عبور اشتباه است")
            return
        role, fullname = r
        self.user = self.e_user.get()
        self.fullname = fullname
        self.scheduler = Scheduler(self.db, self.user, self.fullname, self.root)
        self.dashboard(role)

    # ---------- DASHBOARD ----------
    def dashboard(self, role):
        self.clear()
        colors = self.get_colors()
        self.root.configure(bg=colors["bg"])

        # فریم اصلی
        main_frame = tk.Frame(self.root, bg=colors["bg"])
        main_frame.pack(fill="both", expand=True)

        # سایدبار راست
        sidebar = tk.Frame(main_frame, width=220, bg=colors["sidebar"])
        sidebar.pack(side="right", fill="y")

        # محتوای اصلی
        content = tk.Frame(main_frame, bg=colors["bg"])
        content.pack(side="left", fill="both", expand=True)

        # عنوان
        title_text = f"{role.upper()} PANEL - {self.fullname}"
        tk.Label(
            content,
            text=title_text,
            font=("Segoe UI", 18, "bold"),
            bg=colors["bg"],
            fg=colors["fg"]
        ).pack(pady=15)

        # جدول
        cols = ("شناسه", "بیمار", "دارو", "ساعت", "روزها")
        self.table = ttk.Treeview(content, columns=cols, show="headings", height=15)
        for c in cols:
            self.table.heading(c, text=c)
            self.table.column(c, width=100)
        self.table.pack(fill="both", expand=True, padx=20, pady=10)
        self.refresh()

        # دکمه‌های سایدبار
        sidebar_buttons = [
            ("💊 افزودن دارو", self.add_med),
            ("📋 لیست داروها", self.show_meds),
            ("📊 آمار", self.show_stats),
            ("❓ راهنما", self.show_help),
            ("ℹ️ درباره ما", self.show_about),
            ("🎨 تغییر تم", self.toggle_theme),
            ("🗑️ حذف انتخاب", self.delete),
            ("🚪 خروج", self.logout),
        ]

        for text, cmd in sidebar_buttons:
            btn = tk.Button(
                sidebar,
                text=text,
                command=cmd,
                bg=colors["sidebar"],
                fg=colors["fg"],
                font=("Segoe UI", 11),
                relief="flat",
                anchor="w",
                padx=15,
                pady=8
            )
            btn.pack(fill="x", padx=10, pady=3)

    def refresh(self):
        for i in self.table.get_children():
            self.table.delete(i)
        if self.user:
            for m in self.db.get_user_meds(self.user):
                days_persian = {
                    "monday": "دوشنبه", "tuesday": "سه‌شنبه", "wednesday": "چهارشنبه",
                    "thursday": "پنج‌شنبه", "friday": "جمعه", "saturday": "شنبه", "sunday": "یکشنبه"
                }
                days_list = [days_persian.get(d.strip(), d.strip()) for d in m[6].split(",")]
                days_str = "،".join(days_list)
                self.table.insert("", tk.END, values=(m[0], m[2], m[4], m[5], days_str))

    # ---------- SIDEBAR COMMANDS ----------
    def add_med(self):
        if not self.user:
            messagebox.showerror("خطا", "وارد حساب کاربری خود شوید")
            return

        win = tk.Toplevel(self.root)
        win.title("اضافه کردن دارو")
        win.configure(bg="#1e1e2f")
        win.geometry("400x500")

        colors = self.get_colors()
        win.configure(bg=colors["bg"])

        tk.Label(win, text="نام بیمار", bg=colors["bg"], fg=colors["fg"], font=("Segoe UI", 12)).pack(pady=5)
        e_patient = tk.Entry(win, font=("Segoe UI", 12), bg=colors["entry_bg"], fg=colors["entry_fg"])
        e_patient.pack(pady=5)

        tk.Label(win, text="نام دارو", bg=colors["bg"], fg=colors["fg"], font=("Segoe UI", 12)).pack(pady=5)
        e_name = tk.Entry(win, font=("Segoe UI", 12), bg=colors["entry_bg"], fg=colors["entry_fg"])
        e_name.pack(pady=5)

        tk.Label(win, text="زمان (HH:MM)", bg=colors["bg"], fg=colors["fg"], font=("Segoe UI", 12)).pack(pady=5)
        e_time = tk.Entry(win, font=("Segoe UI", 12), bg=colors["entry_bg"], fg=colors["entry_fg"])
        e_time.pack(pady=5)

        days_frame = tk.Frame(win, bg=colors["bg"])
        days_frame.pack(pady=10)

        days_persian = {
            "monday": "دوشنبه", "tuesday": "سه‌شنبه", "wednesday": "چهارشنبه",
            "thursday": "پنج‌شنبه", "friday": "جمعه", "saturday": "شنبه", "sunday": "یکشنبه"
        }
        days_vars = {}
        for d, label in days_persian.items():
            var = tk.BooleanVar()
            days_vars[d] = var
            tk.Checkbutton(days_frame, text=label, variable=var,
                           bg=colors["bg"], fg=colors["fg"],
                           selectcolor=colors["entry_bg"], font=("Segoe UI", 10)).pack(anchor="w")

        def save():
            data = {
                "user": self.user,
                "patient": e_patient.get(),
                "nurse": self.fullname,
                "name": e_name.get(),
                "time": e_time.get(),
                "days": [d for d, v in days_vars.items() if v.get()]
            }
            if not data["days"]:
                messagebox.showerror("خطا", "حداقل یک روز را انتخاب کنید")
                return
            self.db.add_med(data)
            if self.scheduler:
                self.scheduler.reload()
            win.destroy()
            self.refresh()
            messagebox.showinfo("موفق", "دارو با موفقیت اضافه شد")

        tk.Button(win, text="ذخیره", command=save,
                  bg="#00cec9", fg="black", font=("Segoe UI", 12, "bold"), padx=20, pady=5).pack(pady=15)

    def show_meds(self):
        self.refresh()
        messagebox.showinfo("لیست داروها", "داروها در جدول نمایش داده می‌شوند.")

    def show_stats(self):
        if not self.user:
            messagebox.showerror("خطا", "وارد حساب کاربری خود شوید")
            return
        meds = self.db.get_user_meds(self.user)
        patients = set(m[2] for m in meds)
        total_meds = len(meds)
        total_patients = len(patients)

        # محاسبه یادآوری‌های فعال
        active_reminders = 0
        for m in meds:
            days = m[6].split(",")
            # بررسی روز جاری
            today = datetime.now().strftime("%A").lower()
            if today in days:
                active_reminders += 1

        messagebox.showinfo(
            "آمار",
            f"تعداد کل داروها: {total_meds}\n"
            f"تعداد بیماران: {total_patients}\n"
            f"یادآوری فعال امروز: {active_reminders}"
        )

    def show_help(self):
        messagebox.showinfo(
            "راهنمای استفاده",
            "1️⃣ وارد حساب کاربری خود شوید\n"
            "2️⃣ از طریق دکمه 'افزودن دارو' داروی جدید اضافه کنید\n"
            "3️⃣ زمان و روزهای مصرف را مشخص کنید\n"
            "4️⃣ در زمان تعیین شده، یادآوری دریافت خواهید کرد\n"
            "5️⃣ برای حذف دارو، روی آن در جدول کلیک کرده و 'حذف انتخاب' را بزنید"
        )

    def show_about(self):
        messagebox.showinfo(
            "درباره ما",
            "💊 یادآور هوشمند دارو\n"
            "نسخه 2.0 (ادغام شده)\n\n"
            "طراحی شده برای مدیریت و یادآوری زمان مصرف دارو\n"
            "با قابلیت ثبت پرستار و بیمار"
        )

    def delete(self):
        sel = self.table.selection()
        if not sel:
            messagebox.showerror("خطا", "لطفاً یک دارو را انتخاب کنید")
            return
        if messagebox.askyesno("حذف", "آیا از حذف این دارو مطمئن هستید؟"):
            id = int(self.table.item(sel[0])["values"][0])
            self.db.delete_med(id)
            if self.scheduler:
                self.scheduler.reload()
            self.refresh()
            messagebox.showinfo("موفق", "دارو با موفقیت حذف شد")

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.save_settings()
        if self.user:
            # بازسازی صفحه با تم جدید
            self.dashboard("user")
        else:
            self.login_screen()

    def logout(self):
        if messagebox.askyesno("خروج", "از حساب خود خارج می‌شوید؟"):
            self.user = None
            self.fullname = None
            if self.scheduler:
                schedule.clear()
            self.login_screen()


# ================= RUN =================
if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()

