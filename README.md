# medicene-reminder

# 💊 Medicine Reminder System

A comprehensive **Medicine Reminder and Patient Management System** developed in **Python** to help patients, caregivers, and healthcare providers manage medication schedules efficiently. The project includes a desktop application built with **Tkinter** and a mobile version developed using **Kivy**, with a scalable architecture prepared for future enterprise deployment.

---

## 📖 Overview

Medication adherence is one of the major challenges in healthcare. Missing or delaying medication can lead to serious health complications, especially for elderly patients and individuals taking multiple medications.

This project was designed to provide a simple, secure, and extensible solution for medication management through automatic reminders, patient management, secure authentication, and a user-friendly interface.

---

# ✨ Features

- 🔐 Secure user authentication using **bcrypt password hashing**
- 💊 Add, delete, and manage medications
- ⏰ Automatic medication scheduling
- 🔔 Desktop notifications
- 🔊 Alarm sound reminders
- 🌙 Dark Mode / ☀️ Light Mode
- 👤 Multi-user support
- 📱 Mobile application built with Kivy
- 💾 SQLite database
- ⚙️ JSON-based application settings
- 🧩 Modular Object-Oriented Architecture

---

# 🏗️ Software Architecture

The project follows **Object-Oriented Programming (OOP)** principles to improve:

- Maintainability
- Scalability
- Readability
- Reusability

Main modules include:

- **DBManager** → Database operations
- **Scheduler** → Medication scheduling
- **Authentication** → User login & registration
- **Notification Service** → Reminder notifications
- **GUI Layer** → User Interface

---

# 🗄️ Database

The application uses **SQLite** as its embedded relational database.

Main tables:

- Users
- Medicines

Relationship:

```
One User
      │
      ├── Medicine 1
      ├── Medicine 2
      └── Medicine N
```

---

# 🔒 Security

Security has been considered from the beginning of the project.

- Passwords are never stored as plain text.
- All passwords are hashed using **bcrypt**.
- User authentication is performed securely before accessing the application.

---

# 🛠️ Technologies Used

- Python
- Tkinter
- SQLite3
- bcrypt
- threading
- schedule
- plyer
- pygame
- Pillow
- JSON
- Kivy

---

# 🎯 Objectives

- Improve medication adherence
- Reduce missed medication doses
- Increase patient safety
- Simplify medication management
- Provide a scalable healthcare solution

---

# 📂 Project Structure

````
```text
Medicine-Reminder/
│
├── 📁 main_program/
│   ├── main.py                    # Desktop application source code
│   ├── medicine_mobile.db         # SQLite database
│   ├── settings.json              # Application settings
│   ├── requirements.txt           # Python dependencies
│   ├── Medicine Reminder.spec     # PyInstaller configuration
│   ├── medicine-reminder.png.ico
│   └── medicine_icon.ico
│
├── 📁 mobile_app/
│   ├── main_mobile.py             # Mobile application (Kivy)
│   ├── medicine.kv                # Kivy UI layout
│   ├── medicine_mobile.db         # SQLite database
│   ├── settings.json              # Mobile app settings
│   └── requirements.txt           # Mobile dependencies
│
├── 📁 intriuducing movie/
│   └── 2026-06-26 17-23-07.mkv    # Project introduction video
│
├── informations.pdf               # Project documentation
├── programming.pdf                # Technical documentation
├── medicine-reminder.ico          # Project icon
├── plans.md                       # Future development roadmap
├── TODO.md                        # Planned improvements
├── .gitignore                     # Git ignored files
└── README.md                      # Project documentation
````

---

# 📸 Screenshots

> Add screenshots of the Login page, Dashboard, Medicine Management, Reminder Notification, and Mobile Application here.

---

# 📄 License

This project was developed for the **Khwarizmi Youth Festival** and is intended for educational and research purposes.

---

# 👨‍💻 Developers

**Taha Nemati**

Python Developer | Software Engineering Enthusiast | Embedded Systems Engineer | IoT Developer

**Aliakbar asadi**

Python and web developer

---

## ⭐ Project Highlights

- Object-Oriented Design
- Secure Authentication
- SQLite Relational Database
- Background Thread Scheduling
- Cross-Platform Development
- Modular Architecture
- Healthcare-Oriented Solution
- Ready for Future Enterprise Expansion
