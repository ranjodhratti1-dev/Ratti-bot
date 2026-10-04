import os
import time
import requests
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from gtts import gTTS

# --- Health Check Server for Render Free Tier ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is active!")

    def log_message(self, format, *args):
        return

def run_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    server.serve_forever()

threading.Thread(target=run_health_server, daemon=True).start()

# --- API Keys ---
TELEGRAM_BOT_TOKEN = "8937029414:AAFiIV32-Wz9e2j-duP3FncUo3zWrTbBHoU"
GEMINI_API_KEY = "AQ.Ab8RN6Ke51fqNfkgK9qOgD-cAajgVkj0_uNxC6zVjbMCpAHOJQ"
TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def send_message(chat_id, text):
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Error: {e}")

def send_video(chat_id, video_path, caption=""):
    url = f"{TELEGRAM_API_URL}/sendVideo"
    try:
        with open(video_path, 'rb') as video_file:
            files = {'video': video_file}
            data = {'chat_id': chat_id, 'caption': caption, 'parse_mode': 'Markdown'}
            requests.post(url, files=files, data=data, timeout=120)
    except Exception as e:
        send_message(chat_id, f"❌ Error: {e}")

def call_gemini(prompt):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json()["candidates"][0]["content"]["parts"][0]["text"]
        return f"❌ Gemini API Error: {response.status_code}"
    except Exception as e:
        return f"❌ Exception: {e}"

def make_short_video(topic, chat_id):
    send_message(chat_id, "⏳ **1/3:** ਪੰਜਾਬੀ ਸਕ੍ਰਿਪਟ ਤਿਆਰ ਹੋ ਰਹੀ ਹੈ...")
    prompt = f"Write a short, engaging 15-second YouTube Short script in Punjabi for: '{topic}'. Return ONLY plain spoken Punjabi text in Gurmukhi script without any extra labels or English."
    script = call_gemini(prompt)

    send_message(chat_id, "⏳ **2/3:** ਪੰਜਾਬੀ AI ਆਵਾਜ਼ (Voiceover) ਜਨਰੇਟ ਹੋ ਰਹੀ ਹੈ...")
    try:
        tts = gTTS(text=script, lang='pa')
        tts.save("voice.mp3")
    except Exception as e:
        send_message(chat_id, f"❌ Voice Error: {e}")
        return

    send_message(chat_id, "⏳ **3/3:** ਵੀਡੀਓ ਰੈਂਡਰ ਕੀਤੀ ਜਾ ਰਹੀ ਹੈ...")
    safe_topic = topic.replace("'", "").replace('"', '').replace(":", "").replace("\\", "")

    cmd = [
        "ffmpeg", "-y",
        "-f", "lavfi", "-i", "color=c=0x0f172a:s=720x1280:r=25",
        "-i", "voice.mp3",
        "-vf", f"drawtext=text='{safe_topic}':fontcolor=white:fontsize=40:x=(w-text_w)/2:y=(h-text_h)/2:box=1:boxcolor=black@0.6:boxborderw=10",
        "-c:v", "libx264", "-preset", "ultrafast",
        "-c:a", "aac", "-pix_fmt", "yuv420p", "-shortest", "short_output.mp4"
    ]
    
    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    if os.path.exists("short_output.mp4"):
        send_video(chat_id, "short_output.mp4", f"🎬 **Short Video:** {topic}\n\n📝 **Script:**\n{script}")
        if os.path.exists("voice.mp3"): os.remove("voice.mp3")
        if os.path.exists("short_output.mp4"): os.remove("short_output.mp4")
    else:
        send_message(chat_id, "❌ ਵੀਡੀਓ ਫਾਈਲ ਨਹੀਂ ਬਣ ਸਕੀ।")

def process_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "")

    if text.startswith("/start"):
        send_message(chat_id, "👋 **YouTube Creator AI Bot Active!**\n\n1. `/make_short [ਟੌਪਿਕ]` - Punjabi AI Voice Short Video\n2. `/punjabi [ਟੌਪਿਕ]` - Punjabi Script\n3. `/thumbnail [ਟੌਪਿਕ]` - Thumbnail Ideas\n4. `/idea [ਟੌਪਿਕ]` - Video Idea\n5. `/seo [ਟੌਪਿਕ]` - SEO Titles & Tags")
    elif text.startswith("/make_short"):
        topic = text.replace("/make_short", "").strip()
        if topic: make_short_video(topic, chat_id)
        else: send_message(chat_id, "⚠️ ਕਿਰਪਾ ਕਰਕੇ ਟੌਪਿਕ ਲਿਖੋ: `/make_short Punjabi Tech Hacks`")
    elif text.startswith("/punjabi"):
        topic = text.replace("/punjabi", "").strip()
        if topic: send_message(chat_id, call_gemini(f"Write viral script in Punjabi for: '{topic}'"))
    elif text.startswith("/thumbnail"):
        topic = text.replace("/thumbnail", "").strip()
        if topic: send_message(chat_id, call_gemini(f"Provide 3 thumbnail ideas for: '{topic}'"))
    elif text.startswith("/idea"):
        topic = text.replace("/idea", "").strip()
        if topic: send_message(chat_id, call_gemini(f"Create video outline for: '{topic}'"))
    elif text.startswith("/seo"):
        topic = text.replace("/seo", "").strip()
        if topic: send_message(chat_id, call_gemini(f"Give 5 titles, SEO description & 15 hashtags for: '{topic}'"))

def main():
    print("🤖 YouTube Creator AI Bot running...")
    offset = None
    while True:
        try:
            url = f"{TELEGRAM_API_URL}/getUpdates?timeout=30"
            if offset: url += f"&offset={offset}"
            res = requests.get(url, timeout=35).json()
            if res.get("ok"):
                for result in res.get("result", []):
                    offset = result["update_id"] + 1
                    if "message" in result: process_message(result["message"])
        except Exception as e:
            time.sleep(3)

if __name__ == "__main__":
    main()
