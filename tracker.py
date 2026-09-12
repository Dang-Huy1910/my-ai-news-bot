import os
import sys
import json
import time
import re
from datetime import datetime
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

# Danh sách các repo Awesome cần theo dõi cập nhật (AI Tools & MCP Servers)
TRACKED_REPOS = [
    {
        "owner": "steven2358",
        "repo": "awesome-generative-ai",
        "label": "Awesome Generative AI",
        "state_file": os.path.join(os.path.dirname(__file__), "last_commit.txt"),
    },
    {
        "owner": "punkpeye",
        "repo": "awesome-mcp-servers",
        "label": "Awesome MCP Servers",
        "state_file": os.path.join(os.path.dirname(__file__), "last_commit_mcp.txt"),
    }
]
LESSON_STATE_FILE = os.path.join(os.path.dirname(__file__), "lesson_day.txt")

# ========================================================
# LỘ TRÌNH KIẾN THỨC AI ENGINEERING (Từ cơ bản đến nâng cao)
# ========================================================
AI_CURRICULUM = [
    {"day": 1, "topic": "Vector & Phép toán Vectorization trong NumPy", "tech": "numpy", "desc": "Tại sao AI không dùng vòng lặp for mà phải dùng vector hóa (SIMD speedup)?"},
    {"day": 2, "topic": "Tích vô hướng (Dot Product) & Cosine Similarity", "tech": "numpy", "desc": "Bản chất toán học để đo độ tương đồng giữa 2 câu trong Vector Database / RAG."},
    {"day": 3, "topic": "Nhân ma trận (Matrix Multiplication - np.matmul)", "tech": "numpy", "desc": "Phép toán cốt lõi chiếm 95% khối lượng tính toán của mọi mạng Neural và LLM."},
    {"day": 4, "topic": "Cơ chế Broadcasting trong NumPy", "tech": "numpy", "desc": "Cách cộng/nhân các tensor lệch chiều tự động mà không cần nhân bản dữ liệu bộ nhớ."},
    {"day": 5, "topic": "Pandas Data Cleaning & Xử lý Text cho NLP", "tech": "pandas", "desc": "Làm sạch text, xử lý giá trị NaN và chuẩn hóa cột dữ liệu trước khi nạp vào AI."},
    {"day": 6, "topic": "Chuẩn hóa dữ liệu (Normalization & Standardization)", "tech": "numpy / pandas", "desc": "MinMaxScaler vs StandardScaler: Tại sao không scale thì model không hội tụ?"},
    {"day": 7, "topic": "Khái niệm Tensor trong PyTorch", "tech": "pytorch / tensor", "desc": "Tensor khác gì NumPy ndarray? Khả năng đưa lên GPU (CUDA) và lưu đồ thị tính toán."},
    {"day": 8, "topic": "PyTorch Autograd & Đạo hàm tự động", "tech": "pytorch / tensor", "desc": "Cách PyTorch tự động tính đạo hàm (gradient) với .backward() và .grad."},
    {"day": 9, "topic": "Thuật toán Gradient Descent & Learning Rate", "tech": "numpy / pytorch", "desc": "Nguyên lý quả bóng lăn xuống dốc để tìm bộ trọng số tối ưu (loss nhỏ nhất)."},
    {"day": 10, "topic": "Hàm kích hoạt (Activation): ReLU vs Leaky ReLU", "tech": "numpy / pytorch", "desc": "Tại sao mạng neural cần hàm phi tuyến? Giải quyết bài toán Vanishing Gradient."},
    {"day": 11, "topic": "Hàm kích hoạt Softmax", "tech": "numpy / pytorch", "desc": "Cách chuyển đổi vector điểm thô (logits) thành phân phối xác suất từ 0 đến 1."},
    {"day": 12, "topic": "Hàm mất mát (Loss Function): MSE vs Cross-Entropy", "tech": "pytorch", "desc": "Khi nào dùng Mean Squared Error (Regression) và khi nào dùng Cross-Entropy (Phân loại)?"},
    {"day": 13, "topic": "Xây dựng Linear Regression từ đầu (From Scratch)", "tech": "numpy / pytorch", "desc": "Tự tay viết phương trình y = W*x + b và cập nhật trọng số W, b sau mỗi epoch."},
    {"day": 14, "topic": "Logistic Regression & Hàm Sigmoid", "tech": "numpy / pytorch", "desc": "Phân loại nhị phân 0/1 bằng cách bẻ cong đường thẳng qua hàm Sigmoid."},
    {"day": 15, "topic": "Thuật toán K-Nearest Neighbors (KNN)", "tech": "numpy", "desc": "Dự đoán nhãn dựa trên K điểm dữ liệu gần nhất trong không gian vector."},
    {"day": 16, "topic": "Thuật toán Phân cụm K-Means", "tech": "numpy", "desc": "Cách nhóm các cụm vector embeddings mà không cần dữ liệu có nhãn trước."},
    {"day": 17, "topic": "Khái niệm Vector Embeddings", "tech": "numpy / pytorch", "desc": "Biến từ ngữ, hình ảnh thành vector số học biểu diễn ngữ nghĩa không gian."},
    {"day": 18, "topic": "Cơ chế Self-Attention trong Transformer", "tech": "pytorch / tensor", "desc": "Các vector Query, Key, Value tương tác với nhau thế nào để hiểu ngữ cảnh câu?"},
    {"day": 19, "topic": "Kỹ thuật Tokenization (Byte-Pair Encoding - BPE)", "tech": "python / nlp", "desc": "Cách LLM bẻ nhỏ từ ngữ thành các subwords để nạp vào model."},
    {"day": 20, "topic": "Tham số Temperature & Top-p trong LLM", "tech": "numpy / softmax", "desc": "Điều khiển độ sáng tạo hay khuôn mẫu của LLM qua việc chia logits trước Softmax."},
    {"day": 21, "topic": "Cơ chế RAG (Retrieval-Augmented Generation)", "tech": "rag / vector", "desc": "Kết hợp Vector Search (Cosine distance) + Prompt Context để LLM không bịa thông tin."},
    {"day": 22, "topic": "Kỹ thuật Quantization (Lượng tử hóa mô hình)", "tech": "tensor / deep learning", "desc": "Giảm dung lượng model từ FP16 xuống INT8/INT4 (GGUF) để chạy mượt trên máy cá nhân."}
]


