import feedparser
import requests
import re
import sys
import json
import html
import difflib
from datetime import datetime, timedelta

# ==========================================
# 1. НАСТРОЙКИ И КОНСТАНТЫ
# ==========================================
TOKEN = '8315240372:AAHSLp4ttCPRwysSmEh8r6otZkMQRcJUuUE'
CHANNEL_ID = '-1004352959600'

MIN_SCORE = 2              # Снижено до 2 (достаточно упоминания "Навигатор" или "ИИ")
MAX_NEWS = 10              # Максимум новостей на раздел
DUPLICATE_THRESHOLD = 0.65 # Порог похожести для удаления дублей
REQUEST_TIMEOUT = 15       # Таймаут для запросов к RSS

# ==========================================
# 2. СЛОВАРИ И ФИЛЬТРЫ
# ==========================================
MAP_WORDS = [
    'карт', 'map', 'гео', 'geo', 'навигац', 'naviga', 'маршрут', 'route', 'poi', 'организаци', 'place', 'отзыв', 'review',
    '2гис', 'дубльгис', 'навител', 'ситигид', 'османд'
]
NAVIGATION_WORDS = ['навигатор', 'navigator', 'маршрутизатор', 'gps']
AI_WORDS = ['ии', 'ai', 'нейросет', 'машинное обучение', 'gpt', 'gemini', 'llm']
MARKETING_WORDS = ['маркетинг', 'реклам', 'advertis', 'креатив', 'спецпроект', 'кейс', 'лидогенерация', 'таргет', 'воронка', 'медиаплан', 'охват', 'btl']
BAD_WORDS = [
    'android', 'pixel', 'смартфон', 'телефон', 'gmail', 'chrome', 'youtube', 'workspace', 
    'google cloud', 'gemini app', 'google search', 'seo', 'поиск google', 'play market', 
    'бассейн', 'цены на', 'стоимость', 'обойдется', 'гитлер', 'нацист', 'секретный код', 
    'я помню те годы', 'полиция выступает против', 'проблем с картами', 'как настроить', 
    'лучшее приложение', 'руководство', 'сравнивал', 'топ-', 'топ '
]
GOOD_SOURCES = [
    'sostav.ru', 'vc.ru', 'habr.com', 'rbc.ru', 'vedomosti.ru', 'forbes.ru', 'tass.ru',
    'reuters.com', 'bloomberg.com', 'techcrunch.com', 'theverge.com', '9to5google.com',
    'engadget.com', 'searchengineland.com', 'marTech', 'autoevolution.com',
    'moika78.ru', 'za-rulem.ru', 'biggorod.ru'
]
BAD_SOURCES = [
    'vietnam.vn', 'cyprusinform.com', 'unian.net', 'golos.ua', 'focus.ua', 
    'makeuseof.com', 'bgr.com', 'lifehacker.com', 'zdnet.com', 'truesharing.ru'
]

# ==========================================
# 3. RSS ИСТОЧНИКИ (Из bot.py)
# ==========================================
RSS_FEEDS_RU = [
    "https://news.google.com/rss/search?q=(%22Яндекс+Карты%22+OR+%22Яндекс.Карты%22+OR+%22Яндекс+Навигатор%22+OR+%222ГИС%22+OR+%22ДубльГИС%22+OR+%222GIS%22)+AND+(%22запустил%22+OR+%22обновил%22+OR+%22добавил%22+OR+%22интегрировал%22+OR+%22выпустил%22+OR+%22представил%22+OR+%22изменил%22+OR+%22закрыл%22+OR+%22открыл%22)&hl=ru&gl=RU&ceid=RU:ru",
    "https://news.google.com/rss/search?q=%22Яндекс+Карты%22+OR+%22Яндекс.Карты%22+OR+%22Яндекс+Навигатор%22+OR+%222ГИС%22+OR+%22ДубльГИС%22+OR+%222GIS%22&hl=ru&gl=RU&ceid=RU:ru",
    "https://news.google.com/rss/search?q=%22Google+Карты%22+OR+%22Google+Maps%22+OR+%22СитиГид%22+OR+%22CityGuide%22+OR+%22Навител%22+OR+%22Organic+Maps%22+OR+%22Maps.me%22+OR+%22OsmAnd%22+OR+%22Яндекс+Бизнес%22+OR+%22Google+Business%22+OR+%22Foursquare%22+OR+%22картографический+сервис%22+OR+%22геосервис%22&hl=ru&gl=RU&ceid=RU:ru"
]

