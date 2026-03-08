import requests
from bs4 import BeautifulSoup
from newspaper import Article
from deep_translator import GoogleTranslator
import os
import time

# GitHub Secrets වලින් රහස්‍ය දත්ත කියවීම
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

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
    replacements = {"ප්‍රකාශ කළේය": "කිව්වා", "සිදු කරනු ලබයි": "කරනවා", "විසින්": "මගින්", "නිරීක්ෂණය විය": "දැක්කා"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text

def get_massive_sources():
    found_items = []
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    # පරීක්ෂා කිරීම සඳහා Google Trends පමණක් දැනට ගනිමු
    try:
        trend_url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
        res = requests.get(trend_url, headers=headers, timeout=10)
        soup = BeautifulSoup(res.content, 'xml')
        for item in soup.find_all('item')[:5]: # මුල් පුවත් 5ක් පමණක්
            title = item.title.text
            link = item.find('ht:news_item_url').text if item.find('ht:news_item_url') else item.link.text
            found_items.append({"title": title, "link": link})
    except: pass
    return found_items

def process_and_send():
    translator = GoogleTranslator(source='auto', target='si')
    all_data = get_massive_sources()
    
    if not all_data:
        send_telegram_msg("⚠️ අලුත් පුවත් කිසිවක් හමු වුණේ නැහැ.")
        return

    for item in all_data:
        try:
            article = Article(item['link'])
            article.download()
            article.parse()
            
            # සිංහලට පරිවර්තනය
            si_title = simplify_sinhala(translator.translate(item['title']))
            si_content = simplify_sinhala(translator.translate(article.text[:1000])) # කෙටි විස්තරයක්

            msg = f"🎥 *NEW SCRIPT*\n\n🔴 *මාතෘකාව:* {si_title}\n\n📝 *විස්තරය:* {si_content}\n\n🔗 {item['link']}"
            send_telegram_msg(msg)
            time.sleep(2) # ටෙලිග්‍රෑම් එකට බරක් නොවීමට කුඩා විරාමයක්
        except: continue

if __name__ == "__main__":
    process_and_send()
