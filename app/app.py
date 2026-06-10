from flask import Flask, request, render_template, jsonify
from datetime import datetime, timedelta
import random

app = Flask(__name__)

# ---------------- DATA ----------------
attempts = {}
blocked_ips = {}
blocked_users = {}
logs = []
timeline = []

VALID_USERS = {"admin": "1234", "user": "1234"}

# ---------------- CLEAN BLOCK EXPIRE ----------------
def cleanup_blocks():
    now = datetime.now()

    # remove expired IP blocks
    for ip in list(blocked_ips.keys()):
        if now > blocked_ips[ip]:
            del blocked_ips[ip]
            attempts[ip] = []

    # remove expired user blocks
    for user in list(blocked_users.keys()):
        if now > blocked_users[user]:
            del blocked_users[user]

def get_location(ip):
    mapping = {
        "192.168.1.1": {"lat": 20.5937, "lon": 78.9629, "country": "India"},
        "10.0.0.2": {"lat": 37.0902, "lon": -95.7129, "country": "USA"},
        "172.16.0.3": {"lat": 51.1657, "lon": 10.4515, "country": "Germany"}
    }
    return mapping.get(ip, {"lat": 0, "lon": 0, "country": "Unknown"})
# ---------------- ATTACK ENGINE ----------------
def simulate_attack(ip, username):
    now = datetime.now()
    cleanup_blocks()

    attempts.setdefault(ip, []).append(now)

    # keep last 60 sec attempts
    attempts[ip] = [t for t in attempts[ip] if now - t < timedelta(seconds=60)]
    count = len(attempts[ip])
    
    # threat logic
    if count <= 3:
        threat, action = "LOW", "LOG"
    elif count <= 5:
        threat, action = "MEDIUM", "WARN"
    elif count <= 8:
        threat, action = "HIGH", "BLOCK IP"
        blocked_ips[ip] = now + timedelta(seconds=60)
    else:
        threat, action = "CRITICAL", "BLOCK USER"
        blocked_users[username] = now + timedelta(seconds=120)

    attack_type = "Brute Force" if count > 5 else "Normal"

    # log entry
    loc = get_location(ip)

    logs.append({
        "ip": ip,
        "user": username,
        "time": now.strftime("%H:%M:%S"),
        "status": "FAILED",
        "threat": threat,
        "action": action,
        "type": attack_type,
        "lat": loc["lat"],
        "lon": loc["lon"],
        "country": loc["country"]
    })
    # timeline entry
    timeline.append({
        "time": now.strftime("%H:%M:%S"),
        "count": count
    })


# ---------------- ROUTES ----------------

@app.route("/")
def soc():
    return render_template("soc.html")


# ---------------- ATTACK API ----------------
@app.route("/attack", methods=["POST"])
def attack():
    data = request.json or {}

    attack_type = data.get("type", "Brute Force")
    intensity = int(data.get("intensity", 10))

    fake_ips = ["192.168.1.1", "10.0.0.2", "172.16.0.3"]

    for _ in range(intensity):
        ip = random.choice(fake_ips)
        simulate_attack(ip, "hacker")

    return jsonify({
        "message": f"{attack_type} attack launched ({intensity})"
    })

# ---------------- LOGIN ----------------
@app.route("/login", methods=["POST"])
def login():
    ip = request.remote_addr or "127.0.0.1"
    username = request.form.get("username", "")
    password = request.form.get("password", "")
    now = datetime.now()

    cleanup_blocks()

    # check IP block
    if ip in blocked_ips and now < blocked_ips[ip]:
        return "🚫 IP BLOCKED"

    # check user block
    if username in blocked_users and now < blocked_users[username]:
        return "🚫 USER BLOCKED"

    # success login
    if username in VALID_USERS and VALID_USERS[username] == password:
        logs.append({
            "ip": ip,
            "user": username,
            "time": now.strftime("%H:%M:%S"),
            "status": "SUCCESS",
            "threat": "NONE",
            "action": "LOGIN",
            "type": "Normal"
        })
        return "Login success"

    # failed login
    simulate_attack(ip, username)
    return "Login failed"


# ---------------- LOG API ----------------
@app.route("/logs")
def get_logs():
    success = sum(1 for l in logs if l["status"] == "SUCCESS")
    fail = sum(1 for l in logs if l["status"] == "FAILED")

    return jsonify({
        "logs": logs[-30:],
        "timeline": timeline[-20:],
        "blocked_ips": list(blocked_ips.keys()),
        "blocked_users": list(blocked_users.keys()),
        "success": success,
        "fail": fail
    })


# ---------------- ATTACKER UI ----------------
@app.route("/attacker")
def attacker_ui():
    return """
    <html>
    <head>
    <title>Attacker Panel</title>

    <style>
    body {
        background:#111827;
        color:white;
        font-family:Arial;
        padding:30px;
    }

    .card {
        background:#1f2937;
        padding:20px;
        border-radius:10px;
        width:400px;
    }

    select, input {
        width:100%;
        padding:10px;
        margin:10px 0;
        border-radius:5px;
        border:none;
    }

    button {
        width:100%;
        padding:10px;
        margin-top:10px;
        border:none;
        cursor:pointer;
        font-size:16px;
        border-radius:5px;
    }

    .attack-btn {
        background:red;
        color:white;
    }

    .back-btn {
        background:#2563eb;
        color:white;
    }

    </style>
    </head>

    <body>

    <h1>Attacker Control Panel</h1>

    <div class="card">

        <label>Attack Type</label>
        <select id="type">
            <option value="Brute Force">Brute Force</option>
            <option value="Password Spray">Password Spray</option>
            <option value="Credential Stuffing">Credential Stuffing</option>
        </select>

        <label>Number of Attacks</label>
        <input type="number" id="intensity" value="20" min="1" max="200">

        <button class="attack-btn" onclick="launchAttack()">Launch Attack</button>

        <!-- ✅ BACK BUTTON -->
        <button class="back-btn" onclick="goBack()">⬅ Back to Dashboard</button>

        <p id="status"></p>

    </div>

    <script>
    async function launchAttack(){
        const type = document.getElementById("type").value;
        const intensity = document.getElementById("intensity").value;

        try{
            const res = await fetch('/attack',{
                method:'POST',
                headers:{'Content-Type':'application/json'},
                body:JSON.stringify({
                    type:type,
                    intensity:intensity
                })
            });

            const data = await res.json();
            document.getElementById("status").innerText = data.message;

        }catch(err){
            document.getElementById("status").innerText = "Attack failed";
        }
    }

    function goBack(){
        window.location.href = "/";
    }
    </script>

    </body>
    </html>
    """

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)