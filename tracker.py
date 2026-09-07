import os
import sys
import json
import requests

# ==========================================
# CẤU HÌNH (Lấy từ biến môi trường hoặc file .env)
# ==========================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "").strip()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()

# Nếu chưa có biến môi trường, đọc từ file .env nếu có
ENV_FILE = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(ENV_FILE):
    with open(ENV_FILE, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                key = key.strip()
                val = val.strip().strip('"').strip("'")
                if key == "TELEGRAM_BOT_TOKEN" and not TELEGRAM_BOT_TOKEN:
                    TELEGRAM_BOT_TOKEN = val
                elif key == "TELEGRAM_CHAT_ID" and not TELEGRAM_CHAT_ID:
                    TELEGRAM_CHAT_ID = val
                elif key == "GEMINI_API_KEY" and not GEMINI_API_KEY:
                    GEMINI_API_KEY = val

REPO_OWNER = "steven2358"
REPO_NAME = "awesome-generative-ai"
STATE_FILE = os.path.join(os.path.dirname(__file__), "last_commit.txt")


def send_telegram_message(text: str):
    """Gửi tin nhắn định dạng HTML hoặc Text về Telegram"""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Lỗi: Chưa cấu hình TELEGRAM_BOT_TOKEN hoặc TELEGRAM_CHAT_ID")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    try:
        res = requests.post(url, json=payload, timeout=15)
        res_data = res.json()
        if res_data.get("ok"):
            print("✅ Đã gửi tin nhắn Telegram thành công!")
            return True
        else:
            # Thử gửi dạng text thuần nếu lỗi định dạng HTML
            payload.pop("parse_mode", None)
            res2 = requests.post(url, json=payload, timeout=15)
            if res2.json().get("ok"):
                print("✅ Đã gửi tin nhắn Telegram (chế độ văn bản thuần) thành công!")
                return True
            print(f"❌ Telegram API trả về lỗi: {res_data}")
            return False
    except Exception as e:
        print(f"❌ Lỗi kết nối Telegram: {e}")
        return False


def summarize_with_gemini(raw_text: str) -> str:
    """Gọi Gemini API để tóm tắt các công nghệ AI mới bằng tiếng Việt ngắn gọn"""
    if not GEMINI_API_KEY:
        print("❌ Lỗi: Chưa cấu hình GEMINI_API_KEY")
        return "⚠️ Không có Gemini API Key để tóm tắt."

    # Gọi trực tiếp REST API của Gemini (không phụ thuộc SDK cồng kềnh)
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    
    prompt = f"""
Bạn là một trợ lý công nghệ AI thông minh. Dưới đây là danh sách các nội dung mới được cập nhật trên kho GitHub "Awesome Generative AI".

Dữ liệu đầu vào:
{raw_text}

Yêu cầu:
1. Viết một bản tin ngắn gọn, súc tích bằng tiếng Việt để gửi vào Telegram.
2. Với mỗi công cụ/model mới, ghi rõ:
   - Tên công cụ (kèm link nếu có)
   - 1-2 câu miêu tả công dụng chính
3. Sử dụng các emoji phù hợp (⚡, 🛠️, 🎨, 🤖...) để tin nhắn sinh động, dễ đọc trên điện thoại.
4. Độ dài: Tối đa 5 gạch đầu dòng, không thêm lời chào mở đầu hay kết thúc rườm rà.
"""

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=30)
        if res.status_code == 200:
            data = res.json()
            summary = data["candidates"][0]["content"]["parts"][0]["text"]
            return summary.strip()
        else:
            print(f"⚠️ Gemini API trả về mã lỗi {res.status_code}: {res.text}")
            # Fallback nếu model 2.5-flash chưa sẵn sàng trên key, thử gọi 1.5-flash
            url_fallback = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            res2 = requests.post(url_fallback, headers=headers, json=payload, timeout=30)
            if res2.status_code == 200:
                data2 = res2.json()
                return data2["candidates"][0]["content"]["parts"][0]["text"].strip()
            return f"⚠️ Lỗi tóm tắt từ Gemini: {res.text[:200]}"
    except Exception as e:
        print(f"❌ Lỗi kết nối Gemini API: {e}")
        return f"⚠️ Lỗi khi gọi Gemini: {e}"


