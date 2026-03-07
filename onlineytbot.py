import requests
from bs4 import BeautifulSoup
from newspaper import Article
from deep_translator import GoogleTranslator
import os
import time
import schedule
import re
from flask import Flask
from threading import Thread

# --- 1. Render සඳහා Web Server සැකසුම ---
app = Flask('')

@app.route('/')
def home():
    return "YouTube News Bot is Running!"

def run_server():
    # Render සාමාන්‍යයෙන් PORT එකක් ලබා දෙයි, නැතිනම් 10000 භාවිතා කරයි
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.start()

# --- 2. සැකසුම් ---
TELEGRAM_TOKEN = '8761743193:AAGL6gMzbuHLxbf0cxQChXSjXs0BeWwO6yk'
CHAT_ID = '8610552803'

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        if len(message) > 4000:
            for i in range(0, len(message), 4000):
                requests.post(url, data={'chat_id': CHAT_ID, 'text': message[i:i+4000], 'parse_mode': 'Markdown'}, timeout=10)
        else:
            requests.post(url, data={'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}, timeout=10)
    except:
        requests.post(url, data={'chat_id': CHAT_ID, 'text': message}, timeout=10)

def simplify_sinhala(text):
    replacements = {
        "ප්‍රකාශ කළේය": "කිව්වා",
        "සිදු කරනු ලබයි": "කරනවා",
        "නිරීක්ෂණය කරන ලදී": "දැකගන්න ලැබුණා",
        "භාවිතා කරමින්": "පාවිච්චි කරලා",
        "සමගින්": "එක්ක",
        "පැවැත්වූයේය": "පැවැත්වුවා",
        "විසින්": "මගින්",
        "නිරත විය": "යෙදුණා",
        "අනාවරණය විය": "හෙළි වුණා"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    sentences = text.split('.')
    simplified = [s.strip() for s in sentences if len(s.strip()) > 5]
    return ".\n\n".join(simplified)

def setup_bot():
    translator = GoogleTranslator(source='auto', target='si')
    log_file = 'processed_urls.txt'
    if not os.path.exists(log_file):
        with open(log_file, 'w') as f: pass
    return translator, log_file

def get_massive_sources():
    send_telegram_msg("🔍 *[INFO]* ගෝලීය පුවත් සහ Trends පරීක්ෂාව ආරම්භ කළා...")
    found_items = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        trend_url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
        res = requests.get(trend_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, 'xml')
        for item in soup.find_all('item')[:20]:
            title = item.title.text
            link = item.find('ht:news_item_url').text if item.find('ht:news_item_url') else item.link.text
            found_items.append({"title": f"🔥 TRENDING: {title}", "link": link})
    except: pass

    mega_sources = [
        "https://www.reuters.com/world/", "https://www.bbc.com/news/world", 
        "https://www.aljazeera.com/news/", "https://www.defense.gov/News/",
        "https://www.nasa.gov/news-release/", "https://www.techcrunch.com/",
        "https://www.bloomberg.com/world", "https://www.military.com/daily-news"
    ]

    for url in mega_sources:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                t = a.text.strip()
                if len(t) > 65:
                    l = a['href']
                    if not l.startswith('http'): l = f"https://{url.split('/')[2]}{l}"
                    found_items.append({"title": t, "link": l})
                    if len(found_items) > 60: break
        except: continue
    return found_items

def process_and_send():
    send_telegram_msg("⚡ *[START]* නව YouTube ස්ක්‍රිප්ට් එක සකසමින් පවතී...")
    translator, log_file = setup_bot()
    all_data = get_massive_sources()
    
    with open(log_file, 'r', encoding='utf-8') as f: processed = f.read()
    new_count = 0

    for item in all_data:
        if item['link'] in processed: continue
        
        try:
            article = Article(item['link'])
            article.download(); article.parse()
            if len(article.text) < 600: continue

            final_title = simplify_sinhala(translator.translate(item['title']))
            final_content = simplify_sinhala(translator.translate(article.text[:3500]))

            keywords = f"{final_title}, News, Trending, World News, Today News"
            tags = "#News #Trending #YouTubeSL #WorldNews #BreakingNews"

            full_message = f"""
🎥 *YOUTUBE VOICE-OVER SCRIPT*
━━━━━━━━━━━━━━━━━━━━━━
🔴 *වීඩියෝ මාතෘකාව:* {final_title}

👋 *හඳුන්වාදීම (Intro):*
ආයුබෝවන් හැමෝටම! අද අපි අරගෙන ආවේ ලෝකයේ විශාල අවධානයක් දිනාගත් විශේෂ පුවතක්. මේ ගැන දැනගන්න වීඩියෝව අවසානය දක්වාම රැඳී සිටින්න්න.

📝 *ප්‍රධාන අන්තර්ගතය (Main Content):*
{final_content}

🎬 *අවසානය (Outro):*
ඉතින් මේ විශේෂ පුවත ගැන ඔයාලට මොකද හිතෙන්නේ? පල්ලෙහායින් කමෙන්ට් කරන්න. මේ වගේ තවත් තොරතුරු දැනගන්න අපේ චැනල් එක සබ්ස්ක්‍රයිබ් කරන්න අමතක කරන්න එපා. ස්තූතියි!

━━━━━━━━━━━━━━━━━━━━━━
📊 *YOUTUBE META DATA*
━━━━━━━━━━━━━━━━━━━━━━
🔑 *Keywords:*
{keywords}

🏷️ *Tags:*
{tags}

🔗 *Original Source:* {item['link']}
━━━━━━━━━━━━━━━━━━━━━━
            """

            send_telegram_msg(full_message)
            
            with open(log_file, 'a', encoding='utf-8') as f: f.write(item['link'] + '\n')
            new_count += 1
            if new_count >= 10: break 
            time.sleep(5) 
        except: continue
    
    send_telegram_msg(f"✅ *[FINISH]* වටය අවසන්. අලුත් ස්ක්‍රිප්ට් {new_count} ක් ලබා දුන්නා.")

# --- 3. ධාවනය කිරීම ---
if __name__ == "__main__":
    # Render සර්වර් එක පණ ගැන්වීම
    keep_alive()
    
    send_telegram_msg("🚀 Bot is now LIVE on Render 24/7!")
    process_and_send()
    
    schedule.every(10).minutes.do(process_and_send)
    
    while True:
        schedule.run_pending()
        time.sleep(1)