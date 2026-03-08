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
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        if len(message) > 4000:
            for i in range(0, len(message), 4000):
                requests.post(url, data={'chat_id': CHAT_ID, 'text': message[i:i+4000], 'parse_mode': 'Markdown'}, timeout=15)
        else:
            requests.post(url, data={'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}, timeout=15)
    except:
        requests.post(url, data={'chat_id': CHAT_ID, 'text': message}, timeout=15)

def keep_alive_ping():
    """සෑම විනාඩි 02කටම වරක් බොට් ක්‍රියාත්මක බව ටෙලිග්‍රෑම් වෙත දන්වයි"""
    while True:
        send_telegram_msg("🟢 *[SYSTEM CHECK]* බොට් පද්ධතිය සක්‍රීයව පවතිනවා (24/7 Live Status)...")
        time.sleep(120) # තත්පර 120 (විනාඩි 02)

def simplify_sinhala(text):
    """පරිවර්තනය වූ සිංහල සරල කථන ශෛලියකට සහ විශ්ලේෂණාත්මක ස්වරූපයකට හැරවීම"""
    replacements = {
        "ප්‍රකාශ කළේය": "පැවසුවා", "සිදු කරනු ලබයි": "කරනවා", "නිරීක්ෂණය විය": "දැකගන්න ලැබුණා",
        "විසින්": "මගින්", "පැවැත්වූයේය": "පැවැත්වුවා", "අනාවරණය විය": "හෙළි වුණා",
        "භාවිතා කරමින්": "පාවිච්චි කරලා", "සමගින්": "එක්ක", "යුධ ගැටුම්": "සටන්",
        "ආර්ථික අර්බුදය": "සල්ලි ප්‍රශ්න", "විමර්ශනය": "පරීක්ෂණය", "අවස්ථාවන්හිදී": "වෙලාවල් වලදී"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def create_clickbait_title(title):
    """කුතුහලය දනවන සහ නරඹන්නා පොළඹවන මාතෘකා සැකසීම"""
    hooks = [
        "ලෝකයම කැළඹූ රහස මෙන්න: ", "අවසානයේදී ඇත්ත හෙළිවෙයි! ", "මේක අහලවත් තිබුණද? ",
        "කාටවත් කියන්න එපා! ", "විශේෂ හෙළිදරව්ව: ", "අද දවසේ උණුසුම්ම පුවත: ",
        "මීට පෙර කිසිවෙකු නොකී ඇත්ත: "
    ]
    return random.choice(hooks) + title

def get_sources():
    """ලොව ප්‍රමුඛ අඩවි 20+, Google Trends 20 සහ ලංකාවේ Trends එකතු කිරීම"""
    found_items = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # Google Trends (20 items)
    try:
        res = requests.get("https://trends.google.com/trends/trendingsearches/daily/rss?geo=US", headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, 'xml')
        for item in soup.find_all('item')[:20]:
            found_items.append({"title": item.title.text, "link": item.link.text, "type": "Trending"})
    except: pass

    # Global Media & War/Economic News (වෙබ් අඩවි 20ක් පමණ)
    mega_feeds = [
        "http://feeds.bbci.co.uk/news/world/rss.xml", "https://www.reutersagency.com/feed/",
        "https://www.aljazeera.com/xml/rss/all.xml", "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
        "https://www.defense.gov/DesktopModules/ArticleCS/RSS.ashx?max=10",
        "https://www.nasa.gov/news-release/feed/", "https://techcrunch.com/feed/",
        "https://www.military.com/rss-feeds/content?type=news", "https://www.theguardian.com/world/rss",
        "https://www.sciencedaily.com/rss/all.xml"
    ]
    for url in mega_feeds:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.content, 'xml')
            for item in soup.find_all('item')[:10]:
                found_items.append({"title": item.title.text, "link": item.link.text, "type": "Analysis"})
        except: pass

    # Sri Lanka Trends (Top 5)
    sl_feeds = ["https://www.hirunews.lk/rss/sinhala.xml", "http://www.adaderana.lk/rss.php"]
    for url in sl_feeds:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.content, 'xml')
            for item in soup.find_all('item')[:3]:
                found_items.append({"title": item.title.text, "link": item.link.text, "type": "SL_Trend"})
        except: pass
        
    return found_items

def process_and_send():
    translator = GoogleTranslator(source='auto', target='si')
    
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            processed_urls = f.read().splitlines()
    else:
        processed_urls = []

    all_data = get_sources()
    new_scripts_count = 0

    for item in all_data:
        if item['link'] in processed_urls:
            continue

        try:
            article = Article(item['link'])
            article.download(); article.parse()
            
            # විනාඩි 6ක වොයිස් ඕවර් එකක් සඳහා දීර්ඝ අන්තර්ගතයක් අවශ්‍යයි
            if len(article.text) < 1200: continue

            # සිංහලට පරිවර්තනය සහ සරල කිරීම
            translated_title = translator.translate(item['title'])
            final_title = simplify_sinhala(create_clickbait_title(translated_title))
            
            # ගැඹුරු විශ්ලේෂණයක් සඳහා අකුරු 5000ක් දක්වා ගනී
            body_si = translator.translate(article.text[:5000])
            final_body = simplify_sinhala(body_si)

            # SEO Meta Data
            meta_data = f"Keywords: {translated_title}, War News, Economy, SL Trends, Technology\nTags: #Trending #WarAnalysis #Voiceover #YouTubeSL #BreakingNews"

            full_script = f"""
🎬 *YOUTUBE 06-MINUTE VIDEO SCRIPT*
━━━━━━━━━━━━━━━━━━━━━━
🔴 *වීඩියෝ මාතෘකාව:* {final_title}

👋 *Intro (කුතුහලය දනවන ආරම්භය):*
ආයුබෝවන්! අද අපි කතා කරන්නේ මුළු ලෝකයේම අවධානය දිනාගත්, නමුත් බොහෝ දෙනෙක් ගැඹුරින් නොදන්නා විශේෂ පුවතක් ගැන. මේ වීඩියෝව අවසාන වෙනකොට ඔබ කිසිසේත්ම බලාපොරොත්තු නොවන දෙයක් දැනගන්න ලැබේවි.

📝 *ගැඹුරු විශ්ලේෂණය (Main Content):*
{final_body}

🎬 *අවසානය (Call to Action):*
ඉතින් මේ සිදුවීම ගැන ඔබ හිතන්නේ මොකක්ද? යුධමය තත්ත්වය හෝ ආර්ථිකය ගැන ඔබේ අදහස පහළින් කමෙන්ට් කරන්න. මේ වගේ ගැඹුරු විශ්ලේෂණ දිගටම බලන්න අපිව සබ්ස්ක්‍රයිබ් කරන්න!

━━━━━━━━━━━━━━━━━━━━━━
📊 *SEO & META DATA*
━━━━━━━━━━━━━━━━━━━━━━
{meta_data}

🔗 *Original Source:* {item['link']}
━━━━━━━━━━━━━━━━━━━━━━
            """

            send_telegram_msg(full_script)
            
            # ලින්ක් එක සේව් කිරීම (නැවත පළ කිරීම වැළැක්වීමට)
            with open(LOG_FILE, "a") as f:
                f.write(item['link'] + "\n")
            
            new_scripts_count += 1
            if new_scripts_count >= 3: break # වරකට ගැඹුරු ස්ක්‍රිප්ට් 3ක් පමණක් සකසයි
            time.sleep(10)
        except:
            continue

if __name__ == "__main__":
    # "Alive" පණිවිඩය වෙනම ත්‍රෙඩ් එකක ක්‍රියාත්මක කිරීම
    Thread(target=keep_alive_ping).start()
    
    send_telegram_msg("🚀 *[SYSTEM START]* පුවත් විශ්ලේෂණ පද්ධතිය ආරම්භ කළා...")
    
    while True:
        process_and_send()
        time.sleep(1800) # සෑම පැය බාගයකටම වරක් අලුත් පුවත් පරීක්ෂා කරයි
