import requests
from bs4 import BeautifulSoup
from newspaper import Article
from deep_translator import GoogleTranslator
import os
import time
import random

# GitHub Secrets මගින් දත්ත ලබා ගැනීම
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

def send_telegram_msg(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    try:
        # පණිවිඩය දිග වැඩි නම් කොටස් වලට බෙදා යවයි
        if len(message) > 4000:
            for i in range(0, len(message), 4000):
                requests.post(url, data={'chat_id': CHAT_ID, 'text': message[i:i+4000], 'parse_mode': 'Markdown'}, timeout=15)
        else:
            requests.post(url, data={'chat_id': CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}, timeout=15)
    except:
        requests.post(url, data={'chat_id': CHAT_ID, 'text': message}, timeout=15)

def simplify_sinhala(text):
    """පරිවර්තනය වූ සිංහල තවදුරටත් සරල කථන ශෛලියට හැරවීම"""
    replacements = {
        "ප්‍රකාශ කළේය": "කිව්වා", "සිදු කරනු ලබයි": "කරනවා", "නිරීක්ෂණය කරන ලදී": "දැකගන්න ලැබුණා",
        "භාවිතා කරමින්": "පාවිච්චි කරලා", "සමගින්": "එක්ක", "විසින්": "මගින්",
        "පැවැත්වූයේය": "පැවැත්වුවා", "අනාවරණය විය": "හෙළි වුණා", "නිරත විය": "යෙදුණා"
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def make_clickbait(title):
    """මාතෘකාව කුතුහලය දනවන ලෙස වෙනස් කිරීම"""
    prefixes = ["මෙන්න අද ලෝකයම කතා වෙන ", "කිසිවෙකු නොකියූ ", "සැඟවුණු ඇත්ත හෙළිවෙයි: ", "අවසානය වෙනස්ම එකක්: "]
    return random.choice(prefixes) + title

def get_sources():
    """ලෝකයේ අඩවි 20ක්, Google Trends 20ක් සහ ලංකාවේ පුවත් 5ක් සොයා ගැනීම"""
    found_items = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # 1. Google Trends (Daily Trends 20)
    try:
        res = requests.get("https://trends.google.com/trends/trendingsearches/daily/rss?geo=US", headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, 'xml')
        for item in soup.find_all('item')[:20]:
            found_items.append({"title": item.title.text, "link": item.link.text, "tag": "Global Trend"})
    except: pass

    # 2. Sri Lanka Trends (RSS පුවත් අඩවි 5ක්)
    sl_sources = ["https://www.adaderana.lk/rss.php", "https://www.hirunews.lk/rss/sinhala.xml"]
    for url in sl_sources:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.content, 'xml')
            for item in soup.find_all('item')[:3]:
                found_items.append({"title": item.title.text, "link": item.link.text, "tag": "SL Trend"})
        except: pass

    # 3. Global Media (වෙබ් අඩවි 20ක් පමණ ආවරණය වන පරිදි)
    mega_sources = [
        "https://www.reuters.com/world/", "https://www.bbc.com/news/world", 
        "https://www.aljazeera.com/news/", "https://www.nasa.gov/news-release/",
        "https://www.techcrunch.com/", "https://www.bloomberg.com/world",
        "https://www.military.com/daily-news", "https://www.cnbc.com/world-politics/",
        "https://www.sciencedaily.com/news/", "https://www.wired.com/"
    ]
    for url in mega_sources:
        try:
            res = requests.get(url, headers=headers, timeout=10)
            soup = BeautifulSoup(res.text, 'html.parser')
            for a in soup.find_all('a', href=True):
                if len(a.text.strip()) > 60:
                    l = a['href']
                    if not l.startswith('http'): l = f"https://{url.split('/')[2]}{l}"
                    found_items.append({"title": a.text.strip(), "link": l, "tag": "Global News"})
                    if len(found_items) > 60: break
        except: continue
    
    return found_items

def process_and_send():
    translator = GoogleTranslator(source='auto', target='si')
    news_list = get_sources()
    
    # ලැයිස්තුවෙන් පුවත් කිහිපයක් තෝරා ගැනීම (විනාඩි 6ක Script එකක් සඳහා)
    random.shuffle(news_list)
    processed_count = 0

    for item in news_list:
        try:
            article = Article(item['link'])
            article.download(); article.parse()
            
            if len(article.text) < 1000: continue # දීර්ඝ ලිපි පමණක් තෝරා ගනී

            # සිංහලට හැරවීම සහ සරල කිරීම
            raw_title = translator.translate(item['title'])
            clickbait_title = simplify_sinhala(make_clickbait(raw_title))
            
            # විනාඩි 6ක වොයිස් ඕවර් එකක් සඳහා වචන 800-1000ක් අවශ්‍යයි
            full_body = translator.translate(article.text[:4500]) # උපරිම අකුරු 4500ක් ගනී
            simple_body = simplify_sinhala(full_body)

            # Meta Data සැකසීම
            keywords = f"{raw_title}, Sri Lanka News, Technology, Discovery, World News, Voiceover Sinhala"
            tags = "#NewsSriLanka #Trending #Discovery #Technology #YouTubeSL"

            # සම්පූර්ණ පිටපත සැකසීම
            script_msg = f"""
🔥 *YOUTUBE 06-MINUTE SCRIPT* 🔥
━━━━━━━━━━━━━━━━━━━━━━
📌 *මාතෘකාව:* {clickbait_title}

👋 *Intro (තත්පර 30):*
ආයුබෝවන් හැමෝටම! අද අපි අරගෙන ආවේ ලෝකයම හොල්ලපු, හැමෝම දැනගත යුතුම විශේෂ පුවතක්. මේ සිදුවීම පිටුපස තියෙන අබිරහස මොකක්ද? විනාඩි 6ක් පුරා අපි මේ ගැන සම්පූර්ණයෙන් කතා කරමු.

📖 *ප්‍රධාන පුවත (Main Content):*
{simple_body}

🎬 *Outro:*
ඉතින් මේ ගැන ඔයාලගේ අදහස මොකක්ද? පහළින් කමෙන්ට් කරන්න. මේ වගේ වීඩියෝ දිගටම බලන්න අපිව සබ්ස්ක්‍රයිබ් කරන්න. ස්තූතියි!

━━━━━━━━━━━━━━━━━━━━━━
📊 *META DATA FOR SEO*
━━━━━━━━━━━━━━━━━━━━━━
🔑 *Keywords:* {keywords}
🏷️ *Tags:* {tags}
🔗 *Source:* {item['link']}
━━━━━━━━━━━━━━━━━━━━━━
            """
            send_telegram_msg(script_msg)
            processed_count += 1
            if processed_count >= 5: break # වරකට පිටපත් 5ක් යවයි
            time.sleep(5)
        except: continue

if __name__ == "__main__":
    send_telegram_msg("🔄 *[SYSTEM]* පද්ධතිය පුවත් සෙවීම සහ Script සැකසීම ආරම්භ කළා...")
    process_and_send()
    send_telegram_msg("✅ *[SYSTEM]* සියලුම ස්ක්‍රිප්ට් ටෙලිග්‍රෑම් වෙත යවා අවසන්.")