def get_latest_commit():
    """Lấy thông tin commit mới nhất của file README.md từ GitHub API"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits?path=README.md&per_page=1"
    headers = {"User-Agent": "Daily-AI-Digest-Bot"}
    res = requests.get(url, headers=headers, timeout=15)
    if res.status_code == 200:
        commits = res.json()
        if commits:
            return commits[0]["sha"], commits[0]["commit"]["message"]
    return None, None


def get_commit_diff(old_sha: str, new_sha: str):
    """Lấy các dòng thay đổi giữa 2 commit"""
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/compare/{old_sha}...{new_sha}"
    headers = {"User-Agent": "Daily-AI-Digest-Bot"}
    res = requests.get(url, headers=headers, timeout=15)
    if res.status_code == 200:
        data = res.json()
        added_lines = []
        for file in data.get("files", []):
            if file.get("filename") == "README.md":
                patch = file.get("patch", "")
                for line in patch.split("\n"):
                    if line.startswith("+") and not line.startswith("+++"):
                        added_lines.append(line[1:].strip())
        return "\n".join(added_lines)
    return ""


def main():
    print("🚀 Bắt đầu quét cập nhật AI...")

    # Kiểm tra cờ test (--test)
    if "--test" in sys.argv:
        print("🧪 Đang chạy chế độ kiểm tra (TEST MODE)...")
        sample_update = """
        - [FLUX 1.1 Pro](https://blackforestlabs.ai/) - New frontier image generation model with 6x faster speed and higher quality.
        - [Cursor Router](https://cursor.com/) - Intelligent model routing system that automatically picks the right model for coding.
        - [NotebookLM Audio Overviews](https://notebooklm.google/) - Generates conversational podcasts from your uploaded documents.
        """
        print("1. Đang gọi Gemini API để tóm tắt mẫu...")
        summary = summarize_with_gemini(sample_update)
        print("\n--- Bản tóm tắt từ Gemini ---")
        print(summary)
        print("-----------------------------\n")

        print("2. Đang gửi thử vào Telegram của bạn...")
        msg = f"<b>🔔 [TEST] Bản tin AI hàng ngày</b>\n\n{summary}\n\n<i>✨ Hệ thống của bạn đã sẵn sàng hoạt động!</i>"
        if send_telegram_message(msg):
            print("\n🎉 THÀNH CÔNG! Hãy kiểm tra tin nhắn Telegram trên điện thoại của bạn ngay.")
        return

    # Chế độ chạy thật (Daily Tracker)
    latest_sha, commit_msg = get_latest_commit()
    if not latest_sha:
        print("❌ Không lấy được commit từ GitHub.")
        return

    last_saved_sha = None
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            last_saved_sha = f.read().strip()

    if not last_saved_sha:
        print(f"📌 Chạy lần đầu tiên. Đang lưu commit hiện tại ({latest_sha[:7]}).")
        with open(STATE_FILE, "w") as f:
            f.write(latest_sha)
        send_telegram_message(f"<b>🚀 AI Tracker Bot đã được kích hoạt!</b>\n\nBot đã bắt đầu theo dõi repo <code>{REPO_NAME}</code>. Khi có công cụ mới, bạn sẽ nhận được thông báo tại đây mỗi ngày.")
        return

    if latest_sha == last_saved_sha:
        print("✅ Chưa có cập nhật nào mới từ lần quét trước.")
        return

    print(f"⚡ Phát hiện cập nhật mới! ({last_saved_sha[:7]} -> {latest_sha[:7]})")
    diff_text = get_commit_diff(last_saved_sha, latest_sha)

    if not diff_text.strip():
        print("ℹ️ Commit có thay đổi nhưng không ảnh hưởng tới nội dung công cụ.")
        with open(STATE_FILE, "w") as f:
            f.write(latest_sha)
        return

    print("🤖 Đang phân tích và tóm tắt qua Gemini...")
    summary = summarize_with_gemini(diff_text)

    telegram_msg = f"<b>📢 CẬP NHẬT CÔNG NGHỆ AI MỚI</b>\n\n{summary}\n\n🔗 <i>Nguồn: {REPO_OWNER}/{REPO_NAME}</i>"
    if send_telegram_message(telegram_msg):
        with open(STATE_FILE, "w") as f:
            f.write(latest_sha)
        print("✅ Đã cập nhật trạng thái mới thành công.")


if __name__ == "__main__":
    main()

