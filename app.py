from flask import Flask, render_template, request  # 匯入 flask 相關套件
from flask_socketio import SocketIO, emit  # 匯入 flask SocketIO 相關套件

app = Flask(__name__)

# 初始化 SocketIO ，允許跨域連線，並指定使用 eventlet 非同步模式
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="eventlet")

# 紀錄線上使用者 { sid: {"username": str} }
clients = {}

# ===== 📢 SocketIO 事件處理區 =====
# 計算目前線上已設定使用者名稱的數量，並廣播更新給所有人
def broadcast_user_count():
    emit("user_count", 
        {"count": len([c for c in clients.values() if c.get("username")])}, 
        broadcast=True)

# 🔗 用戶連線時觸發
@socketio.on("connect")
def on_connect():
    clients[request.sid] = {"username": None}
    print("Client connect:", request.sid)

# ❌ 用戶離線時觸發
@socketio.on("disconnect")
def on_disconnect():
    info = clients.pop(request.sid, None)
    if info and info.get("username"):
        emit("user_left", {
            "username": info["username"]
        }, broadcast=True)
        broadcast_user_count()
    print("Client disconnect:", request.sid)

# 👤 設定使用者名稱
@socketio.on("set_username")
def handle_set_username(data):
    if request.sid in clients:
        clients[request.sid]["username"] = data.get("username", "")
        broadcast_user_count()

# 🚪 使用者剛進入聊天室時觸發，接收 join 事件並廣播
@socketio.on("join")
def on_join(data):
    username = data.get("username", "匿名")
    if request.sid in clients:
        clients[request.sid]["username"] = username
    else:
        clients[request.sid] = {"username": username}
        
    emit("user_joined", {
        "username": username
    }, broadcast=True)
    
    broadcast_user_count()
    print(username, "joined")

# 💬 5-3-5 傳送與接收訊息：當使用者傳送訊息時觸發
@socketio.on("send_message")
def on_message(data):
    emit("chat_message", data, broadcast=True, include_self=False)

# ⌨️ 5-3-6 顯示對方輸入狀態：當使用者正在輸入時觸發
@socketio.on("typing")
def on_typing(data):
    emit("typing", data, broadcast=True, include_self=False)

# ✏️ 5-3-7 更改使用者名稱時觸發[cite: 15]
@socketio.on("change_username")
def on_change(data):
    old = data.get("oldUsername")  # 原本的名稱[cite: 15]
    new = data.get("newUsername")  # 新名稱[cite: 15]

    # 如果這個 SID 還在 clients 裡，更新名稱[cite: 15]
    if request.sid in clients:
        clients[request.sid]["username"] = new

    # 廣播名稱變更事件給所有人[cite: 15]
    emit("user_changed_name", 
        {"oldUsername": old, "newUsername": new}, 
        broadcast=True)

@app.route("/")
def index():
    return render_template("index.html")

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, debug=True)