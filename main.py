import feedparser
import requests
import re
import sys
import json
import html
import difflib
import urllib.parse
from datetime import datetime, timedelta

# ==========================================
# 1. НАСТРОЙКИ И КОНСТАНТЫ
# ==========================================
TOKEN = '8315240372:AAHSLp4ttCPRwysSmEh8r6otZkMQRcJUuUE'
CHANNEL_ID = '-1004352959600'

MIN_SCORE = 5              # Минимальный балл для попадания в дайджест
MAX_NEWS = 10             # Максимум новостей на раздел
DUPLICATE_THRESHOLD = 0.65    # Порог похожести для удаления дублей
REQUEST_TIMEOUT = 15          # Таймаут для запросов к RSS

# ==========================================
# 2. СЛОВАРИ И ФИЛЬТРЫ
# ==========================================
MAP_WORDS = [
    'карт', 'map', 'гео', 'geo', 'навигац', 'naviga', 'маршрут', 'route', 'poi', 'организаци', 'place', 'отзыв', 'review'
]
NAVIGATION_WORDS = ['навигатор', 'navigator', 'маршрутизатор', 'gps']
AI_WORDS = ['ии', 'ai', 'нейросет', 'машинное обучение', 'gpt', 'gemini', 'llm']
MARKETING_WORDS = ['маркетинг', 'реклам', 'advertis', 'креатив', 'спецпроект', 'кейс', 'лидогенерация', 'таргет', 'воронка']
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
# 3. ОФИЦИАЛЬНЫЕ RSS ИСТОЧНИКИ (Google News + Блоги)
# ==========================================
RSS_FEEDS_RU = [
    "https://news.google.com/rss/search?q=%22Яндекс+Карты%22+OR+%222ГИС%22+OR+%22Google+Карты%22&hl=ru&gl=RU&ceid=RU:ru",
    "https://news.google.com/rss/search?q=%22Яндекс.Карты%22+OR+%22Яндекс+Навигатор%22&hl=ru&gl=RU&ceid=RU:ru",
    "https://news.google.com/rss/search?q=%22картографический+сервис%22+OR+%22геосервис%22&hl=ru&gl=RU&ceid=ru:ru",
    "https://news.google.com/rss/search?q=%22навигационное+приложение%22&hl=ru&gl=RU&ceid=ru:ru"
]

RSS_FEEDS_WORLD = [
    "https://news.google.com/rss/search?q=%22Google+Maps%22+OR+%22Apple+Maps%22+OR+%22Waze%22+OR+%22Mapbox%22+OR+%22HERE+WeGo%22&hl=en&gl=US&ceid=US:en",
    "https://news.google.com/rss/search?q=%22Esri%22+OR+%22TomTom%22+OR+%22OpenStreetMap%22&hl=en&gl=US&ceid=US:en"
]

RSS_FEEDS_MARKETING = [
    "https://news.google.com/rss/search?q=(%22Яндекс+Карты%22+OR+%222ГИС%22)+AND+(%22спецпроект%22+OR+%22рекламная+кампания%22+OR+%22медиаплан%22+OR+%22лидогенерация%22)&hl=ru&gl=RU&ceid=RU:ru"
]

# ==========================================
# 4. ФУТИЛИТЫ ТЕЛЕГРАМА И TELEGRA.PH (ИДЕАЛЬНАЯ СОВМЕСТИМОСТЬ С BOT.PY)
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
        content.append({"tag": "p", "через пробел": [safe_text(title)]})
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
        summary = re.sub(r'<[^>]+>', '', summary) # Убираем HTML теги из саммари
        summary = summary[:500] # Ограничиваем длину саммари для скорости
        
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
        print(f"Ошибка парсинга: {e}")
        return None

# ==========================================
# 6. СКОРИНГ (Логика подсчета баллов)
# ==========================================
def calculate_score(article):
    text = article['text']
    source = article['source']
    domain = article['domain']
    score = 0
    reasons = []
    
    # Блокировка мусорных доменов
    if any(bad in domain for bad in BAD_SOURCES):
        return -999, "Мусорный домен"
        
    # Штрафы за плохие слова
    for bad_word in BAD_WORDS:
        if re.search(r'\b' + re.escape(bad_word) + r'\b', text, re.IGNORECASE):
            score -= 10
            reasons.append(f"Мусорное слово: {bad_word}")
            
    # Поиск по словарям (Плюсы)
    word_lists = {
        'map': (MAP_WORDS, 3),
        'nav': (NAVIGATION_WORDS, 2),
        'ai': (AI_WORDS, 2),
        'mkt': (MARKETING_WORDS, 2)
    }
    
    for category, (words, points) in word_lists.items():
        for word in words:
            if re.search(r'\b' + re.escape(word) + r'\b', text, re.IGNORECASE):
                score += points
                reasons.append(f"+{points} {word}")
                break # Достаточно одного совпадения на категорию

    # Бонусы/Штрафы за источник
    is_good = any(good in source or good in domain for good in GOOD_SOURCES)
    if is_good:
        score += 2
        reasons.append("+2 Источник из белого списка")

    return score, " | ".join(reasons) if reasons else "Нет релевантных слов"

