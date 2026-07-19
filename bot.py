import feedparser
import requests
import sys
import json
from datetime import datetime, timedelta

TOKEN = '8315240372:AAHSLp4ttCPRwysSmEh8r6otZkMQRcJUuUE'
CHANNEL_ID = '-1004352959600'

# ==========================================
# 1. ЗАПРОСЫ ДЛЯ ЧЕТВЕРГА (РФ + МИР)
# ==========================================
QUERIES_RU = [
    '"Яндекс Карты" OR "Яндекс.Карты" OR "Яндекс Навигатор" OR "2ГИС" OR "ДубльГИС" OR "2GIS"',
    '"Google Карты" OR "Google Maps" OR "СитиГид" OR "CityGuide" OR "Навител" OR "Organic Maps" OR "Maps.me" OR "OsmAnd"',
    '"Яндекс Бизнес" OR "Google Business" OR "Foursquare" OR "картографический сервис" OR "геосервис" OR "навигационное приложение"',
    'site:vc.ru ("Яндекс Карты" OR "2ГИС" OR "Google Maps" OR "Навител")'
]

QUERIES_WORLD = [
    '"Google Maps" OR "Apple Maps" OR "Waze" OR "Foursquare"',
    '"HERE WeGo" OR "HERE Technologies" OR "TomTom" OR "Sygic" OR "Mapbox" OR "Esri"',
    '"KakaoMap" OR "Naver Map" OR "Baidu Maps" OR "Gaode Maps" OR "Amap" OR "Navitime" OR "MapmyIndia" OR "GrabMaps" OR "Gojek Maps" OR "OpenStreetMap"'
]

# ==========================================
# 2. ЗАПРОСЫ ДЛЯ ПОНЕДЕЛЬНИКА (МАРКЕТИНГ И 50+ АГЕНТСТВ)
# ==========================================
QUERIES_MARKETING = [
    # --- Медиа и Аналитика ---
    'site:sostav.ru OR site:slon.ru OR site:lookatme.ru ("Яндекс Карты" OR "2ГИС" OR "Google Карты")',
    'site:roistat.com OR site:seonews.ru OR site:clubber.ru OR site:metodmedia.ru ("Яндекс Карты" OR "2ГИС")',
    # --- PPL, Affiliate и Performance ---
    'site:admitad.com OR site:workle.ru OR site:click.ru OR site:alfalead.ru ("Яндекс Карты" OR "2ГИС")',
    'site:pandordo.com OR site:elama.ru OR site:roibonus.ru OR site:actionpay.ru ("Яндекс Карты" OR "2ГИС")',
    'site:salesfinder.ru OR site:targethunter.ru OR site:profitcommander.com ("Яндекс Карты" OR "2ГИС")',
    # --- SMM и Digital-холдинги ---
    'site:smmplanner.com OR site:netpeak.net OR site:icontext.ru OR site:ingate.ru ("Яндекс Карты" OR "2ГИС")',
    'site:jetstyle.ru OR site:freshmiddle.ru OR site:promo.ru OR site:instream.ru ("Яндекс Карты" OR "2ГИС")',
    'site:promeo.ru OR site:labuda.pro OR site:alexadigital.ru OR site:zorka.space ("Яндекс Карты" OR "2ГИС")',
    'site:actiondigital.ru OR site:greens.agency OR site:mindspace.ru OR site:vitamingroup.ru ("Яндекс Карты" OR "2ГИС")',
    # --- PR и SERM ---
    'site:imc.ru OR site:mslgroup.ru OR site:spn.ru OR site:piar-shkola.ru ("Яндекс Карты" OR "2ГИС")',
    'site:plus8.ru OR site:imaginegroup.ru OR site:apr-agency.ru OR site:manganis.ru ("Яндекс Карты" OR "2ГИС")',
    # --- Креатив, Дизайн и Брендинг ---
    'site:ony.agency OR site:shuka.design OR site:atao.ru OR site:kollegi.agency ("Яндекс Карты" OR "2ГИС")',
    'site:partizan.moscow OR site:blackwhite.su OR site:ulybkaradugi.ru OR site:voskhod.agency ("Яндекс Карты" OR "2ГИС")',
    'site:suprematika.com OR site:lovata.com OR site:rendell.ru OR site:artlebedev.ru ("Яндекс Карты" OR "2ГИС")',
    'site:mildberry.ru OR site:emotionalbranding.ru OR site:velvet.media OR site:fiercepanda.ru ("Яндекс Карты" OR "2ГИС")',
    'site:pencil.agency OR site:onlineman.ru OR site:wannart.ru OR site:platov.vc ("Яндекс Карты" OR "2ГИС")',
    'site:banda.agency OR site:iskra.biz OR site:happyagency.ru OR site:possible.ru ("Яндекс Карты" OR "2ГИС")',
    'site:adv.ru OR site:dentsu.ru OR site:publicisgroupe.ru OR site:omnicommediagroup.ru ("Яндекс Карты" OR "2ГИС")',
    # --- Event, BTL и Контент ---
    'site:agt.ru OR site:mkgroup.ru OR site:eventum.ru OR site:yva.ru ("Яндекс Карты" OR "2ГИС")',
    'site:mediacube.media OR site:saltcontent.ru OR site:ideaplatform.ru OR site:freakyfranky.ru ("Яндекс Карты" OR "2ГИС")',
    'site:redquadro.ru OR site:groupm.com OR site:starcom.ru OR site:mediacom.ru ("Яндекс Карты" OR "2ГИС")',
    'site:maxima.ru OR site:omd.com OR site:snil.ru OR site:akarussia.ru ("Яндекс Карты" OR "2ГИС")',
    'site:digital.ru OR site:deviate.ru OR site:pm.media ("Яндекс Карты" OR "2ГИС")',
    # --- Широкая сеть ---
    '("Яндекс Карты" OR "2ГИС" OR "Google Maps") AND ("креативное агентство" OR "медиаплан" OR "спецпроект" OR "кейс" OR "наружная реклама")'
]

