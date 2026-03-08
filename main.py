import requests
from bs4 import BeautifulSoup
from newspaper import Article
from deep_translator import GoogleTranslator
import os
import time
import random
import re
from threading import Thread

# GitHub Secrets මගින් දත්ත ලබා ගැනීම
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
LOG_FILE = "processed_urls.txt"

def send_telegram_msg(message):
    """ටෙලිග්‍රෑම් අකුරු සීමාව ඉක්මවා යන විට පණිවිඩය කඩා යොමු කරයි"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    max_length = 4000
    
    if len(message) <= max_length:
        requests.post(url, data={'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}, timeout=15)
    else:
        # අකුරු සීමාව ඉක්මවන්නේ නම් පණිවිඩය කොටස් වලට බෙදීම
        chunks = [message[i:i + max_length] for i in range(0, len(message), max_length)]
        for chunk in chunks:
            requests.post(url, data={'chat_id': CHAT_ID, 'text': chunk, 'parse_mode': 'Markdown'}, timeout=15)
            time.sleep(1)

def keep_alive_ping():
    """සෑම විනාඩි 02කටම වරක් බොට් ක්‍රියාත්මක බව ටෙලිග්‍රෑම් වෙත දන්වයි"""
    while True:
        try:
            send_telegram_msg("🟢 *[LIVE STATUS]* පද්ධතිය සක්‍රීයයි. මම පුවත් ගවේෂණය කරමින් සිටිමි...")
        except: pass
        time.sleep(120)

def enhance_sinhala(text):
    """පරිවර්තනය වූ සිංහල තවදුරටත් සරල, කථන ශෛලියකට සහ ගැඹුරු විශ්ලේෂණාත්මක ස්වරූපයකට හැරවීම"""
    # වඩාත් ස්වභාවික සිංහල වචන භාවිතය
    refinement_map = {
        "ප්‍රකාශ කළේය": "පැවසුවා", "සිදු කරනු ලබයි": "කරනවා", "නිරීක්ෂණය විය": "පෙනෙන්නට තිබුණා",
        "විසින්": "මගින්", "පැවැත්වූයේය": "පැවැත්වුවා", "අනාවරණය විය": "හෙළි වුණා",
        "භාවිතා කරමින්": "පාවිච්චි කරලා", "සමගින්": "එක්ක", "යුධ ගැටුම්": "භයානක සටන්",
        "ආර්ථික අර්බුදය": "ආර්ථික කඩා වැටීම", "විමර්ශනය": "ගැඹුරු පරීක්ෂණය", 
        "සැලකිය යුතු": "ගොඩක් ලොකු", "වැඩිදුරටත්": "තවත් විස්තර කියනවා නම්",
        "වාර්තා වේ": "දැනගන්න ලැබෙනවා", "පවතින": "තියෙන", "සඳහා": "වෙනුවෙන්"
    }
    for old, new in refinement_map.items():
        text = text.replace(old, new)
    
    # වාක්‍ය ආරම්භය වඩාත් ආකර්ෂණීය කිරීම
    text = text.replace("එය", "මේ සිදුවීම").replace("ඔහු", "මෙම පුද්ගලයා")
    return text

def create_magnetic_title(title):
    """නරඹන්නාගේ කුතුහලය උපරිම කරන ආකර්ෂණීය මාතෘකා සැකසීම"""
    hooks = [
        "ලෝකයම හොල්ලපු ඒ රහස මෙන්න: ", "සැඟවුණු ඇත්ත එළියට එයි! ", "ඔබ මීට පෙර නොඇසූ: ",
        "කාටවත් කියන්න එපා! ", "විශේෂ හෙළිදරව්ව: ", "අද දවසේ භයානකම පුවත: ",
        "ඇයි හැමෝම මේ ගැන කතා කරන්නේ? ", "අවසානය ඔබ සිතනවාට වඩා වෙනස්: "
    ]
    return random.choice(hooks) + title

def get_mega_sources():
    """අඩවි 20+, Google Trends 20 සහ SL Trends එකතු කිරීම"""
    found_items = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 1. Google Trends (20 items)
    try:
        res = requests.get("https://trends.google.com/trends/trendingsearches/daily/rss?geo=US", headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, 'xml')
        for item in soup.find_all('item')[:20]:
            found_items.append({"title": item.title.text, "link": item.link.text})
    except: pass

    # 2. Global News & War Analysis (ලෝක ප්‍රකට පුවත් RSS 10+)
    mega_feeds = [
        "http://feeds.bbci.co.uk/news/world/rss.xml", "https://www.reutersagency.com/feed/",
        "https://www.aljazeera.com/xml/rss/all.xml", "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
        "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?max=10",
        "https://www.nasa.gov/news-release/feed/", "https://techcrunch.com/feed/",
        "https://www.military.com/rss-feeds/content?type=news", "https://www.theguardian.com/world/rss",
        "https://www.sciencedaily.com/rss/all.xml", "https://www.bloomberg.com/politics/feeds/site.xml"
    ]
    for url in mega_feeds:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.content, 'xml')
            for item in soup.find_all('item')[:5]:
                found_items.append({"title": item.title.text, "link": item.link.text})
        except: pass

    # 3. Sri Lanka Trends (Top 5)
    sl_feeds = ["https://www.hirunews.lk/rss/sinhala.xml", "http://www.adaderana.lk/rss.php"]
    for url in sl_feeds:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.content, 'xml')
            for item in soup.find_all('item')[:3]:
                found_items.append({"title": item.title.text, "link": item.link.text})
        except: pass
        
    return found_items

def process_and_analyze():
    translator = GoogleTranslator(source='auto', target='si')
    
    # ලොග් කියවීම (Duplicates වැළැක්වීමට)
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            processed_urls = f.read().splitlines()
    else:
        processed_urls = []

    all_data = get_mega_sources()
    scripts_done = 0

    for item in all_data:
        if item['link'] in processed_urls: continue

        try:
            article = Article(item['link'])
            article.download(); article.parse()
            
            # විනාඩි 6ක වොයිස් ඕවර් එකක් සඳහා අකුරු 1500කට වඩා තිබිය යුතුයි
            if len(article.text) < 1500: continue

            # සිංහලට පරිවර්තනය සහ ගුණාත්මක බව වැඩි කිරීම
            raw_title_si = translator.translate(item['title'])
            final_title = enhance_sinhala(create_magnetic_title(raw_title_si))
            
            # ගැඹුරු යුධ/ආර්ථික විශ්ලේෂණයක් සඳහා අකුරු 5000ක් දක්වා ගනී
            body_chunks = [article.text[i:i+4500] for i in range(0, len(article.text), 4500)][0]
            body_si = translator.translate(body_chunks)
            final_body = enhance_sinhala(body_si)

            # YouTube Meta Data
            meta_data = f"📊 *SEO META DATA*\n*Keywords:* {raw_title_si}, World Affairs, Military Strategy, Technology News, SL News\n*Tags:* #WarAnalysis #TrendingNews #YouTubeSinhala #GlobalPolitics #Voiceover"

            full_script = f"""
