import feedparser
import requests
import sys
import json
from datetime import datetime, timedelta

TOKEN = '8315240372:AAHSLp4ttCPRwysSmEh8r6otZkMQRcJUuUE'
CHANNEL_ID = '-1004352959600'

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

QUERIES_MARKETING = [
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
BANNED_PHRASES = ['ищу', 'вакансия', 'требуется', 'резюме', 'бренд-лид', 'продакт-менеджер на', 'упаковка карточки', 'оформление карточки', 'как добавить организацию', 'как попасть в карты', 'накрутка отзывов', 'как повысить рейтинг', 'как удалить отзыв', 'как ответить на отзыв', 'ведение карточки', 'оформить карточку', 'продвижение карточки', 'как исправить ошибку в']

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
    
    for item in news_items:
        date, title, source, link = item
        safe_link = safe_text(link)
        if not safe_link.startswith('http'): continue

        # ПРАВИЛЬНАЯ СТРУКТУРА TELEGRA.PH (href строго в attrs)
        content.append({
            "tag": "p",
            "children": [
                safe_text(date), " — ",
                {"tag": "a", "attrs": {"href": safe_link}, "children": [safe_text(title)]},
                " (", {"tag": "em", "children": [safe_text(source)]}, ")"
            ]
        })
        content.append({"tag": "br"})

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
                    if do_translate: clean_title = translate_to_ru(clean_title)
                    news_items.append((pub_date, clean_title, source, link))
        except: pass
    news_items.sort(key=lambda x: x[0], reverse=True)
    return news_items[:20]

region = sys.argv[1]
period_str = get_week_period()

if region == 'RU':
    news = get_news(QUERIES_RU, 'ru', 'RU')
    title_str = f"🇷🇺 Карты в России | {period_str}"
elif region == 'WORLD':
    news = get_news(QUERIES_WORLD, 'en', 'US', do_translate=True)
    title_str = f"🌍 Карты в мире | {period_str}"
else:
    news = get_news(QUERIES_MARKETING, 'ru', 'RU', is_marketing=True)
    title_str = f"📺 Маркетинг и карты | {period_str}"

if not news:
    send_tg_message(title_str + "\n\nНа этой неделе новостей не найдено.")
else:
    ph_url = create_telegraph_page(title_str, news)
    if ph_url:
        msg = f"<a href='{ph_url}'>{title_str} ↧</a>"
        send_tg_message(msg)
    else:
        text = title_str + "\n\n" + "\n\n".join([f"<b>{d}</b>\n{t}\n{s} | <a href='{l}'>Читать</a>" for d, t, s, l in news])
        send_tg_message(text)