# ==========================================
# 3. ФИЛЬТРЫ
# ==========================================
REQUIRED_BRANDS = ['яндекс карт', '2гис', 'дубльгис', 'google карт', 'навител', 'ситигид', 'organic maps', 'maps.me', 'османд', 'османд', 'яндекс бизнес', 'google business', 'картографическ']
BANNED_PHRASES = ['ищу', 'вакансия', 'требуется', 'резюме', 'бренд-лид', 'продакт-менеджер на', 'упаковка карточки', 'оформление карточки', 'как добавить организацию', 'как попасть в карты', 'накрутка отзывов', 'как повысить рейтинг', 'как удалить отзыв', 'как ответить на отзыв', 'ведение карточки', 'оформить карточку', 'продвижение карточки', 'как исправить ошибку в']

# ==========================================
# 4. ФУНКЦИИ ОФОРМЛЕНИЯ
# ==========================================
def get_week_period():
    today = datetime.now()
    start = today - timedelta(days=7)
    months = ["", "января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    yr = f"{str(today.year)[2:]}'"
    if start.month == today.month:
        return f"{start.day}–{today.day} {months[today.month]}, {yr}"
    else:
        return f"{start.day} {months[start.month]} – {today.day} {months[today.month]}, {yr}"

def get_telegraph_token():
    r = requests.get('https://api.telegra.ph/createAccount', params={'short_name': 'MapsPMM_Digest', 'author_name': 'Maps Digest Bot'})
    return r.json()['result']['access_token']

def create_telegraph_page(title, news_items):
    t_token = get_telegraph_token()
    content = []
    for item in news_items:
        date, title, source, link = item
        # Формируем строку: Дата — Заголовок (Источник), где Заголовок - ссылка
        content.append({
            "tag": "p",
            "children": [
                date, # Убрали <strong>, чтобы не булило заголовок
                " — ",
                {"tag": "a", "href": link, "children": [title]},
                " (",
                {"tag": "em", "children": [source]},
                ")"
            ]
        })
        # Мелкий отступ между новостями
        content.append({"tag": "br"})

    r = requests.post('https://api.telegra.ph/createPage', json={
        'access_token': t_token,
        'title': title, # Заголовок страницы (стал h3, больше не конфликтует)
        'author_name': 'Maps PMM',
        'content': content,
        'return_content': False
    })
    
    if r.status_code == 200 and r.json()['ok']:
        return r.json()['result']['url']
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
    except:
        pass
    return text

def send_tg_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    requests.post(url, json=payload)

# ==========================================
# 5. СБОР НОВОСТЕЙ
# ==========================================
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
                        if pub_dt < week_ago: continue
                        pub_date = pub_dt.strftime("%d.%m.%Y")
                    except: continue
                        
                    title = entry.title
                    link = entry.link
                    source = "Источник"
                    clean_title = title
                    if " - " in title:
                        parts = title.rsplit(" - ", 1)
                        clean_title = parts[0].strip()
                        source = parts[1].strip()

                    if is_marketing:
                        title_lower = clean_title.lower()
                        if not any(brand in title_lower for brand in REQUIRED_BRANDS): continue
                        if any(bad in title_lower for bad in BANNED_PHRASES): continue

                    if do_translate:
                        clean_title = translate_to_ru(clean_title)
                        
                    news_items.append((pub_date, clean_title, source, link))
        except: pass
            
    news_items.sort(key=lambda x: x[0], reverse=True)
    return news_items[:20]

# ==========================================
# 6. ГЛАВНАЯ ЛОГИКА
# ==========================================
region = sys.argv[1]
period_str = get_week_period() # Рассчитываем ровно 7 дней

if region == 'RU':
    news = get_news(QUERIES_RU, 'ru', 'RU')
    title_tg = f"🇷🇺 Карты в России | {period_str}"
    title_ph = "Карты в России: Дайджест"
elif region == 'WORLD':
    news = get_news(QUERIES_WORLD, 'en', 'US', do_translate=True)
    title_tg = f"🌍 Карты в мире | {period_str}"
    title_ph = "Карты в мире: Дайджест"
else:
    news = get_news(QUERIES_MARKETING, 'ru', 'RU', is_marketing=True)
    title_tg = f"📺 Маркетинг в индустрии | {period_str}"
    title_ph = "Маркетинг в индустрии: Дайджест"

if not news:
    send_tg_message(f"{title_tg}\n\nНа этой неделе новостей не найдено.")
else:
    print("Создаю страницу на Telegra.ph...")
    ph_url = create_telegraph_page(title_ph, news)
    
    if ph_url:
        # Строгий дизайн по ТЗ
        msg = f"{title_tg}\n\n↧ <a href='{ph_url}'>Открыть полный дайджест</a>"
        send_tg_message(msg)
        print("Успех!")
    else:
        print("Ошибка Telegra.ph, отправляю текстом.")
        text = title_tg + "\n\n" + "\n\n".join([f"<b>{d}</b>\n{t}\n{s} | <a href='{l}'>Читать</a>" for d, t, s, l in news])
        send_tg_message(text)