RSS_FEEDS_WORLD = [
    "https://news.google.com/rss/search?q=(%22Google+Maps%22+OR+%22Apple+Maps%22+OR+%22Waze%22+OR+%22Mapbox%22+OR+%22Esri%22+OR+%22HERE+WeGo%22+OR+%22TomTom%22)+AND+(%22launched%22+OR+%22announced%22+OR+%22updated%22+OR+%22added%22+OR+%22integrated%22+OR+%22banned%22+OR+%22partnered%22+OR+%22integration%22+OR+%22deployment%22+OR+%22feature%22)&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=%22Google+Maps%22+OR+%22Apple+Maps%22+OR+%22Waze%22+OR+%22Foursquare%22+OR+%22HERE+WeGo%22+OR+%22HERE+Technologies%22+OR+%22TomTom%22+OR+%22Sygic%22+OR+%22Mapbox%22+OR+%22Esri%22&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=%22KakaoMap%22+OR+%22Naver+Map%22+OR+%22Baidu+Maps%22+OR+%22Gaode+Maps%22+OR+%22Amap%22+OR+%22Navitime%22+OR+%22MapmyIndia%22+OR+%22GrabMaps%22+OR+%22Gojek+Maps%22+OR+%22OpenStreetMap%22&hl=en&gl=US&ceid=US:en"
]

RSS_FEEDS_MARKETING = [
    "https://news.google.com/rss/search?q=(%22Яндекс+Карты%22+OR+%222ГИС%22+OR+%22Google+Maps%22)+AND+(%22креативная+концепция%22+OR+%22спецпроект+для%22+OR+%22рекламная+кампания%22+OR+%22BTL-активация%22+OR+%22медийный+план%22+OR+%22медиаплан%22+OR+%22охват%22+OR+%22таргет+в+картах%22+OR+%22лидогенерация%22+OR+%22воронка+продаж%22)&hl=ru&gl=RU&ceid=RU:ru",
    "https://news.google.com/rss/search?q=(%22Яндекс+Карты%22+OR+%222ГИС%22+OR+%22Google+Карты%22)+AND+(%22креативное+агентство%22+OR+%22медиаплан%22+OR+%22спецпроект%22+OR+%22кейс%22+OR+%22наружная+реклама%22)&hl=ru&gl=RU&ceid=RU:ru"
]

# ==========================================
# 4. ФУТИЛИТЫ ТЕЛЕГРАМА И TELEGRA.PH
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
    r = requests.get('https://api.telegra.ph/createAccount', params={'short_name': 'MapsPMM_Digest_Main', 'author_name': 'Maps Digest'})
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
        content.append({"tag": "hr"})

    payload_str = json.dumps({
        'access_token': t_token,
        'title': safe_text(page_title), 
        'author_name': 'Maps PMM (Test Scoring)',
        'content': content,
        'return_content': False
    }, ensure_ascii=False).encode('utf-8')
    
    r = requests.post('https://api.telegra.ph/createPage', data=payload_str, headers={'Content-Type': 'application/json; charset=utf-8'})
    
    if r.status_code == 200 and r.json()['ok']:
        return r.json()['result']['url']
    print(f"TELEGRA.PH ERROR: {r.text}")
    return None

def send_tg_message(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHANNEL_ID, "text": text, "parse_mode": "HTML", "disable_web_page_preview": True}
    requests.post(url, json=payload)

