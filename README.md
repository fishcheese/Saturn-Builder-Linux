## <div align="center"><img width="20" height="20" alt="image" src="https://github.com/user-attachments/assets/cd085b32-5d66-4016-b691-272b6631c8b0" />  Construct 3 Cordova zip to apk builder 
   <div align="center"><img width="200" height="200" alt="" src="https://github.com/user-attachments/assets/b427cf12-2630-4aff-8d52-a465ac1397cf" />
<br>
<br>
      
![GitHub release (latest by date)](https://img.shields.io/github/v/release/EwenLoy/Saturn-Builder) ![GitHub downloads](https://img.shields.io/github/downloads/EwenLoy/Saturn-Builder/total) ![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-blue)
   
<div align="left">
   
## 📖 What is Saturn-Builder? / Что это?
<div align="left"> Saturn-Builder is a friendly app made with Python that helps you build Android apps without complicated setup. It downloads and installs everything you need (like special tools) on its own. Whether you're new to app-making or have some experience, this tool makes it simple to create your own apps for Android!
<br>
<br>
<div align="left"> Saturn-Builder - это удобное приложение, созданное на Python, которое поможет вам создавать приложения для Android без сложной настройки. Оно самостоятельно загружает и устанавливает все, что вам нужно (например, специальные инструменты). Независимо от того, новичок вы в создании приложений или у вас есть некоторый опыт, этот инструмент упрощает создание ваших собственных приложений для Android!
---

## 🌟 What Can It Do? / Возможности

| Feature                  | What It Means                                    |
|--------------------------|--------------------------------------------------|
| 🛠️ **Easy Setup**        | Automatically installs tools you need (~1 GB).   |
| 📱 **Make Apps**          | Creates APK or AAB files for your Android apps.  |
| 📂 **Manage Projects**    | Lets you start new projects or open old ones.    |
| 🌐 **Language Switch**    | Change the app’s language to English or Russian. |
| 📜 **Show Progress**      | Shows you what’s happening while building.       |
| 🖥️ **Simple Interface**   | Easy-to-use screen to control everything.        |

---

## 🛠️ How to Get Started / Как начать

Saturn-Builder works on **Windows 10 or 11**. / Работает на win 10, 11 (windows 7 не пробовал, попробуйте если хотите)

1. Visit the [releases page](https://github.com/EwenLoy/Saturn-Builder/releases/tag/main). / Просто скачайте exe со страницы релизов
2. Download the `Saturn-Builder.exe` file (it’s like a setup program).
3. Double-click the file to install and open the app.

> **Tip**: Make sure you have about 1 GB of free space on your computer for the tools.
> > **Совет**: Убедитесь, что у вас достаточно свободного места на диске (~1 GB).

---

## 👀 How to use / Как пользоваться

1. **First start**: / Первый запуск
   - After installing, click `Saturn-Builder.exe` to start.
   - The first time, it will ask to install some tools. Click **Install Dependencies** to get started, or **Skip for Now** if you want to try it later (but you won’t be able to make apps yet).
   - При первом запуске вам будет предложено установить необходимые зависимости (~1GB), однако если вы откажетесь, приложение не будет работать
   
     <div align="left"><img width="500" height="500" alt="Снимок экрана 2025-08-31 180023" src="https://github.com/user-attachments/assets/c1bd34f4-9203-48d6-8f1c-baeab97fe776" />


2. **Pick a Language after installing dependencies**: / выберите язык интерфейса (если по англ не понимаете)
   - Choose English or Russian from a dropdown menu in the app.
   - The app will change its language right away!

3. **Open the Cordova Project (zip)**: / нажмите кнопку загрузить проект (Load project) ваш zip архив Cordova
   - Click **Load Project** to open one you’ve worked on before.

3.1 **Choose build type** / Выберете тип сборки
- Debug APK
- Unsigned release APK
- Unsigned Android App Bundle
- Signed debug APK
- Signed release APK
- Signed Android App Bundle
4. **Build Your App**: / Сборка вашего приложения
   - If you need a special key for your app, follow the steps to add it / Если подписанная сборка подгрузите или создайте ключи
   - Click **Build** and watch the progress on the screen / Нажмите "Собрать" и ожидайте

5. **Get Your App**: / Получите ваше приложение
   - When it’s done, your app files (APK or AAB) will be in your project folder, and the folder will open so you can see them!
   - Когда сборка закончится, откроется проводник с вашим файлом
## 🚨Possible problems / Возможные проблемы
 **Убедитесь, что у вас НЕ ИСПОЛЬЗУЕТСЯ КИРИЛЛИЦА (РУС БУКВЫ) в проекте! Иначе получите ошибку:**
**Make sure that you DO NOT USE CYRILLIC LETTERS in your project! Otherwise you will get an error:**
>[19:06:24] ❌ Command finished with code 1

>[19:06:24] ❌ Error: Cordova build failed with code 1

>[19:06:24] Traceback (most recent call last):
 
>> File "main.py", line 1902, in _build_thread

>>File "main.py", line 1966, in _build_cordova

>>Exception: Cordova build failed with code 1

## ✅ Solution: rename all files and names to English, including icons
## ✅ Решение: переименуйте все файлы и названия на английский, включая значки

---

## 📸 Pictures / Фото

<img width="1154" height="780" alt="image" src="https://github.com/user-attachments/assets/4c8111c7-e49a-4d87-b07c-9aeff08aab4c" />

## 📸 Construct 3 export options / Тип экспорта для construct 3 (этот полученный файл загружаете в программу, данный тип экспорта работает и в БЕСПЛАТНОЙ версии construct)

<img width="450" height="439" alt="image" src="https://github.com/user-attachments/assets/606dd9fd-bee0-475c-8927-a5fc168c2724" /> <img width="480" height="503" alt="image" src="https://github.com/user-attachments/assets/68605654-142e-45d0-992e-c39dc4a64f53" />





---

## 🛠️ What It Needs / Что использует

Saturn-Builder downloads these tools automatically:
- **Node.js**: Helps run the app-making process.
- **JDK 17**: A tool to prepare your app for Android.
- **Android SDK**: Tools to build Android apps.
- **Gradle**: Helps put everything together.
- **Cordova CLI**: Makes apps from web projects.

❗You’ll need about 1 GB of space for all this❗

---

## 🤝 Help Make It Better / Помогите улучшить сервис

Love Saturn-Builder? Want to add your ideas?
1. Copy the project to your own GitHub (fork it).
2. Make a new version: `git checkout -b feature/your-idea`.
3. Send us your changes: [Create PR](https://github.com/EwenLoy/Saturn-Builder/pulls).

---

## 📬 Contact Us / Связь со мной (или нет)

- **GitHub**: [@EwenLoy](https://github.com/EwenLoy)
- **Email**: ewenloy@gmail.com
- **Facebook**: Soon
- **Discord**: Soon
- **Telegram**: Soon
- **X**: Soon

---

## 💰 Buy Me a Coffee / ☕ Поддержите школьника:)
<div align="left"><img width="246" height="246" alt="qr-code" src="https://github.com/user-attachments/assets/23c8c13a-10dd-4507-b84b-8ea11071c769" />
   
Support Saturn-Builder! Scan the QR code or click below to buy me a coffee:
[<a href="https://www.donationalerts.com/r/ewenloy">Buy Me a Coffee</a>](https://www.donationalerts.com/r/ewenloy)

---
## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=EwenLoy/Saturn-Builder&type=Date)](https://www.star-history.com/#EwenLoy/Saturn-Builder&Date)

## 📜 License

This project uses the MIT License. Check [LICENSE](LICENSE) for more info.
