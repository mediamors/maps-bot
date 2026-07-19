import feedparser
import requests
import sys
import json
from datetime import datetime, timedelta

TOKEN = '8315240372:AAHSLp4ttCPRwysSmEh8r6otZkMQRcJUuUE'
CHANNEL_ID = '-1004352959600'

# ==========================================
# 1. ЧЕРНЫЙ СПИСОК ДОМЕНОВ (Единственный фильтр от мусора)
# ==========================================
BLOCKED_DOMAINS = [
    'vietnam.vn', 'cyprusinform.com', 'unian.net', 'golos.ua', 'focus.ua', 
    'makeuseof.com', 'bgr.com', 'lifehacker.com', 'zdnet.com'
]

# ==========================================
# 2. СТРОГИЕ ЗАПРОСЫ (ГЛАГОЛЫ И ДЕЙСТВИЯ)
# ==========================================
QUERIES_RU_STRICT = [
    '("Яндекс Карты" OR "Яндекс.Карты" OR "Яндекс Навигатор" OR "2ГИС" OR "ДубльГИС" OR "2GIS") AND ("запустил" OR "обновил" OR "добавил" OR "интегрировал" OR "выпустил" OR "представил" OR "изменил" OR "закрыл" OR "открыл")'
]

QUERIES_WORLD_STRICT = [
    '("Google Maps" OR "Apple Maps" OR "Waze" OR "Mapbox" OR "Esri" OR "HERE WeGo" OR "TomTom") AND ("launched" OR "announced" OR "updated" OR "added" OR "integrated" OR "banned" OR "partnered" OR "integration" OR "deployment" OR "feature")'
]

QUERIES_MARKETING_STRICT = [
    '("Яндекс Карты" OR "2ГИС" OR "Google Maps") AND ("креативная концепция" OR "спецпроект для" OR "рекламная кампания" OR "BTL-активация" OR "медийный план" OR "медиаплан" OR "охват" OR "таргет в картах" OR "лидогенерация" OR "воронка продаж")'
]

# ==========================================
# 3. ОТСТУПНЫЕ ЗАПРОСЫ (СТАРЫЙ ШИРОКИЙ ПОИСК)
# ==========================================
QUERIES_RU_FALLBACK = [
    '"Яндекс Карты" OR "Яндекс.Карты" OR "Яндекс Навигатор" OR "2ГИС" OR "ДубльГИС" OR "2GIS"',
    '"Google Карты" OR "Google Maps" OR "СитиГид" OR "CityGuide" OR "Навител" OR "Organic Maps" OR "Maps.me" OR "OsmAnd"',
    '"Яндекс Бизнес" OR "Google Business" OR "Foursquare" OR "картографический сервис" OR "геосервис" OR "навигационное приложение"',
    'site:vc.ru ("Яндекс Карты" OR "2ГИС" OR "Google Maps" OR "Навител")'
]

QUERIES_WORLD_FALLBACK = [
    '"Google Maps" OR "Apple Maps" OR "Waze" OR "Foursquare"',
    '"HERE WeGo" OR "HERE Technologies" OR "TomTom" OR "Sygic" OR "Mapbox" OR "Esri"',
    '"KakaoMap" OR "Naver Map" OR "Baidu Maps" OR "Gaode Maps" OR "Amap" OR "Navitime" OR "MapmyIndia" OR "GrabMaps" OR "Gojek Maps" OR "OpenStreetMap"'
]

