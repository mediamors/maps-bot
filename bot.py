import feedparser
import requests
import time
import sys

TOKEN = '8315240372:AAHSLp4ttCPRwysSmEh8r6otZkMQRcJUuUE'
CHANNEL_ID = '-1004352959600'

KEYWORDS_RU = '"Яндекс Карты" OR "Яндекс.Карты" OR "Карты Яндекса" OR "ЯндексКарты" OR "Яндекс.Навигатор" OR "Яндекс Навигатор" OR "2ГИС" OR "ДубльГИС" OR "Двагис" OR "2 ГИС" OR "2GIS" OR "Google Карты" OR "Google Maps" OR "Google.Карты" OR "СитиГид" OR "CityGuide" OR "City Guide" OR "Probki.net" OR "Навител" OR "Navitel" OR "Organic Maps" OR "OsmAnd" OR "Maps.me" OR "Mapsme" OR "Яндекс Бизнес" OR "Яндекс.Бизнес" OR "Yandex Business" OR "Google Business Profile" OR "Google Мой Бизнес" OR "Google.Мой.Бизнес" OR "Apple Business Connect" OR "Foursquare" OR "Swarm" OR "ВКонтакте геотеги" OR "VK геолокация" OR "VK карты" OR "2ГИС Геоаналитика" OR "2GIS Гeoаналитика" OR "Яндекс геосервисы" OR "Yandex Geo" OR "картографический сервис" OR "геосервис" OR "навигационное приложение" OR "ГИС" OR "геоинформационная система"'

KEYWORDS_WORLD = '"Google Maps" OR "Apple Maps" OR "Waze" OR "Foursquare" OR "Swarm" OR "HERE WeGo" OR "HERE Technologies" OR "HERE Maps" OR "TomTom" OR "Sygic" OR "Mapbox" OR "CARTO" OR "Esri" OR "KakaoMap" OR "Naver Map" OR "Baidu Maps" OR "Gaode Maps" OR "Amap" OR "Navitime" OR "Yahoo! Maps" OR "MapmyIndia" OR "Mappls" OR "GrabMaps" OR "Grab Maps" OR "Gojek Maps" OR "Maps.me" OR "Mapsme" OR "Guru Maps" OR "OsmAnd" OR "OpenStreetMap" OR "OSM" OR "Google Business Profile" OR "Apple Business Connect"'

def send_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {
        "chat_id": CHANNEL_ID,
        "text": text,
        "parse_mode": "HTML",
        "disable_web_page_preview": True
    }
    response = requests.post(url, json=payload)
    print(f"ОТВЕТ ТЕЛЕГРАМА: {response.status_code} - {response.text}")
    if response.status_code != 200:
        raise Exception(f"ОШИБКА: {response.text}")

def get_news(keywords, lang, gl):
    # МАГИЯ ЗДЕСЬ: добавляем "when:7d", чтобы брать ТОЛЬКО за последние 7 дней
    query_with_time = keywords + " when:7d"
    encoded_query = requests.utils.quote(query_with_time)
    
    url = f"https://news.google.com/rss/search?q={encoded_query}&hl={lang}&gl={gl}&ceid={gl}:{lang}"
    feed = feedparser.parse(url)
    news_items = []
    seen_links = set()
    
    for entry in feed.entries[:20]:
        if entry.link not in seen_links:
            seen_links.add(entry.link)
            try:
                pub_date = time.strftime("%d.%m.%Y", entry.published_parsed)
            except:
                pub_date = "Дата ?"
            title = entry.title
            link = entry.link
            news_items.append(f"{pub_date} | {title} | <a href='{link}'>Читать</a>")
    return news_items

region = sys.argv[1]

if region == 'RU':
    news = get_news(KEYWORDS_RU, 'ru', 'RU')
    header = "🇷🇺 Дайджест: Картографические сервисы РФ\n\n"
else:
    news = get_news(KEYWORDS_WORLD, 'en', 'US')
    header = "🌍 Дайджест: Мировые картографические сервисы\n\n"

if not news:
    final_text = header + "На этой неделе новостей не найдено."
else:
    final_text = header + "\n\n".join(news)

send_message(final_text)