def clean_telegram_html(text: str) -> str:
    """Loại bỏ các thẻ HTML Telegram không hỗ trợ và chuẩn hóa giao diện"""
    text = re.sub(r'<li[^>]*>', '\n🔹 ', text, flags=re.IGNORECASE)
    text = re.sub(r'</?(ul|ol|li|p|h[1-6]|div|span)[^>]*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<br\s*/?>', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()


def send_telegram_message(text: str):
    """Gửi tin nhắn định dạng HTML về Telegram"""
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


def get_current_lesson():
    """Lấy bài học AI Engineering cho ngày hôm nay theo tiến độ lũy tiến"""
    day_idx = 1
    if os.path.exists(LESSON_STATE_FILE):
        try:
            with open(LESSON_STATE_FILE, "r") as f:
                day_idx = int(f.read().strip())
        except Exception:
            day_idx = 1

    # Lấy bài học tương ứng (xoay vòng nếu hết danh sách)
    curriculum_len = len(AI_CURRICULUM)
    selected_topic = AI_CURRICULUM[(day_idx - 1) % curriculum_len]
    return day_idx, selected_topic


def advance_lesson_day(current_day: int):
    """Cập nhật ngày học tiếp theo vào file lưu trạng thái"""
    try:
        with open(LESSON_STATE_FILE, "w") as f:
            f.write(str(current_day + 1))
    except Exception as e:
        print(f"⚠️ Không thể lưu trạng thái ngày học: {e}")


def get_github_trending_repos():
    """Lấy Top 5 kho lưu trữ AI & Machine Learning trending nhất trên GitHub"""
    url = "https://api.github.com/search/repositories?q=topic:ai+created:>2026-01-01&sort=stars&order=desc&per_page=5"
    headers = {"User-Agent": "DailyAIBot/1.0"}
    repos = []
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code == 200:
            items = res.json().get("items", [])
            for item in items[:5]:
                name = item.get("full_name", "")
                stars = item.get("stargazers_count", 0)
                desc = item.get("description", "") or "Không có mô tả."
                # Cắt ngắn mô tả nếu dài
                if len(desc) > 90:
                    desc = desc[:87] + "..."
                url_repo = item.get("html_url", "")
                repos.append({
                    "name": name,
                    "stars": f"{stars:,}",
                    "desc": desc,
                    "url": url_repo
                })
    except Exception as e:
        print(f"⚠️ Lỗi kết nối GitHub Search API: {e}")
    return repos


# Danh sách chủ đề thảo luận: Ưu tiên hàng đầu và chủ đề thứ cấp
PRIORITY_TOPICS = ["Grok", "Codex", "Gemini"]
SECONDARY_TOPICS = ["DeepSeek", "Cursor AI", "Antigravity", "MCP", "Claude"]
ALL_DISCUSSION_TOPICS = PRIORITY_TOPICS + SECONDARY_TOPICS


def get_hacker_news_posts():
    """Lấy các bài thảo luận nổi bật từ Hacker News, mở rộng tìm kiếm cho Grok, Codex, Gemini"""
    posts = []
    headers = {"User-Agent": "DailyAINewsBot/1.0"}

    # Từ khóa tìm kiếm tối ưu trên HN Algolia
    query_map = {
        "Grok": "Grok OR xAI",
        "Codex": "Codex OR \"OpenAI Codex\"",
        "Gemini": "Gemini OR \"Google Gemini\"",
        "DeepSeek": "DeepSeek",
        "Cursor AI": "\"Cursor AI\" OR \"Cursor editor\"",
        "Antigravity": "Antigravity",
        "MCP": "\"Model Context Protocol\" OR MCP",
        "Claude": "Claude"
    }

    for kw in ALL_DISCUSSION_TOPICS:
        query_term = query_map.get(kw, kw)
        try:
            url = f"https://hn.algolia.com/api/v1/search?query={query_term}&tags=story&hitsPerPage=5"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                for hit in data.get("hits", []):
                    title = hit.get("title")
                    points = hit.get("points", 0)
                    link = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                    if title and points and points >= 10:
                        posts.append({
                            "source": "Hacker News",
                            "topic": kw,
                            "title": title,
                            "score": points,
                            "link": link
                        })
        except Exception as e:
            print(f"⚠️ Lỗi quét Hacker News cho {kw}: {e}")

    return posts


def get_reddit_posts():
    """Lấy các bài thảo luận nổi bật từ Reddit về Grok, Codex, Gemini, DeepSeek, Cursor, MCP, Claude"""
    posts = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 DailyAIBot/1.0"}

    query_map = {
        "Grok": "Grok",
        "Codex": "Codex",
        "Gemini": "Gemini",
        "DeepSeek": "DeepSeek",
        "Cursor AI": "Cursor",
        "Antigravity": "Antigravity",
        "MCP": "MCP",
        "Claude": "Claude"
    }

    # Bổ sung các cộng đồng r/GoogleGeminiAI và r/Singularity để đón đầu tin tức Grok và Gemini
    subreddits = "LocalLLaMA+ChatGPT+artificial+GoogleGeminiAI+singularity"

    for kw in ALL_DISCUSSION_TOPICS:
        query_term = query_map.get(kw, kw)
        try:
            url = f"https://www.reddit.com/r/{subreddits}/search.json?q={query_term}&sort=top&t=week&limit=5"
            res = requests.get(url, headers=headers, timeout=10)
            if res.status_code == 200:
                data = res.json()
                children = data.get("data", {}).get("children", [])
                for child in children:
                    d = child.get("data", {})
                    title = d.get("title")
                    score = d.get("score", 0)
                    permalink = "https://reddit.com" + d.get("permalink", "")
                    if title and score >= 20:
                        posts.append({
                            "source": "Reddit",
                            "topic": kw,
                            "title": title,
                            "score": score,
                            "link": permalink
                        })
        except Exception as e:
            print(f"⚠️ Lỗi quét Reddit cho {kw}: {e}")

    return posts


def filter_and_prioritize_discussions(posts: list, max_total: int = 4) -> list:
    """
    Lọc và ưu tiên bài thảo luận:
    - ĐẶC BIỆT ƯU TIÊN cho Grok, Codex, Gemini.
    - Đảm bảo tính đa dạng: Mỗi chủ đề/mô hình TỐI ĐA 1 BÀI (chấm dứt tình trạng Claude độc chiếm cả 3 bài).
    - Claude chỉ được tối đa 1 bài và chỉ lấy nếu còn chỗ sau khi đã chọn các chủ đề ưu tiên.
    """
    if not posts:
        return []

    # Nhóm bài viết theo topic, sắp xếp theo điểm vote giảm dần trong từng nhóm
    grouped_by_topic = {}
    for p in posts:
        t = p.get("topic")
        if t not in grouped_by_topic:
            grouped_by_topic[t] = []
        grouped_by_topic[t].append(p)

    for t in grouped_by_topic:
        grouped_by_topic[t].sort(key=lambda x: x["score"], reverse=True)

    selected = []
    used_topics = set()

    # Bước 1: Ưu tiên chọn 1 bài tốt nhất từ mỗi topic trong PRIORITY_TOPICS (Grok, Codex, Gemini)
    for topic in PRIORITY_TOPICS:
        if topic in grouped_by_topic and grouped_by_topic[topic]:
            best_post = grouped_by_topic[topic][0]
            selected.append(best_post)
            used_topics.add(topic)

    # Bước 2: Điền các vị trí còn lại từ các chủ đề khác (DeepSeek, MCP, Cursor, Claude...)
    remaining_candidates = []
    for topic, topic_posts in grouped_by_topic.items():
        if topic not in used_topics and topic_posts:
            remaining_candidates.append(topic_posts[0])

    # Sắp xếp các topic còn lại theo score giảm dần
    remaining_candidates.sort(key=lambda x: x["score"], reverse=True)

    for p in remaining_candidates:
        if len(selected) >= max_total:
            break
        selected.append(p)
        used_topics.add(p["topic"])

    # Bước 3: Nếu vẫn chưa đủ max_total và còn bài từ PRIORITY_TOPICS (ví dụ có 2 tin nóng về Grok/Gemini)
    if len(selected) < max_total:
        for topic in PRIORITY_TOPICS:
            if topic in grouped_by_topic and len(grouped_by_topic[topic]) > 1:
                selected.append(grouped_by_topic[topic][1])
                if len(selected) >= max_total:
                    break

    return selected



def summarize_with_gemini(lesson_info: dict, trending_repos: list, awesome_diff: str, discussions: list) -> str:
    """Gọi Gemini API tổng hợp bản tin 4 phần ưu tiên Góc học tập AI lên đầu"""
    if not GEMINI_API_KEY:
        print("❌ Lỗi: Chưa cấu hình GEMINI_API_KEY")
        return "⚠️ Không có Gemini API Key để tạo bản tin."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}

    # Chuẩn bị dữ liệu Top 5 GitHub Trending
    trending_text = ""
    if trending_repos:
        for r in trending_repos:
            trending_text += f"- [{r['stars']} ⭐] {r['name']}: {r['desc']} - Link: {r['url']}\n"
    else:
        trending_text = "Không có repo trending mới ghi nhận hôm nay."

    # Chuẩn bị dữ liệu Thảo luận
    discussions_text = ""
    if discussions:
        for item in discussions:
            discussions_text += f"- [{item['source']} - {item['score']} upvotes] {item['title']} (Chủ đề: {item['topic']}) - Link: {item['link']}\n"
    else:
        discussions_text = "Không có thảo luận nổi bật mới hôm nay."

    today_str = datetime.now().strftime("%d/%m/%Y")

    prompt = f"""
Bạn là một kỹ sư AI Senior và người hướng dẫn công nghệ AI. Hãy biên soạn dữ liệu dưới đây thành một bản tin Telegram buổi sáng HOÀN HẢO, CHỈN CHU, DỄ ĐỌC.

--- THÔNG TIN BÀI HỌC HÔM NAY (NGÀY {lesson_info['day']}) ---
Chủ đề: {lesson_info['topic']}
Công nghệ liên quan: {lesson_info['tech']}
Gợi ý nội dung: {lesson_info['desc']}

--- DỮ LIỆU TOP 5 GITHUB TRENDING HÔM NAY ---
{trending_text}

--- DỮ LIỆU CÔNG CỤ & MODEL MỚI (GITHUB AWESOME AI & AWESOME MCP SERVERS) ---
{awesome_diff if awesome_diff.strip() else "Hôm nay chưa có cập nhật công cụ mới trên Awesome AI hoặc Awesome MCP."}

--- DỮ LIỆU THẢO LUẬN CỘNG ĐỒNG (REDDIT & HACKER NEWS) ---
{discussions_text}

--- QUY TẮC ĐỊNH DẠNG HTML BẮT BUỘC: ---
- TUYỆT ĐỐI KHÔNG dùng thẻ: <ul>, <ol>, <li>, <p>, <br>, <h1>, <h2>.
- CHỈ DÙNG: <b>, <i>, <code>, <pre>, <a href="...">, <blockquote>.
- Dùng xuống dòng trực tiếp thay vì <br>.

--- THỨ TỰ BẮT BUỘC CỦA CÁC PHẦN (ƯU TIÊN HỌC TẬP LÊN ĐẦU): ---

☕ <b>BẢN TIN AI & HỌC TẬP BUỔI SÁNG</b>
<i>📅 Ngày {today_str} • Ngày học #{lesson_info['day']}</i>
━━━━━━━━━━━━━━━━━━━━

 <b>1. GÓC HỌC TẬP AI ENGINEERING HÔM NAY</b>
<b>Chủ đề: {lesson_info['topic']}</b>
<blockquote>💡 <b>Khái niệm:</b> [Giải thích 2-3 câu thật dễ hiểu, trực quan về bản chất toán học/thuật toán]
💻 <b>Code thực chiến:</b>
<code>[Viết 3-5 dòng code Python ngắn gọn bằng NumPy/Pandas/PyTorch minh họa trực tiếp khái niệm]</code>
🎯 <b>Ứng dụng:</b> [1 câu giải thích tại sao kỹ sư AI cần biết điều này trong thực tế]</blockquote>

━━━━━━━━━━━━━━━━━━━━

 <b>2. TOP 5 GITHUB REPO TRENDING (AI & ML)</b>
[Liệt kê đủ 5 repo trending theo mẫu sau:]
1️⃣ <a href="[url_repo]"><b>[Tên repo]</b></a> (⭐ [Số sao])
<i>[Mô tả 1 câu về công dụng của repo này]</i>

2️⃣ <a href="[url_repo]"><b>[Tên repo]</b></a> (⭐ [Số sao])
<i>[Mô tả 1 câu]</i>
[Tương tự cho các repo 3, 4, 5]

━━━━━━━━━━━━━━━━━━━━

🛠️ <b>3. CÔNG CỤ & MCP SERVER MỚI NỔI BẬT</b>
[Nêu 1-2 công cụ hoặc MCP server mới từ Awesome AI / Awesome MCP Server kèm link in đậm, mô tả ngắn gọn 1 câu]

━━━━━━━━━━━━━━━━━━━━

🔥 <b>4. THẢO LUẬN NỔI BẬT (Reddit & HN)</b>
[Trình bày từ 2 đến 3 bài thảo luận theo dữ liệu cung cấp.
QUY TẮC BẮT BUỘC CHO PHẦN NÀY:
- ĐẶC BIỆT ƯU TIÊN chọn các thảo luận về: Grok (xAI), Codex (OpenAI), và Gemini (Google).
- TUYỆT ĐỐI KHÔNG để một mô hình độc chiếm (Ví dụ: KHÔNG chọn 2 hoặc 3 bài cùng về Claude).
- Mỗi nền tảng/model chỉ xuất hiện TỐI ĐA 1 BÀI để đảm bảo tính đa dạng (Nếu có bài về Claude, tối đa chỉ chọn 1 bài).]

💬 <b>[Tên chủ đề thảo luận - ghi rõ tên công nghệ/model: ví dụ Grok 3, OpenAI Codex, Google Gemini, v.v.]</b>
<blockquote>[1-2 câu tóm tắt nội dung thảo luận].
👉 <a href="[link_goc]">Xem thảo luận</a> ([Số] votes)</blockquote>

━━━━━━━━━━━━━━━━━━━━
<i>🤖 Cập nhật tự động bởi AI Learning & News Bot</i>
"""

    payload = {
        "contents": [
            {
                "parts": [{"text": prompt}]
            }
        ]
    }

    try:
        res = requests.post(url, headers=headers, json=payload, timeout=35)
        if res.status_code == 200:
            data = res.json()
            summary = data["candidates"][0]["content"]["parts"][0]["text"]
            return clean_telegram_html(summary)
        else:
            url_fallback = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
            res2 = requests.post(url_fallback, headers=headers, json=payload, timeout=35)
            if res2.status_code == 200:
                data2 = res2.json()
                return clean_telegram_html(data2["candidates"][0]["content"]["parts"][0]["text"])
            return f"⚠️ Lỗi tóm tắt từ Gemini: {res.text[:200]}"
    except Exception as e:
        print(f"❌ Lỗi kết nối Gemini API: {e}")
        return f"⚠️ Lỗi khi gọi Gemini: {e}"