QUERIES_MARKETING_FALLBACK = [
    'site:sostav.ru OR site:slon.ru OR site:lookatme.ru ("Яндекс Карты" OR "2ГИС" OR "Google Карты")',
    'site:roistat.com OR site:seonews.ru OR site:clubber.ru OR site:metodmedia.ru ("Яндекс Карты" OR "2ГИС")',
    'site:admitad.com OR site:workle.ru OR site:click.ru OR site:alfalead.ru ("Яндекс Карты" OR "2ГИС")',
    'site:pandordo.com OR site:elama.ru OR site:roibonus.ru OR site:actionpay.ru ("Яндекс Карты" OR "2ГИС")',
    'site:salesfinder.ru OR site:targethunter.ru OR site:profitcommander.com ("Яндекс Карты" OR "2ГИС")',
    'site:smmplanner.com OR site:netpeak.net OR site:icontext.ru OR site:ingate.ru ("Яндекс Карты" OR "2ГИС")',
    'site:jetstyle.ru OR site:freshmiddle.ru OR site:promo.ru OR site:instream.ru ("Яндекс Карты" OR "2ГИС")',
    'site:promeo.ru OR site:labuda.pro OR site:alexadigital.ru OR site:zorka.space ("Яндекс Карты" OR "2ГИС")',
    'site:actiondigital.ru OR site:greens.agency OR site:mindspace.ru OR site:vitamingroup.ru ("Яндекс Карты" OR "2ГИС")',
    'site:imc.ru OR site:mslgroup.ru OR site:spn.ru OR site:piar-shkola.ru ("Яндекс Карты" OR "2ГИС")',
    'site:plus8.ru OR site:imaginegroup.ru OR site:apr-agency.ru OR site:manganis.ru ("Яндекс Карты" OR "2ГИС")',
    'site:ony.agency OR site:shuka.design OR site:atao.ru OR site:kollegi.agency ("Яндекс Карты" OR "2ГИС")',
    'site:partizan.moscow OR site:blackwhite.su OR site:ulybkaradugi.ru OR site:voskhod.agency ("Яндекс Карты" OR "2ГИС")',
    'site:suprematika.com OR site:lovata.com OR site:rendell.ru OR site:artlebedev.ru ("Яндекс Карты" OR "2ГИС")',
    'site:mildberry.ru OR site:emotionalbranding.ru OR site:velvet.media OR site:fiercepanda.ru ("Яндекс Карты" OR "2ГИС")',
    'site:pencil.agency OR site:onlineman.ru OR site:wannart.ru OR site:platov.vc ("Яндекс Карты" OR "2ГИС")',
    'site:banda.agency OR site:iskra.biz OR site:happyagency.ru OR site:possible.ru ("Яндекс Карты" OR "2ГИС")',
    'site:adv.ru OR site:dentsu.ru OR site:publicisgroupe.ru OR site:omnicommediagroup.ru ("Яндекс Карты" OR "2ГИС")',
    'site:agt.ru OR site:mkgroup.ru OR site:eventum.ru OR site:yva.ru ("Яндекс Карты" OR "2ГИС")',
    'site:mediacube.media OR site:saltcontent.ru OR site:ideaplatform.ru OR site:freakyfranky.ru ("Яндекс Карты" OR "2ГИС")',
    'site:redquadro.ru OR site:groupm.com OR site:starcom.ru OR site:mediacom.ru ("Яндекс Карты" OR "2ГИС")',
    'site:maxima.ru OR site:omd.com OR site:snil.ru OR site:akarussia.ru ("Яндекс Карты" OR "2ГИС")',
    'site:digital.ru OR site:deviate.ru OR site:pm.media ("Яндекс Карты" OR "2ГИС")',
    '("Яндекс Карты" OR "2ГИС" OR "Google Maps") AND ("креативное агентство" OR "медиаплан" OR "спецпроект" OR "кейс" OR "наружная реклама")'
]

REQUIRED_BRANDS = ['яндекс карт', '2гис', 'дубльгис', 'google карт', 'навител', 'ситигид', 'organic maps', 'maps.me', 'османд', 'османд', 'яндекс бизнес', 'google business', 'картографическ']

# ==========================================
# 4. ФУНКЦИИ
# ==========================================
def safe_text(text):
    if not isinstance(text, str): text = str(text)
    return text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ').strip()

