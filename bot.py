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

QUERIES_MARKETING = [
    'site:sostav.ru ("Яндекс Карты" OR "2ГИС" OR "Google Карты" OR "Яндекс Бизнес")',
    'site:vc.ru ("Яндекс Карты" OR "2ГИС" OR "Google Maps")',
    'site:platov.vc OR site:banda.agency ("Яндекс Карты" OR "2ГИС" OR "Google Maps")',
    'site:iskra.biz OR site:happyagency.ru ("Яндекс Карты" OR "2ГИС")',
    'site:lookatme.ru OR site:slon.ru ("Яндекс Карты" OR "2ГИС" OR "Google Карты")',
    'site:seonews.ru OR site:clubber.ru OR site:metodmedia.ru ("Яндекс Карты" OR "2ГИС" OR "Google Карты")',
    'site:snil.ru OR site:akarussia.ru OR site:digital.ru ("Яндекс Карты" OR "2ГИС")',
    '("Яндекс Карты" OR "2ГИС" OR "Google Maps") AND ("креативное агентство" OR "медиаплан" OR "спецпроект" OR "кейс" OR "наружная реклама")'
]

# Белый список (Щит)
REQUIRED_BRANDS = [
    'яндекс карт', '2гис', 'дубльгис', 'google карт', 'навител', 
    'ситигид', 'organic maps', 'maps.me', 'османд', 'osmand',
    'яндекс бизнес', 'google business', 'картографическ'
]

# Черный список (Отсеиваем вакансии и инструкции для владельцев)
BANNED_PHRASES = [
    'ищу', 'вакансия', 'требуется', 'резюме', 'бренд-лид', 'продакт-менеджер на',
    'упаковка карточки', 'оформление карточки', 'как добавить организацию', 'как попасть в карты',
    'накрутка отзывов', 'как повысить рейтинг', 'как удалить отзыв', 'как ответить на отзыв',
    'ведение карточки', 'оформить карточку', 'продвижение карточки', 'как исправить ошибку в'
]

# Функция для защиты ссылок от поломки в Телеграме
def escape_html(text):
    text = text.replace('&', '&amp;')
    text = text.replace('<', '&lt;')
    text = text.replace('>', '&gt;')
    return text

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

def get_news(queries, lang, gl, do_translate=False, is_marketing=False):
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

                    # Логика фильтрации (только для маркетинга)
                    if is_marketing:
                        title_lower = clean_title.lower()
                        
                        # 1. Щит: нет бренда = мусор
                        if not any(brand in title_lower for brand in REQUIRED_BRANDS):
                            print(f"МУСОР (нет бренда): {clean_title[:40]}...")
                            continue
                            
                        # 2. Черный список: вакансии и рутинные гайды = мусор
                        if any(bad_phrase in title_lower for bad_phrase in BANNED_PHRASES):
                            print(f"МУСОР (гайд/вакансия): {clean_title[:40]}...")
                            continue

                    if do_translate:
                        print(f"Перевожу: {clean_title[:30]}...")
                        clean_title = translate_to_ru(clean_title)
                        
                    # ЭКРАНИРУЕМ HTML (ИСПРАВЛЯЕТ БИТЫЕ ССЫЛКИ)
                    safe_title = escape_html(clean_title)
                    safe_source = escape_html(source)
                    safe_link = link.replace('&', '&amp;') # Ссылки ломались именно из-за &
                        
                    news_items.append(f"<b>{pub_date}</b>\n{safe_title}\n{safe_source} | <a href='{safe_link}'>Читать</a>")
        except Exception as e:
            print(f"Ошибка запроса: {e}")
            
    news_items.sort(key=lambda x: x.split('\n')[0], reverse=True)
    return news_items[:20]

region = sys.argv[1]

if region == 'RU':
    news = get_news(QUERIES_RU, 'ru', 'RU')
    header = "🇷🇺 <b>Карты РФ</b>\n\n"
    hashtags = "\n\n#новостирф"
elif region == 'WORLD':
    news = get_news(QUERIES_WORLD, 'en', 'US', do_translate=True)
    header = "🌍 <b>Карты в мире</b>\n\n"
    hashtags = "\n\n#новостимир"
else:
    news = get_news(QUERIES_MARKETING, 'ru', 'RU', is_marketing=True)
    header = "📺 <b>Маркетинг в индустрии</b>\n\n"
    hashtags = "\n\n#реклама"

if not news:
    final_text = header + "На этой неделе новостей не найдено." + hashtags
else:
    final_text = header + "\n\n".join(news) + hashtags

send_message(final_text)
