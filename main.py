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

MIN_SCORE = 3              # Порог скоринга (3 позволяет брать базовые упоминания карт)
MAX_NEWS = 10              # Максимум новостей на раздел
DUPLICATE_THRESHOLD = 0.65 # Порог похожести для удаления дублей
REQUEST_TIMEOUT = 15       # Таймаут для запросов к RSS

# ==========================================
# 2. СЛОВАРИ И ФИЛЬТРЫ (Из оригинального main.py)
# ==========================================
MAP_WORDS = [
    'карт', 'map', 'гео', 'geo', 'навигац', 'naviga', 'маршрут', 'route', 'poi', 'организаци', 'place', 'отзыв', 'review'
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
# 3. RSS ИСТОЧНИКИ (Интегрированы запросы из bot.py)
# ==========================================
RSS_FEEDS_RU = [
    # Строгий поиск (Глаголы и действия)
    "https://news.google.com/rss/search?q=(%22Яндекс+Карты%22+OR+%22Яндекс.Карты%22+OR+%22Яндекс+Навигатор%22+OR+%222ГИС%22+OR+%22ДубльГИС%22+OR+%222GIS%22)+AND+(%22запустил%22+OR+%22обновил%22+OR+%22добавил%22+OR+%22интегрировал%22+OR+%22выпустил%22+OR+%22представил%22+OR+%22изменил%22+OR+%22закрыл%22+OR+%22открыл%22)&hl=ru&gl=RU&ceid=RU:ru",
    # Отступной запрос 1 (Основные бренды)
    "https://news.google.com/rss/search?q=%22Яндекс+Карты%22+OR+%22Яндекс.Карты%22+OR+%22Яндекс+Навигатор%22+OR+%222ГИС%22+OR+%22ДубльГИС%22+OR+%222GIS%22&hl=ru&gl=RU&ceid=RU:ru",
    # Отступной запрос 2 (Вторичные бренды и сервисы)
    "https://news.google.com/rss/search?q=%22Google+Карты%22+OR+%22Google+Maps%22+OR+%22СитиГид%22+OR+%22CityGuide%22+OR+%22Навител%22+OR+%22Organic+Maps%22+OR+%22Maps.me%22+OR+%22OsmAnd%22+OR+%22Яндекс+Бизнес%22+OR+%22Google+Business%22+OR+%22Foursquare%22+OR+%22картографический+сервис%22+OR+%22геосервис%22&hl=ru&gl=RU&ceid=RU:ru"
]

RSS_FEEDS_WORLD = [
    # Строгий поиск (Действия на английском)
    "https://news.google.com/rss/search?q=(%22Google+Maps%22+OR+%22Apple+Maps%22+OR+%22Waze%22+OR+%22Mapbox%22+OR+%22Esri%22+OR+%22HERE+WeGo%22+OR+%22TomTom%22)+AND+(%22launched%22+OR+%22announced%22+OR+%22updated%22+OR+%22added%22+OR+%22integrated%22+OR+%22banned%22+OR+%22partnered%22+OR+%22integration%22+OR+%22deployment%22+OR+%22feature%22)&hl=en&gl=US&ceid=US:en",
    # Отступной запрос 1 (Западные бренды)
    "https://news.google.com/rss/search?q=%22Google+Maps%22+OR+%22Apple+Maps%22+OR+%22Waze%22+OR+%22Foursquare%22+OR+%22HERE+WeGo%22+OR+%22HERE+Technologies%22+OR+%22TomTom%22+OR+%22Sygic%22+OR+%22Mapbox%22+OR+%22Esri%22&hl=en&gl=US&ceid=US:en",
    # Отступной запрос 2 (Азиатские и другие бренды)
    "https://news.google.com/rss/search?q=%22KakaoMap%22+OR+%22Naver+Map%22+OR+%22Baidu+Maps%22+OR+%22Gaode+Maps%22+OR+%22Amap%22+OR+%22Navitime%22+OR+%22MapmyIndia%22+OR+%22GrabMaps%22+OR+%22Gojek+Maps%22+OR+%22OpenStreetMap%22&hl=en&gl=US&ceid=US:en"
]

RSS_FEEDS_MARKETING = [
    # Строгий поиск (Жесткие маркетинговые триггеры)
    "https://news.google.com/rss/search?q=(%22Яндекс+Карты%
