import feedparser
import requests
import sys
from datetime import datetime, timedelta

TOKEN = '8315240372:AAHSLp4ttCPRwysSmEh8r6otZkMQRcJUuUE'
CHANNEL_ID = '-1004352959600'

# РАЗБИВАЕМ НА 3 ОТДЕЛЬНЫХ ЗАПРОСА ДЛЯ НАДЕЖНОСТИ
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

def get_news(queries, lang, gl):
    week_ago = datetime.now() - timedelta(days=7)
    news_items = []
    seen_links = set()
    
    # Теперь цикл проходит по КАЖДОМУ маленькому запросу
    for query in queries:
        encoded_query = requests.utils.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl={lang}&gl={gl}&ceid={gl}:{lang}"
        
        try:
            feed = feedparser.parse(url)
            # Берем топ-15 из каждого маленького запроса
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
                    news_items.append(f"{pub_date} | {title} | <a href='{link}'>Читать</a>")
        except Exception as e:
            print(f"Ошибка при запросе {query}: {e}")
            
    # Сортируем все собранные новости по дате (от новых к старым)
    news_items.sort(key=lambda x: x.split(' | ')[0], reverse=True)
    
    # Отдаем максимум 20 штук
    return news_items[:20]

region = sys.argv[1]

if region == 'RU':
    news = get_news(QUERIES_RU, 'ru', 'RU')
    header = "🇷🇺 Дайджест: Картографические сервисы РФ\n\n"
else:
    news = get_news(QUERIES_WORLD, 'en', 'US')
    header = "🌍 Дайджест: Мировые картографические сервисы\n\n"

if not news:
    final_text = header + "На этой неделе новостей не найдено."
else:
    final_text = header + "\n\n".join(news)

send_message(final_text)