def get_week_period():
    today = datetime.now()
    start = today - timedelta(days=7)
    months = ["", "янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
    yr = f"{str(today.year)[2:]}'"
    if start.month == today.month:
        return f"{start.day}-{today.day} {months[today.month]}, {yr}"
    else:
        return f"{start.day} {months[start.month]}-{today.day} {months[today.month]}, {yr}"

def get_telegraph_token():
    r = requests.get('https://api.telegra.ph/createAccount', params={'short_name': 'MapsPMM_Digest', 'author_name': 'Maps Digest'})
    return r.json()['result']['access_token']

def create_telegraph_page(page_title, news_items):
    t_token = get_telegraph_token()
    content = []
    months = ["", "янв", "фев", "мар", "апр", "мая", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]
    
    for item in news_items:
        date, title, source, link = item
        safe_link = safe_text(link)
        if not safe_link.startswith('http'): continue

        try:
            dt = datetime.strptime(date, "%d.%m.%Y")
            short_date = f"{dt.day} {months[dt.month]}, {str(dt.year)[2:]}'"
        except:
            short_date = date

        content.append({"tag": "p", "children": [short_date]})
        content.append({"tag": "p", "children": [safe_text(title)]})
        content.append({
            "tag": "p",
            "children": [
                {"tag": "a", "attrs": {"href": safe_link}, "children": [safe_text(source)]}
            ]
        })
        content.append({"tag": "p", "children": ["—"]})

    payload_str = json.dumps({
        'access_token': t_token,
        'title': safe_text(page_title), 
        'author_name': 'Maps PMM',
        'content': content,
        'return_content': False
    }, ensure_ascii=False).encode('utf-8')
    
    r = requests.post('https://api.telegra.ph/createPage', data=payload_str, headers={'Content-Type': 'application/json; charset=utf-8'})
    
    if r.status_code == 200 and r.json()['ok']:
        return r.json()['result']['url']
    print(f"TELEGRA.PH ERROR: {r.text}")
    return None

def translate_to_ru(text):
    try:
        url = f"https://translate.google.com/m?sl=en&tl=ru&q={requests.utils.quote(text)}"
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        if '<div class="result-container">' in response.text:
            translated = response.text.split('<div class="result-container">')[1].split('</div>')[0]
            import re
            return re.sub('<[^<]+?>', '', translated).strip()
    except: pass
    return text

def send_tg_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    requests.post(url, json=payload)

def get_news(queries, lang, gl, do_translate=False, apply_shield=False):
    week_ago = datetime.now() - timedelta(days=7)
    news_items = []
    seen_links = set()
    
    for query in queries:
        encoded_query = requests.utils.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_query}&hl={lang}&gl={gl}&ceid={gl}:{lang}"
        try:
            feed = feedparser.parse(url)
            for entry in feed.entries[:15]:
                link = entry.link
                
                domain = link.split('/')[2] if len(link.split('/')) > 2 else ""
                if any(bad in domain for bad in BLOCKED_DOMAINS):
                    continue
                    
                if link not in seen_links:
                    seen_links.add(link)
                    try:
                        pub_dt = datetime(*entry.published_parsed[:6])
                        if pub_dt < week_ago: continue
                        pub_date = pub_dt.strftime("%d.%m.%Y")
                    except: continue
                    
                    title = entry.title
                    source = "Источник"
                    clean_title = title
                    if " - " in title:
                        parts = title.rsplit(" - ", 1)
                        clean_title = parts[0].strip()
                        source = parts[1].strip()
                        
                    if apply_shield:
                        title_lower = clean_title.lower()
                        if not any(brand in title_lower for brand in REQUIRED_BRANDS): continue

                    if do_translate: clean_title = translate_to_ru(clean_title)
                    news_items.append((pub_date, clean_title, source, link))
        except: pass
    return news_items

# ==========================================
# 5. НОВАЯ ЛОГИКА: СТРОГИЙ ПОИСК + ОТСТУПНОЕ ПРАВИЛО
# ==========================================
def fetch_with_fallback(strict_q, fallback_q, lang, gl, do_translate=False, apply_shield=False):
    print(f"Запуск строгого поиска (Глаголы/Маркетинг)...")
    news = get_news(strict_q, lang, gl, do_translate, apply_shield=False)
    
    if len(news) < 3:
        print(f"Найдено только {len(news)} статей. Запускаю отступное правило (Расширенный поиск)...")
        fallback_news = get_news(fallback_q, lang, gl, do_translate, apply_shield=apply_shield)
        
        seen = set(item[3] for item in news)
        for item in fallback_news:
            if item[3] not in seen:
                news.append(item)
                
    news.sort(key=lambda x: x[0], reverse=True)
    return news[:20]

# ==========================================
# 6. ГЛАВНАЯ ЛОГИКА (Ссылка перенесена на эмодзи)
# ==========================================
region = sys.argv[1]
period_str = get_week_period()

if region == 'HEADER':
    send_tg_message(f"↧ Дайджест за {period_str}")
    
else:
    if region == 'RU':
        news = fetch_with_fallback(QUERIES_RU_STRICT, QUERIES_RU_FALLBACK, 'ru', 'RU')
        tg_emoji = "🇷🇺"
        tg_text = "Россия"
        ph_title = f"🇷🇺 Россия | {period_str}"
    elif region == 'WORLD':
        news = fetch_with_fallback(QUERIES_WORLD_STRICT, QUERIES_WORLD_FALLBACK, 'en', 'US', do_translate=True)
        tg_emoji = "🌍"
        tg_text = "Мир" 
        ph_title = f"🌍 Мир | {period_str}"
    else:
        news = fetch_with_fallback(QUERIES_MARKETING_STRICT, QUERIES_MARKETING_FALLBACK, 'ru', 'RU', apply_shield=True)
        tg_emoji = "📺"
        tg_text = "Маркетинг"
        ph_title = f"📺 Маркетинг | {period_str}"

    if not news:
        print("Новостей нет, пост пропущен.")
    else:
        ph_url = create_telegraph_page(ph_title, news)
        if ph_url:
            # Эмодзи - ссылка, пробел, Текст - ссылка
            msg = f"<a href='{ph_url}'>{tg_emoji}</a> <a href='{ph_url}'>{tg_text}</a>"
            send_tg_message(msg)
        else:
            text = f"{tg_emoji} {tg_text}\n\n" + "\n\n".join([f"<b>{d}</b>\n{t}\n{s} | <a href='{l}'>Читать</a>" for d, t, s, l in news])
            send_tg_message(text)
