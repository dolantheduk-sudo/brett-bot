# 🎲 Brett Bot

**BRETT THE POSSESSED DIE**
***ROLL TO KNOW YOUR FATE***

Brett Bot is a fun Discord bot that emulates the famous *Brett die* — rolling randomized outcomes with a touch of personality, and keeping track of user stats over time.

![Brett Bot Icon](icon.png) <!-- replace with your actual icon path -->

---

## ✨ Features
- **`!brett`** → Roll the Brett die for a random outcome  
- **`!8brett`** → Ask Brett a yes/no question (like a Magic 8-Ball)  
- **`!stats`** → See how many times you’ve rolled Brett  
- **`!chart`** → View a bar chart of your Brett roll history  
- **`!emojichart`** → Same as chart, but with emojis  
- **`!exportstats`** → Export your personal stats as a JSON file  
- **`!help`** → List all available commands  

All rolls are saved persistently so your stats never reset when the bot restarts (thanks to a JSON file on disk).

---

## 🚀 Getting Started

### 1. Clone the Repo
```bash
git clone https://github.com/YOUR_USERNAME/brett-bot.git
cd brett-bot
```

### 2. Install Dependencies
Make sure you have Python **3.10+** installed.  
Then run:
```bash
pip install -r requirements.txt
```

### 3. Configure Environment
Create a `.env` file in the root folder with your Discord bot token:
```
DISCORD_BOT_TOKEN=your_token_here
STATS_FILE=stats.json
```

### 4. Run Brett Bot
```bash
python bot.py
```

---

## ⚙️ Deployment
Brett Bot is designed to work on [Render](https://render.com), but you can run it anywhere:

- On Render, mount a **Persistent Disk** and set:
  ```
  STATS_FILE=/data/stats.json
  ```
- Add your bot token as a **Secret Environment Variable**.

---

## 🛠️ Development
- Written in **Python 3.10+**
- Uses **discord.py**
- Persistent data is stored in `stats.json` (JSON format)

---

## 📝 Roadmap / Ideas
- Leaderboards (who rolls Brett the most)  
- More Brett “personalities” / outcomes  
- Daily streaks & achievements  
- Fun Easter egg commands  

---

## 🤝 Contributing
PRs welcome! If you have cool new command ideas, feel free to fork and submit.

---

## 📜 License
MIT License — free to use, modify, and share.

---

### 👑 Made with ❤️ for the Brett die
