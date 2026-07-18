import feedparser
import requests
import sys
import re
from datetime import datetime, timedelta

TOKEN = '8315240372:AAHSLp4ttCPRwysSmEh8r6otZkMQRcJUuUE'
CHANNEL_ID = '-1004352959600'

QUERIES_RU = [
    '"Яндекс Карты" OR "Яндекс.Карты" OR "Яндекс Навигатор" OR "2ГИС" OR "ДубльГИС" OR "2GIS"',
    '"Google Карты" OR "Google Maps" OR "СитиГид" OR "CityGuide" OR "Навител" OR "Organic Maps" OR "Maps.me" OR "OsmAnd"',
    '"Яндекс Бизнес" OR "Google Business" OR "Foursquare" OR "картографический сервис" OR "геосервис" OR "навигационное приложение"'
]

QUERIES_WORLD = [
    '"Google Maps" OR "Apple Maps" OR "Waze" OR "Foursquare"',
    '"HERE WeGo" OR "HERE Technologies" OR "TomTom" OR "Sygic" OR "Mapbox" OR "Esri"',
    '"KakaoMap" OR "Naver Map" OR "Baidu Maps" OR "Gaode Maps" OR "Amap" OR "Navitime" OR "MapmyIndia" OR "GrabMaps" OR "Gojek Maps" OR "OpenStreetMap"'
]

# РАСШИРЕННЫЙ ПОИСК ДЛЯ ПОНЕДЕЛЬНИКА
QUERIES_MARKETING = [
    # 1. Ядро маркетинга
    'site:sostav.ru (карты OR "2ГИС" OR "Яндекс Карты" OR "Google Карты" OR геосервис)',
    'site:vc.ru (карты OR "2ГИС" OR "Яндекс Карты" OR "Google Maps" OR навигатор)',
    'site:adindex.ru OR site:cossa.ru (карты OR "Яндекс Карты" OR "2ГИС")',
    # 2. IT и Разработка
    'site:habr.com (карты OR "2ГИС" OR "Яндекс Карты" OR "Google Maps" OR OpenStreetMap)',
    'site:tjournal.ru OR site:roem.ru OR site:tadviser.ru (карты OR "Яндекс Карты" OR "2ГИС" OR геосервис)',
    # 3. Бизнес и GR
    'site:rbc.ru OR site:vedomosti.ru OR site:forbes.ru (карты OR "Яндекс Карты" OR "2ГИС" OR "Google Карты")',
    'site:kommersant.ru OR site:iz.ru (карты OR "Яндекс Карты" OR "2ГИС" OR навигатор)',
    # 4. Юридические и IT-гос
    'site:rapsi.ru OR site:zakon.ru OR site:cnews.ru (карты OR "2ГИС" OR "Яндекс Карты" OR ГИС)',
    # 5. Крупные агентства (НРА, Russ и др.)
    'site:nra.ru OR site:russ-media.com (карты OR "Яндекс Карты" OR "2ГИС" OR геосервис)',
    # 6. Сетка-безопасность по смыслу
    '("Яндекс Карты" OR "2ГИС" OR "Google Карты" OR геосервис) AND (маркетинг OR реклама OR разработка OR "локальный маркетинг" OR кейс OR "новая функция" OR релиз)'
]

def translate_to_ru(text):
    try:
        url = f"https://translate.google.com/m?sl=en&tl=ru&q={requests.utils.quote(text)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        start_tag = '<div class="result-container">'
        end_tag = '</div>'
        if start_tag in response.text:
            translated = response.text.split(start_tag)[1].split(end_tag)[0]
            return re.sub('<[^<]+?>', '', translated).strip()
    except Exception as e:
        print(f"Ошибка перевода: {e}")
    return text

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    response = requests.post(url, json=payload)
    print(f"ОТВЕТ ТЕЛЕГРАМА: {response.status_code}")
    if response.status_code != 200:
        raise Exception(f"ОШИБКА: {response.text}")

def get_news(queries, lang, gl, do_translate=False):
    week_ago = datetime.now() - timedelta(days=7)
    news_items = []
    seen_links = set()
    
    for query in queries:
        encoded_query = requests.utils.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl={lang}&gl={gl}&ceid={gl}:{lang}"
        
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                if entry.link not in seen_links:
                    seen_links.add(entry.link)
                    
                    try:
                        pub_dt = datetime(*entry.published_parsed[:6])
                        if pub_dt < week_ago:
                            continue
                        pub_date = pub_dt.strftime("%d.%m.%Y")
                    except:
                        continue
                        
                    title = entry.title
                    link = entry.link
                    
                    source = "Источник"
                    clean_title = title
                    if " - " in title:
                        parts = title.rsplit(" - ", 1)
                        clean_title = parts[0].strip()
                        source = parts[1].strip()

                    if do_translate:
                        print(f"Перевожу: {clean_title[:30]}...")
                        clean_title = translate_to_ru(clean_title)
                        
                    news_items.append(f"<b>{pub_date}</b>\n{clean_title}\n{source} | <a href='{link}'>Читать</a>")
        except Exception as e:
            print(f"Ошибка запроса: {e}")
            
    news_items.sort(key=lambda x: x.split('\n')[0], reverse=True)
    return news_items[:20]

region = sys.argv[1]

if region == 'RU':
    news = get_news(QUERIES_RU, 'ru', 'RU', do_translate=False)
    header = "🇷🇺 <b>Карты РФ</b>\n\n"
elif region == 'WORLD':
    news = get_news(QUERIES_WORLD, 'en', 'US', do_translate=True)
    header = "🌍 <b>Карты в мире</b>\n\n"
else:
    news = get_news(QUERIES_MARKETING, 'ru', 'RU', do_translate=False)
    header = "🧩 <b>Маркетинг и индустрия карт</b>\n\n"

if not news:
    final_text = header + "На этой неделе новостей не найдено."
else:
    final_text = header + "\n\n".join(news)

send_message(final_text)