def get_latest_commit(owner: str, repo: str):
    """Lấy commit mới nhất của file README.md từ GitHub API"""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits?path=README.md&per_page=1"
    headers = {"User-Agent": "Daily-AI-Digest-Bot"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            commits = res.json()
            if commits:
                return commits[0]["sha"], commits[0]["commit"]["message"]
    except Exception as e:
        print(f"⚠️ Lỗi kết nối GitHub API ({owner}/{repo}): {e}")
    return None, None


def get_commit_diff(owner: str, repo: str, old_sha: str, new_sha: str):
    """Lấy các dòng thay đổi giữa 2 commit"""
    url = f"https://api.github.com/repos/{owner}/{repo}/compare/{old_sha}...{new_sha}"
    headers = {"User-Agent": "Daily-AI-Digest-Bot"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            added_lines = []
            for file in data.get("files", []):
                if file.get("filename") == "README.md":
                    patch = file.get("patch", "")
                    for line in patch.split("\n"):
                        if line.startswith("+") and not line.startswith("+++"):
                            content = line[1:].strip()
                            if content and content.startswith("-"):
                                added_lines.append(content)
            return "\n".join(added_lines)
    except Exception as e:
        print(f"⚠️ Lỗi lấy commit diff ({owner}/{repo}): {e}")
    return ""


def get_recent_additions(owner: str, repo: str, commit_sha: str, limit: int = 5):
    """Lấy các mục mới được thêm vào từ commit mới nhất (dùng khi mới khởi tạo hoặc cần xem cập nhật gần nhất)"""
    url = f"https://api.github.com/repos/{owner}/{repo}/commits/{commit_sha}"
    headers = {"User-Agent": "Daily-AI-Digest-Bot"}
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            data = res.json()
            added_lines = []
            for file in data.get("files", []):
                if file.get("filename") == "README.md":
                    patch = file.get("patch", "")
                    for line in patch.split("\n"):
                        if line.startswith("+") and not line.startswith("+++"):
                            content = line[1:].strip()
                            if content and content.startswith("-"):
                                added_lines.append(content)
            return "\n".join(added_lines[:limit])
    except Exception as e:
        print(f"⚠️ Lỗi lấy commit gần nhất ({owner}/{repo}): {e}")
    return ""


def get_all_tracked_updates():
    """Quét cập nhật mới từ các repo Awesome AI và Awesome MCP Servers"""
    all_diffs = []
    updates_to_save = []

    for item in TRACKED_REPOS:
        owner = item["owner"]
        repo = item["repo"]
        label = item["label"]
        state_file = item["state_file"]

        latest_sha, commit_msg = get_latest_commit(owner, repo)
        last_saved_sha = None
        if os.path.exists(state_file):
            try:
                with open(state_file, "r", encoding="utf-8") as f:
                    last_saved_sha = f.read().strip()
            except Exception:
                last_saved_sha = None

        repo_diff = ""
        if latest_sha and last_saved_sha and latest_sha != last_saved_sha:
            first_line = commit_msg.split("\n")[0] if commit_msg else ""
            print(f"⚡ Phát hiện commit mới trên {label} ({last_saved_sha[:7]} -> {latest_sha[:7]}): {first_line}")
            repo_diff = get_commit_diff(owner, repo, last_saved_sha, latest_sha)
            updates_to_save.append((state_file, latest_sha))
        elif latest_sha and not last_saved_sha:
            print(f"📌 Lần đầu quét {label}, lấy các mục mới nhất từ commit {latest_sha[:7]}...")
            repo_diff = get_recent_additions(owner, repo, latest_sha, limit=5)
            updates_to_save.append((state_file, latest_sha))
        elif latest_sha:
            updates_to_save.append((state_file, latest_sha))

        if repo_diff.strip():
            all_diffs.append(f"📦 <b>{label}:</b>\n{repo_diff}")

    combined_diff = "\n\n".join(all_diffs)
    return combined_diff, updates_to_save


def main():
    print("🚀 Bắt đầu quét dữ liệu: Kiến thức AI + Top 5 Trending Git + Công cụ AI/MCP + Diễn đàn...")

    # 1. Lấy bài học hôm nay
    day_idx, lesson_info = get_current_lesson()
    lesson_dict = {"day": day_idx, **lesson_info}

    # Chế độ kiểm tra nhanh (--test)
    if "--test" in sys.argv:
        print("🧪 Đang chạy chế độ kiểm tra (TEST MODE AI ENGINEERING & MCP)...")
        sample_trending = [
            {"name": "JuliusBrussee/caveman", "stars": "104,115", "desc": "Token compression & prompt optimizer for LLM coding agents", "url": "https://github.com/JuliusBrussee/caveman"},
            {"name": "koala73/worldmonitor", "stars": "85,771", "desc": "Real-time global intelligence dashboard with AI news aggregation", "url": "https://github.com/koala73/worldmonitor"},
            {"name": "Leonxlnx/taste-skill", "stars": "85,099", "desc": "AI design heuristics skill stops AI from generating generic UI", "url": "https://github.com/Leonxlnx/taste-skill"},
            {"name": "career-ops-hq/career-ops", "stars": "70,442", "desc": "Open-source AI job search: scan job portals and evaluate matches", "url": "https://github.com/career-ops-hq/career-ops"},
            {"name": "headroomlabs-ai/headroom", "stars": "69,665", "desc": "Compress tool outputs, logs, files, and RAG chunks before model context", "url": "https://github.com/headroomlabs-ai/headroom"}
        ]
        sample_tools = """
        📦 <b>Awesome MCP Servers:</b>
        - [TomD4vs/prumo](https://github.com/TomD4vs/prumo) - Checks context files a coding agent reads (CLAUDE.md, SKILL.md, .cursor/rules) against git index.
        - [SLP-DEV1/qwen-dap-mcp](https://github.com/SLP-DEV1/qwen-dap-mcp) - DAP-to-MCP bridge that gives coding agents structured native-debugger evidence.

        📦 <b>Awesome Generative AI:</b>
        - [Cursor Router](https://cursor.com/) - Intelligent model routing system that automatically picks the right model for coding.
        - [NotebookLM Audio](https://notebooklm.google/) - Generates conversational podcasts from your uploaded documents.
        """
        sample_discussions = [
            {
                "source": "Reddit (r/LocalLLaMA)",
                "topic": "Grok",
                "score": 850,
                "title": "xAI releases Grok 3 reasoning benchmark and expanded API context window",
                "link": "https://reddit.com/r/LocalLLaMA"
            },
            {
                "source": "Hacker News",
                "topic": "Codex",
                "score": 620,
                "title": "OpenAI Codex CLI update: Real-time code editing and workspace context integration",
                "link": "https://news.ycombinator.com"
            },
            {
                "source": "Reddit (r/GoogleGeminiAI)",
                "topic": "Gemini",
                "score": 540,
                "title": "Google announces Gemini 2.5 Flash updates with enhanced speed and low-latency multimodal API",
                "link": "https://reddit.com/r/GoogleGeminiAI"
            }
        ]

        print(f"1. Đang gọi Gemini tổng hợp bài học Ngày #{day_idx} ({lesson_info['topic']}) và bản tin...")
        summary = summarize_with_gemini(lesson_dict, sample_trending, sample_tools, sample_discussions)
        print("\n--- Bản tóm tắt từ Gemini ---")
        print(summary)
        print("-----------------------------\n")

        print("2. Đang gửi vào Telegram của bạn...")
        if send_telegram_message(summary):
            print(f"\n🎉 THÀNH CÔNG! Bản tin Ngày #{day_idx} ưu tiên kiến thức AI đã gửi về Telegram!")
        else:
            print("❌ Gửi Telegram thất bại!")
            sys.exit(1)
        return

    # Chế độ chạy thật tự động
    # Quét Top 5 GitHub Trending
    print("📈 Đang lấy Top 5 AI Repos trending trên GitHub...")
    trending_repos = get_github_trending_repos()

    # Quét GitHub Awesome AI & Awesome MCP Servers
    print("⚡ Đang kiểm tra cập nhật mới từ Awesome AI & Awesome MCP Servers...")
    diff_text, updates_to_save = get_all_tracked_updates()

    # Quét Thảo luận Reddit & Hacker News
    print("🔍 Đang quét thảo luận sôi nổi từ Hacker News & Reddit (ưu tiên Grok, Codex, Gemini)...")
    hn_posts = get_hacker_news_posts()
    reddit_posts = get_reddit_posts()
    all_raw_discussions = hn_posts + reddit_posts
    all_discussions = filter_and_prioritize_discussions(all_raw_discussions, max_total=4)

    # Tổng hợp bằng Gemini
    print(f"🤖 Đang gọi Gemini tổng hợp bài học Ngày #{day_idx} và bản tin 4 phần...")
    summary = summarize_with_gemini(lesson_dict, trending_repos, diff_text, all_discussions)

    # Gửi Telegram
    if send_telegram_message(summary):
        # Lưu các SHA mới của các repo được theo dõi
        for state_file, sha in updates_to_save:
            try:
                with open(state_file, "w", encoding="utf-8") as f:
                    f.write(sha)
            except Exception as e:
                print(f"⚠️ Lỗi khi lưu state file {state_file}: {e}")

        # Tiến độ ngày học sang ngày tiếp theo
        advance_lesson_day(day_idx)
        print(f"✅ Đã gửi bản tin Ngày #{day_idx} thành công! Ngày mai sẽ học Ngày #{day_idx + 1}.")
    else:
        print("❌ Gửi Telegram thất bại!")
        sys.exit(1)


if __name__ == "__main__":
    main()
