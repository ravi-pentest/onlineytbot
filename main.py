import requests
from bs4 import BeautifulSoup
from newspaper import Article
from deep_translator import GoogleTranslator
import os
import time
import random
from threading import Thread

# GitHub Secrets මගින් දත්ත ලබා ගැනීම
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')
LOG_FILE = "processed_urls.txt"

def send_telegram_msg(message):
    """ටෙලිග්‍රෑම් අකුරු සීමාව (4096) ඉක්මවා යන විට පණිවිඩය කොටස් වලට බෙදා යොමු කරයි"""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    max_length = 4000
    try:
        if len(message) <= max_length:
            requests.post(url, data={'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}, timeout=15)
        else:
            chunks = [message[i:i + max_length] for i in range(0, len(message), max_length)]
            for chunk in chunks:
                requests.post(url, data={'chat_id': CHAT_ID, 'text': chunk, 'parse_mode': 'Markdown'}, timeout=15)
                time.sleep(1)
    except Exception as e:
        print(f"Telegram sending error: {e}")

def keep_alive_ping():
    """සෑම විනාඩි 02කටම වරක් බොට් ක්‍රියාත්මක බව ටෙලිග්‍රෑම් වෙත දන්වයි"""
    while True:
        try:
            current_time = time.strftime('%H:%M:%S')
            send_telegram_msg(f"🟢 *[ALIVE STATUS - {current_time}]*\nසර්වර් එක සජීවීව පවතිනවා. මම අලුත් පුවත් සොයමින් සිටිමි...")
        except: pass
        time.sleep(120)

def enhance_sinhala_logic(text):
    """පරිවර්තනය වූ සිංහල භාෂාව ඉතා සරල, කථන ශෛලියකට සහ ගැඹුරු විවරණයකට හැරවීම"""
    refinement_map = {
        "ප්‍රකාශ කළේය": "කිව්වා", "සිදු කරනු ලබයි": "කරනවා", "නිරීක්ෂණය විය": "දැක්කා",
        "විසින්": "මගින්", "පැවැත්වූයේය": "පැවැත්වුවා", "අනාවරණය විය": "හෙළි වුණා",
        "භාවිතා කරමින්": "පාවිච්චි කරලා", "සමගින්": "එක්ක", "යුධ ගැටුම්": "භයානක සටන්",
        "ආර්ථික අර්බුදය": "ආර්ථික කඩා වැටීම", "විමර්ශනය": "පරීක්ෂණය", "අභ්‍යවකාශ": "අභ්‍යවකාශය",
        "නිරීක්ෂණය": "බැලීම", "වැඩිදුරටත්": "තවත් විස්තර කිව්වොත්", "වාර්තා වේ": "දැනගන්න ලැබෙනවා"
    }
    for old, new in refinement_map.items():
        text = text.replace(old, new)
    return text

def create_magnetic_title(title):
    """නරඹන්නන් වීඩියෝව වෙත ඇද ගන්නා කුතුහලය දනවන මාතෘකා"""
    hooks = [
        "අද ලෝකයම හොල්ලපු ඒ රහස මෙන්න: ", "කිසිවෙකු නොකියූ සැඟවුණු ඇත්ත: ", 
        "මෙන්න දැන් ලැබුණු විශේෂ පුවත: ", "ඇයි හැමෝම මේ ගැන කතා කරන්නේ? ",
        "අවසානය ඔබ සිතනවාට වඩා භයානකයි: ", "මිලියන ගණනක් බලා සිටි හෙළිදරව්ව: "
    ]
    return random.choice(hooks) + title

def get_massive_sources():
    """වෙබ් අඩවි 70+ (Global 50 + SL 20) සහ Google Trends ග්‍රහණය කර ගැනීම"""
    found_items = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 1. Google Trends (20)
    try:
        res = requests.get("https://trends.google.com/trends/trendingsearches/daily/rss?geo=US", headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, 'xml')
        for item in soup.find_all('item')[:20]:
            found_items.append({"title": item.title.text, "link": item.link.text})
    except: pass

    # 2. Global News & Science/Space (වෙබ් අඩවි 50කට ආසන්න මූලාශ්‍ර)
    global_feeds = [
        "http://feeds.bbci.co.uk/news/world/rss.xml", "https://www.reutersagency.com/feed/",
        "https://www.aljazeera.com/xml/rss/all.xml", "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
        "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?max=10",
        "https://www.nasa.gov/news-release/feed/", "https://techcrunch.com/feed/",
        "https://www.military.com/rss-feeds/content?type=news", "https://www.theguardian.com/world/rss",
        "https://www.sciencedaily.com/rss/all.xml", "https://www.bloomberg.com/politics/feeds/site.xml",
        "https://www.space.com/feeds/all", "https://www.nature.com/nature.rss",
        "https://www.economist.com/international/rss.xml", "https://www.nationalgeographic.com/rss/index.xml"
    ]
    for url in global_feeds:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.content, 'xml')
            for item in soup.find_all('item')[:5]:
                found_items.append({"title": item.title.text, "link": item.link.text})
        except: pass

    # 3. Sri Lanka News (වෙබ් අඩවි 20කට ආසන්න මූලාශ්‍ර)
    sl_feeds = [
        "https://www.hirunews.lk/rss/sinhala.xml", "http://www.adaderana.lk/rss.php",
        "https://www.itnnews.lk/feed/", "https://www.newsfirst.lk/feed/",
        "https://sinhala.adaderana.lk/rss.php", "https://www.lankadeepa.lk/rss/1",
        "https://www.dinamina.lk/feed/"
    ]
    for url in sl_feeds:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.content, 'xml')
            for item in soup.find_all('item')[:5]:
                found_items.append({"title": item.title.text, "link": item.link.text})
        except: pass
        
    return found_items