🎬 *YOUTUBE 06-MINUTE VIDEO SCRIPT*
━━━━━━━━━━━━━━━━━━━━━━
🔴 *වීඩියෝ මාතෘකාව:* {final_title}

👋 *Intro (අවධානය දිනාගැනීම):*
ආයුබෝවන්! අද අපි කතා කරන්නේ ලෝකයම උඩුයටිකුරු කළ හැකි භයානක සිදුවීමක් ගැන. මේ පිටුපස තියෙන ඇත්තම කතාව මොකක්ද? විනාඩි 6ක් පුරා අපි මේ ගැන ගැඹුරින් විමර්ශනය කරමු.

📖 *විශ්ලේෂණය (Deep Content):*
{final_body}

🎬 *Outro:*
ඉතින් මේ ගැන ඔයාලගේ අදහස මොකක්ද? යුධමය තත්ත්වය හෝ ආර්ථිකය ගැන ඔබේ අදහස පහළින් කමෙන්ට් කරන්න. මේ වගේ ගැඹුරු විශ්ලේෂණ දිගටම බලන්න අපිව සබ්ස්ක්‍රයිබ් කරන්න!

━━━━━━━━━━━━━━━━━━━━━━
{meta_data}

🔗 *මූලාශ්‍රය:* {item['link']}
━━━━━━━━━━━━━━━━━━━━━━
            """

            send_telegram_msg(full_script)
            
            # ලින්ක් එක සේව් කිරීම
            with open(LOG_FILE, "a") as f:
                f.write(item['link'] + "\n")
            
            scripts_done += 1
            if scripts_done >= 5: break 
            time.sleep(15) # Rate limiting
        except: continue

if __name__ == "__main__":
    # Alive Ping එක වෙනම ධාවනය කිරීම
    Thread(target=keep_alive_ping).start()
    
    send_telegram_msg("🚀 *[SYSTEM START]* පුවත් ගවේෂණය සහ Script සෑදීම ආරම්භ කළා...")
    
    while True:
        process_and_analyze()
        time.sleep(1800) # සෑම විනාඩි 30කට වරක් නව පුවත් සොයයි
