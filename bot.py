name: Maps Bot
on:
  workflow_dispatch:
  schedule:
    # Понедельник в 10:00 МСК (Маркетинг)
    - cron: '0 7 * * 1'
    # Четверг в 10:00 МСК (РФ + Мир)
    - cron: '0 7 * * 4'
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.10'
    - run: pip install feedparser requests
    
    # Ручной тест (прилетят все 3 поста друг за другом)
    - name: Test Marketing
      if: github.event_name == 'workflow_dispatch'
      run: python bot.py MARKETING
    - name: Test RU
      if: github.event_name == 'workflow_dispatch'
      run: python bot.py RU
    - name: Test World
      if: github.event_name == 'workflow_dispatch'
      run: python bot.py WORLD
    
    # Понедельник: Только маркетинг
    - name: Cron Marketing
      if: github.event.schedule == '0 7 * * 1'
      run: python bot.py MARKETING
    
    # Четверг: РФ и Мир
    - name: Cron RU
      if: github.event.schedule == '0 7 * * 4'
      run: python bot.py RU
    - name: Cron World
      if: github.event.schedule == '0 7 * * 4'
      run: python bot.py WORLD