# ==========================================
# 7. УДАЛЕНИЕ ДУБЛИКАТОВ (difflib)
# ==========================================
def remove_duplicates(articles):
    if not articles: return []
    
    # Сортируем по дате (от новых к старым)
    articles.sort(key=lambda x: x['date'], reverse=True)
    
    filtered = []
    seen_texts = []
    
    for article in articles:
        text_to_compare = article['text'][:300] # Сравниваем только начало текста для скорости
        is_duplicate = False
        
        for seen_text in seen_texts:
            # SequenceMatcher оценивает похожесть от 0 до 1
            ratio = difflib.SequenceMatcher(None, autojunk=False).ratio(seen_text, text_to_compare)
            if ratio >= DUPLICATE_THRESHOLD:
                is_duplicate = True
                break
                
        if not is_duplicate:
            filtered.append(article)
            seen_texts.append(text_to_compare)
            
    return filtered

# ==========================================
# ОПРЕДЕЛЕНИЕ РАЗДЕЛА
# ==========================================
def determine_section(article):
    text = article['text'].lower()
    source = article['source'].lower()
    domain = article['domain'].lower()
    
    # Маркетинг: жесткие триггеры
    mkt_keywords = ['рекламная кампания', 'спецпроект для', 'медиаплан', 'воронка продаж', 'лидогенерация']
    for kw in mkt_keywords:
        if kw in text:
            return 'MARKETING'
            
    # Россия: либо домен RU, либо русские слова, но не маркетинг
    ru_markers = ['карт', 'навигац', 'геосервис', '2гис', 'яндекс', 'ситигид', 'навител', 'османд']
    if any(marker in text for marker in ru_markers):
        return 'RU'
        
    # Если ничего не совпало, относим к миру
    return 'WORLD'

# ==========================================
# 8. СБОРКА И ФИЛЬТРАЦИЯ (Главная логика)
# ==========================================
def process_feed(feed_url):
    print(f"Получаем RSS: {feed_url[:50]}...")
    feed = fetch_rss(feed_url)
    if not feed: return []
    
    articles = []
    for entry in feed.entries:
        parsed = parse_entry(entry)
        if parsed:
            articles.append(parsed)
    print(f"Получено {len(articles)} статей.")
    return articles

def filter_and_score(articles):
    filtered = []
    debug_logs = []
    
    for article in articles:
        score, reason = calculate_score(article)
        
        if score < MIN_SCORE:
            debug_logs.append(f"  ❌ Отклонено (Score: {score}). Причина: {reason} -> {article['title'][:40]}...")
            continue
            
        article['score'] = score
        filtered.append(article)
        
    print(f"После фильтрации осталось: {len(filtered)} статей.")
    if debug_logs:
        print("\n--- Лог отладки (только если включен DEBUG) ---")
        for log in debug_logs: print(log)
    
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
        tg_emoji = "🇷🇺"
        tg_text = "Россия"
        ph_title = f"🇷🇺 Россия | {period_str} (Test Scoring)"
    elif region == 'WORLD':
        feeds = RSS_FEEDS_WORLD
        tg_emoji = "🌍"
        tg_text = "Мир" 
        ph_title = f"🌍 Мир | {period_str} (Test Scoring)"
    else:
        feeds = RSS_FEEDS_MARKETING
        tg_emoji = "📺"
        tg_text = "Маркетинг"
        ph_title = f"📺 Маркетинг | {period_str} (Test Scoring)"

    # 1. Сбор
    print(f"\n=== ЗАПУСК МОДЕЛИ СКОРИНГА ДЛЯ: {region} ===")
    all_articles = []
    seen_links = set()
    
    for feed in feeds:
        articles = process_feed(feed)
        for a in articles:
            if a['link'] not in seen_links:
                seen_links.add(a['link'])
                all_articles.append(a)
                
    # 2. Фильтрация и скоринг
    scored_articles = filter_and_score(all_articles)
    
    # 3. Удаление дубликатов
    deduplicated = remove_duplicates(scored_articles)
    print(f"После удаления дубликатов осталось: {len(deduplicated)} статей.")
    
    # 4. Автоопределение разделов (заменяет жесткое разделение в bot.py)
    for article in deduplicated:
        article['section'] = determine_section(article)
    
    # 5. Сортировка по Score (от лучшего к худшему)
    deduplicated.sort(key=lambda x: x['score'], reverse=True)
    
    # 6. Ограничение количества
    final_news = deduplicated[:MAX_NEWS]
    
    # 7. Форматирование
    if not final_news:
        print("Новостей нет, пост пропущен.")
    else:
        # Разбиваем по автоопределенным разделам
        sections = {'RU': [], 'WORLD': [], 'MARKETING': []}
        for art in final_news:
            sections[art['section']].append(art)
            
        for sec, sec_news in sections.items():
            if not sec_news: continue
            
            ph_title_sec = ph_title.replace("(Test Scoring)", f"({sec})")
            ph_url = create_telegraph_page(ph_title_sec, sec_news)
            
            if ph_url:
                msg = f"<a href='{ph_url}'>{tg_emoji}</a> <a href='{ph_url}'>{tg_text} ({sec})</a>"
                send_tg_message(msg)
            else:
                text = f"{tg_emoji} {tg_text}\n\n" + "\n\n".join([f"[{a['score']}] <b>{a['date']}</b>\n{a['title']}\n{a['source']} | <a href='{a['link']}'>Читать</a>" for a in sec_news])
                send_tg_message(text)
