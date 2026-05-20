# Knight Tamagotchi — Local Edition

Runs entirely on your PC with Flask. No lovable.app needed.

```
knight-local/
├── app.py              ← Flask server (web + API)
├── requirements.txt
├── static/             ← Web frontend (HTML/CSS/JS)
│   ├── index.html      ← tamagotchi view (was /pi)
│   ├── play.html       ← side-scrolling game (was /play)
│   ├── game.js
│   └── style.css
├── state.json          ← created automatically on first run
└── pi/
    ├── main.py         ← Raspberry Pi client
    └── requirements.txt
```

---

## 1. Start the web server on your PC

Open a terminal in this folder and run:

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

**macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```

You'll see:
```
 * Running on http://0.0.0.0:5000
```

Open **http://localhost:5000** in your browser. You should see the tamagotchi screen.
Click **GO OUTSIDE** to play the adventure game.

To stop the server: press `Ctrl+C` in the terminal.

---

## 2. Connect your Raspberry Pi (optional)

On the Pi:

```bash
cd pi
pip3 install -r requirements.txt

# Point the Pi at your PC's local IP (find it with `ipconfig` on Windows
# or `ifconfig` / `ip a` on macOS/Linux). Example: 192.168.1.50
export TAMAGOTCHI_SERVER_URL="http://192.168.1.50:5000"
python3 main.py
```

The Pi pushes stats to your PC every 2 seconds. The browser shows them live.
When you click **GO OUTSIDE** in the browser, the Pi shows "OUTSIDE" until
you click **GO HOME** — collected food is then added to the tamagotchi.

**Buttons (if wired):** GPIO 17 = feed, GPIO 22 = play, GPIO 27 = sleep.
**Keyboard fallback (if running with a monitor):** F = feed, P = play, S = sleep.

---

## 3. Run everything on the same PC (no Pi)

You can also just run `pi/main.py` on your PC — it'll open a small pygame window
that acts as the "device". Default `TAMAGOTCHI_SERVER_URL` is `http://localhost:5000`.

```bash
pip install -r pi/requirements.txt
python pi/main.py
```

---

## 4. Endpoints (for reference)

| Method | Path                          | Use                                  |
|--------|-------------------------------|--------------------------------------|
| GET    | `/api/public/state`           | Full knight state                    |
| GET    | `/api/public/is_outside`      | Is knight outside + pending food     |
| POST   | `/api/public/go_outside`      | Claim knight for adventure           |
| POST   | `/api/public/return`          | Bring knight home with food          |
| POST   | `/api/public/push`            | Pi pushes current stats              |
| POST   | `/api/public/consume_food`    | Convert pending food into -hunger    |

---

## Troubleshooting

- **Port 5000 busy?** Edit the last line of `app.py` and change `port=5000` to `port=5001`.
- **Pi can't reach the server?** Make sure your PC's firewall allows incoming
  connections on port 5000, and that the Pi and PC are on the same Wi-Fi.
  Test from the Pi: `curl http://<your-pc-ip>:5000/api/public/state`.
- **Reset the knight?** Stop the server and delete `state.json`.
