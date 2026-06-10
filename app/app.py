from flask import Flask, request, render_template, jsonify
from datetime import datetime, timedelta
import random
import os
import json

app = Flask(__name__)

# ---------------- PERSISTENT LOG PATHS ----------------
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "security_events.log")

# ---------------- DATA ----------------
attempts = {}
blocked_ips = {}
blocked_users = {}
logs = []
timeline = []

VALID_USERS = {"admin": "1234", "user": "1234"}

# ---------------- LOG UTILITIES ----------------
def write_log_to_file(log_entry):
    try:
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(log_entry) + "\n")
    except Exception as e:
        app.logger.error(f"Error writing persistent log: {e}")

def add_log(log_entry):
    logs.append(log_entry)
    write_log_to_file(log_entry)

def load_logs_from_file():
    global logs, timeline
    if not os.path.exists(LOG_FILE):
        return
    try:
        with open(LOG_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        log_data = json.loads(line)
                        logs.append(log_data)
                        
                        # Populate timeline from fail events
                        if log_data.get("status") == "FAILED":
                            timeline.append({
                                "time": log_data.get("time"),
                                "count": 1
                            })
                    except Exception:
                        pass
    except Exception as e:
        pass

# Load logs on startup
load_logs_from_file()

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

    add_log({
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
        add_log({
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


# ---------------- RESET API ----------------
@app.route("/reset", methods=["POST"])
def reset_logs():
    global attempts, blocked_ips, blocked_users, logs, timeline
    attempts.clear()
    blocked_ips.clear()
    blocked_users.clear()
    logs.clear()
    timeline.clear()
    
    # Clear persistent logs file
    try:
        with open(LOG_FILE, "w") as f:
            f.write("")
    except Exception as e:
        app.logger.error(f"Error resetting log file: {e}")
        
    return jsonify({"message": "Dashboard logs and history reset successfully"})


# ---------------- ATTACKER UI ----------------
@app.route("/attacker")
def attacker_ui():
    return render_template("attacker.html")

# ---------------- RUN ----------------
if __name__ == "__main__":
    import os
    # Read environment variable to decide debug mode (defaults to False for DevSecOps best practices)
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    # Port configuration from environment
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=debug_mode)  # nosec B201 B104