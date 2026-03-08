import requests
from bs4 import BeautifulSoup
from newspaper import Article
from deep_translator import GoogleTranslator
import os
import time
import schedule
import re
import random
from flask import Flask
from threading import Thread

# --- 1. Web Server for 24/7 Hosting ---
app = Flask('')

@app.route('/')
def home():
    return "YouTube News Bot is Running!"

def run_server():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_server)
    t.daemon = True
    t.start()

# --- 2. Configuration & Settings ---
TELEGRAM_TOKEN = '8761743193:AAGL6gMzbuHLxbf0cxQChXSjXs0BeWwO6yk'
CHAT_ID = '8610552803'
LOG_FILE = 'processed_urls.txt'

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    max_len = 4000
    try:
        if len(message) > max_len:
            chunks = [message[i:i+max_len] for i in range(0, len(message), max_len)]
            for chunk in chunks:
                requests.post(url, data={'chat_id': CHAT_ID, 'text': chunk, 'parse_mode': 'Markdown'}, timeout=15)
        else:
            requests.post(url, data={'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}, timeout=15)
    except:
        requests.post(url, data={'chat_id': CHAT_ID, 'text': message}, timeout=15)

def live_status_ping():
    """සෑම විනාඩි 02කටම වරක් බොට් සක්‍රීය බව පෙන්වයි"""
    while True:
        try:
            send_telegram_msg("🟢 *[LIVE STATUS]* පද්ධතිය සජීවීව පවතිනවා. අලුත් පුවත් ගවේෂණය කරමින් සිටිමි...")
        except: pass
        time.sleep(120)

def advanced_sinhala_refine(text):
    """පරිවර්තනය වූ සිංහල වඩාත් සරල සහ ස්වාභාවික කථන ශෛලියකට හැරවීම"""
    replacements = {
        "ප්‍රකාශ කළේය": "පැවසුවා", "සිදු කරනු ලබයි": "කරනවා", "නිරීක්ෂණය විය": "දැකගන්න ලැබුණා",
        "භාවිතා කරමින්": "පාවිච්චි කරලා", "සමගින්": "එක්ක", "විසින්": "මගින්",
        "අනාවරණය විය": "හෙළි වුණා", "වාර්තා වේ": "දැනගන්න ලැබෙනවා", "සඳහා": "වෙනුවෙන්",
        "යුධ ගැටුම්": "භයානක සටන්", "ආර්ථික": "සල්ලි සහ ආර්ථික", "අභ්‍යවකාශ": "අභ්‍යවකාශය",
        "ගවේෂණය": "සොයා බැලීම"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def create_clickbait_title(title):
    hooks = ["ලෝකයම කැළඹූ රහස මෙන්න: ", "කිසිවෙකු නොකියූ සැඟවුණු ඇත්ත: ", "අවසානය වෙනස්ම එකක්: ", "විශේෂ හෙළිදරව්ව: "]
    return random.choice(hooks) + title

# --- 3. News Scrapers ---
def get_sources():
    found_items = []
    headers = {'User-Agent': 'Mozilla/5.0'}

    # 1. Google Trends (20)
    try:
        res = requests.get("https://trends.google.com/trends/trendingsearches/daily/rss?geo=US", headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, 'xml')
        for item in soup.find_all('item')[:20]:
            found_items.append({"title": item.title.text, "link": item.link.text, "cat": "Trend"})
    except: pass

    # 2. Sri Lanka Sinhala News (වෙබ් අඩවි 20ක් පමණ ආවරණය වන RSS)
    sl_rss = [
        "https://www.hirunews.lk/rss/sinhala.xml", "http://www.adaderana.lk/rss.php",
        "https://www.itnnews.lk/feed/", "https://www.newsfirst.lk/feed/",
        "https://sinhala.adaderana.lk/rss.php", "https://www.lankadeepa.lk/rss/1",
        "https://www.dinamina.lk/feed/", "https://www.silumina.lk/feed/"
    ]
    for url in sl_rss:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.content, 'xml')
            for item in soup.find_all('item')[:5]:
                found_items.append({"title": item.title.text, "link": item.link.text, "cat": "SL"})
        except: pass

    # 3. Global News (වෙබ් අඩවි 50ක් පමණ ආවරණය වන ලැයිස්තුව)
    global_urls = [
        "http://feeds.bbci.co.uk/news/world/rss.xml", "https://www.reutersagency.com/feed/",
        "https://www.aljazeera.com/xml/rss/all.xml", "https://www.nasa.gov/news-release/feed/",
        "https://techcrunch.com/feed/", "https://www.military.com/rss-feeds/content?type=news",
        "https://www.sciencedaily.com/rss/all.xml", "https://www.space.com/feeds/all"
    ]
    for url in global_urls:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.content, 'xml')
            for item in soup.find_all('item')[:10]:
                found_items.append({"title": item.title.text, "link": item.link.text, "cat": "Global"})
        except: pass

    return found_items

def process_and_send():
    translator = GoogleTranslator(source='auto', target='si')
    if not os.path.exists(LOG_FILE): 
        with open(LOG_FILE, 'w') as f: pass
    
    with open(LOG_FILE, 'r') as f: processed = f.read()
    
    all_data = get_sources()
    random.shuffle(all_data)
    new_count = 0

    for item in all_data:
        if item['link'] in processed: continue
        
        try:
            article = Article(item['link'])
            article.download(); article.parse()
            if len(article.text) < 800: continue

            # පුවත් විශ්ලේෂණය සහ පරිවර්තනය
            raw_title_si = translator.translate(item['title'])
            final_title = advanced_sinhala_refine(create_clickbait_title(raw_title_si))
            
            # විනාඩි 6ක වොයිස් ඕවර් එකක් සඳහා අකුරු 5000ක්
            body_si = translator.translate(article.text[:5000])
            final_body = advanced_sinhala_refine(body_si)
            
            summary_si = advanced_sinhala_refine(translator.translate(article.text[:400]))

            script = f"""
✨ *[NEW CONTENT ANALYSIS]* ✨
━━━━━━━━━━━━━━━━━━━━━━
🔥 *මාතෘකාව:* {final_title}

📝 *සාරාංශය:*
{summary_si}...

🎬 *YOUTUBE SCRIPT (06 MINS):*
━━━━━━━━━━━━━━━━━━━━━━
👋 *INTRO:*
ආයුබෝවන්! අද අපි අරගෙන ආවේ ලෝකයේ විශාල අවධානයක් දිනාගත් විශේෂ සිදුවීමක්. මේ පිටුපස තියෙන ඇත්තම කතාව මොකක්ද? විනාඩි 6ක් පුරා අපි මේ ගැන ගැඹුරින් සොයා බලමු.

📖 *විස්තරය (Main Content):*
{final_body}

🎬 *OUTRO:*
ඉතින් මේ ගැන ඔයාලට මොකද හිතෙන්නේ? පල්ලෙහායින් කමෙන්ට් කරන්න. මේ වගේ වීඩියෝ දිගටම බලන්න අපිව සබ්ස්ක්‍රයිබ් කරන්න!

━━━━━━━━━━━━━━━━━━━━━━
📊 *SEO META DATA*
━━━━━━━━━━━━━━━━━━━━━━
🔑 *Keywords:* {raw_title_si}, Discovery, War News, Economy, SL News
🏷️ *Tags:* #News #Trending #YouTubeSL #Analysis #Space #War
🔗 *Source:* {item['link']}
━━━━━━━━━━━━━━━━━━━━━━
            """
            send_telegram_msg(script)
            with open(LOG_FILE, 'a') as f: f.write(item['link'] + '\n')
            new_count += 1
            if new_count >= 5: break
            time.sleep(10)
        except: continue

# --- 4. Main Execution ---
if __name__ == "__main__":
    keep_alive()
    Thread(target=live_status_ping, daemon=True).start()
    
    send_telegram_msg("🚀 *[SYSTEM START]* පද්ධතිය සාර්ථකව පණ ගැන්වුණා. සෑම විනාඩි 05කට වරක්ම නව පුවත් පරීක්ෂා කෙරේ.")
    
    schedule.every(5).minutes.do(process_and_send)
    
    process_and_send() # මුල්ම වතාවට ධාවනය
    while True:
        schedule.run_pending()
        time.sleep(1)