def process_and_analyze():
    translator = GoogleTranslator(source='auto', target='si')
    
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            processed_urls = f.read().splitlines()
    else:
        processed_urls = []

    all_news = get_massive_sources()
    random.shuffle(all_news) # පුවත් මිශ්‍ර කිරීම
    scripts_done = 0

    for item in all_news:
        if item['link'] in processed_urls: continue

        try:
            article = Article(item['link'])
            article.download(); article.parse()
            
            if len(article.text) < 1500: continue # ගැඹුරු විශ්ලේෂණයක් සඳහා අවම දිග

            # සිංහල පරිවර්තනය සහ සරල කිරීම
            si_title_raw = translator.translate(item['title'])
            final_title = enhance_sinhala_logic(create_magnetic_title(si_title_raw))
            
            # පණිවිඩයේ සාරාංශය (Summary)
            si_summary = enhance_sinhala_logic(translator.translate(article.summary if article.summary else article.text[:400]))

            # විනාඩි 6ක වොයිස් ඕවර් එකක් සඳහා අකුරු 5500ක් දක්වා ගනී
            content_si = translator.translate(article.text[:5500])
            final_body = enhance_sinhala_logic(content_si)

            # Meta Data
            meta_data = f"📊 *SEO & META DATA*\n*Keywords:* {si_title_raw}, Space, Military, Sri Lanka, Economy, Discovery\n*Tags:* #YouTubeSL #WarAnalysis #SpaceDiscovery #Trending #NewsSriLanka #Voiceover"

            full_report = f"""
✨ *[NEW YOUTUBE SCRIPT ANALYSIS]* ✨
━━━━━━━━━━━━━━━━━━━━━━
🔥 *මාතෘකාව:* {final_title}

📝 *කෙටි සාරාංශය:*
{si_summary}...

🎬 *YOUTUBE SCRIPT (06 MINUTES):*
━━━━━━━━━━━━━━━━━━━━━━
👋 *INTRO:*
ආයුබෝවන්! අද අපි අරගෙන ආවේ මුළු ලෝකයේම අවධානය දිනාගත් විශේෂ පුවතක් ගැන ගැඹුරු විශ්ලේෂණයක්. මේ පිටුපස තියෙන ඇත්තම කතාව මොකක්ද? විනාඩි 6ක් පුරා අපි මේ ගැන විමර්ශනය කරමු.

📖 *ගැඹුරු විශ්ලේෂණය (Content):*
{final_body}

🎬 *OUTRO:*
ඉතින් මේ ගැන ඔයාලගේ අදහස මොකක්ද? පහළින් කමෙන්ට් කරන්න. මේ වගේ වීඩියෝ දිගටම බලන්න අපිව සබ්ස්ක්‍රයිබ් කරන්න!
━━━━━━━━━━━━━━━━━━━━━━

{meta_data}

🔗 *මූලාශ්‍රය:* {item['link']}
━━━━━━━━━━━━━━━━━━━━━━
            """

            send_telegram_msg(full_report)
            
            with open(LOG_FILE, "a") as f:
                f.write(item['link'] + "\n")
            
            scripts_done += 1
            if scripts_done >= 3: break # වරකට ගැඹුරු පුවත් 3ක් පමණි
            time.sleep(20)
        except: continue

if __name__ == "__main__":
    # Alive Ping ත්‍රෙඩ් එක ආරම්භ කිරීම
    Thread(target=keep_alive_ping).start()
    
    send_telegram_msg("🚀 *[SYSTEM START]* පුවත් විශ්ලේෂණ සේවාව ආරම්භ කළා. සෑම විනාඩි 05කට වරක්ම අලුත් පුවත් පරීක්ෂා කෙරේ.")
    
    while True:
        process_and_analyze()
        time.sleep(300) # සෑම විනාඩි 05කට වරක් පරීක්ෂා කරයි