# ==========================================
# 5. РАБОТА С RSS
# ==========================================
def fetch_rss(feed_url):
    try:
        response = requests.get(feed_url, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return feedparser.parse(response.text)
    except Exception as e:
        print(f"Ошибка RSS ({feed_url[:40]}...): {e}")
        return None

def parse_entry(entry):
    try:
        pub_dt = datetime(*entry.published_parsed[:6])
        if datetime.now() - pub_dt > timedelta(days=7): return None
        
        pub_date = pub_dt.strftime("%d.%m.%Y")
        title = entry.title
        summary = getattr(entry, 'summary', '')
        if not summary: summary = ''
        summary = html.unescape(summary)
        summary = re.sub(r'<[^>]+>', '', summary)
        summary = summary[:500]
        
        source = "Источник"
        link = entry.link
        clean_title = title
        if " - " in title:
            parts = title.rsplit(" - ", 1)
            clean_title = parts[0].strip()
            source = parts[1].strip()
            
        return {
            'date': pub_date,
            'text': f"{clean_title}. {summary}".strip(),
            'title': clean_title,
            'source': source,
            'link': link,
            'domain': link.split('/')[2] if len(link.split('/')) > 2 else ""
        }
    except Exception as e:
        return None

# ==========================================
# 6. СКОРИНГ (Исправленная логика поиска слов)
# ==========================================
def calculate_score(article):
    text = article['text']
    source = article['source']
    domain = article['domain']
    score = 0
    reasons = []
    
    if any(bad in domain for bad in BAD_SOURCES):
        return -999, "Мусорный домен"
        
    for bad_word in BAD_WORDS:
        # Ищем точное совпадение плохих фраз
        if re.search(r'(?i)\b' + re.escape(bad_word) + r'\b', text):
            score -= 10
            reasons.append(f"Мусорное слово: {bad_word}")
            
    word_lists = {
        'map': (MAP_WORDS, 3),
        'nav': (NAVIGATION_WORDS, 2),
        'ai': (AI_WORDS, 2),
        'mkt': (MARKETING_WORDS, 2)
    }
    
    for category, (words, points) in word_lists.items():
        for word in words:
            # ИСПРАВЛЕНО: Убрана правая граница \b. 
            # Теперь 'map' найдет 'Maps', а 'навигац' найдет 'навигационное'
            if re.search(r'(?i)\b' + re.escape(word), text):
                score += points
                reasons.append(f"+{points} {word}")
                break 

    is_good = any(good in source or good in domain for good in GOOD_SOURCES)
    if is_good:
        score += 2
        reasons.append("+2 Источник из белого списка")

    return score, " | ".join(reasons) if reasons else "Нет релевантных слов"

# ==========================================
# 7. УДАЛЕНИЕ ДУБЛИКАТОВ
# ==========================================
def remove_duplicates(articles):
    if not articles: return []
    articles.sort(key=lambda x: x['date'], reverse=True)
    filtered = []
    seen_texts = []
    
    for article in articles:
        text_to_compare = article['text'][:300]
        is_duplicate = False
        
        for seen_text in seen_texts:
            ratio = difflib.SequenceMatcher(None, autojunk=False).ratio(seen_text, text_to_compare)
            if ratio >= DUPLICATE_THRESHOLD:
                is_duplicate = True
                break
                
        if not is_duplicate:
            filtered.append(article)
            seen_texts.append(text_to_compare)
            
    return filtered

# ==========================================
# 8. СБОРКА И ФИЛЬТРАЦИЯ
# ==========================================
def process_feed(feed_url):
    print(f"Получаем RSS: {feed_url[:60]}...")
    feed = fetch_rss(feed_url)
    if not feed: return []
    
    articles = []
    for entry in feed.entries:
        parsed = parse_entry(entry)
        if parsed:
            articles.append(parsed)
    print(f"  -> Получено {len(articles)} статей.")
    return articles

def filter_and_score(articles):
    filtered = []
    
    for article in articles:
        score, reason = calculate_score(article)
        
        if score < MIN_SCORE:
            print(f"  ❌ Отклонено (Score: {score}). {article['title'][:50]}...")
            continue
            
        article['score'] = score
        filtered.append(article)
        print(f"  ✅ Принято (Score: {score}). {article['title'][:50]}...")
        
    return filtered

# ==========================================
# 9. ГЛАВНАЯ ЛОГИКА
# ==========================================
region = sys.argv[1]
period_str = get_week_period()

if region == 'HEADER':
    send_tg_message(f"↧ Дайджест за {period_str} (Test Scoring Algorithm)")
    
else:
    if region == 'RU':
        feeds = RSS_FEEDS_RU
        tg_emoji = "🪆"
        tg_text = "Россия"
        ph_title = f"🇷🇺 Россия | {period_str}"
    elif region == 'WORLD':
        feeds = RSS_FEEDS_WORLD
        tg_emoji = "🌍"
        tg_text = "Мир" 
        ph_title = f"🌍 Мир | {period_str}"
    else:
        feeds = RSS_FEEDS_MARKETING
        tg_emoji = "📺"
        tg_text = "Маркетинг"
        ph_title = f"📺 Маркетинг | {period_str}"

    print(f"\n=== ЗАПУСК ДЛЯ: {region} ===")
    all_articles = []
    seen_links = set()
    
    for feed in feeds:
        articles = process_feed(feed)
        for a in articles:
            if a['link'] not in seen_links:
                seen_links.add(a['link'])
                all_articles.append(a)
                
    scored_articles = filter_and_score(all_articles)
    deduplicated = remove_duplicates(scored_articles)
    deduplicated.sort(key=lambda x: x['score'], reverse=True)
    final_news = deduplicated[:MAX_NEWS]
    
    if not final_news:
        print("Новостей нет, пост пропущен.")
    else:
        formatted_news = [(a['date'], a['title'], a['source'], a['link']) for a in final_news]
        
        ph_url = create_telegraph_page(ph_title, formatted_news)
        
        if ph_url:
            msg = f"<a href='{ph_url}'>{tg_emoji}</a> <a href='{ph_url}'>{tg_text}</a>"
            send_tg_message(msg)
            print(f"Успешно отправлено в ТГ: {ph_url}")
        else:
            text = f"{tg_emoji} {tg_text}\n\n" + "\n\n".join([f"[{a['score']}] <b>{a['date']}</b>\n{a['title']}\n{a['source']} | <a href='{a['link']}'>Читать</a>" for a in final_news])
            send_tg_message(text)
            print("Отправлено текстом (Telegraph вернул ошибку)")
