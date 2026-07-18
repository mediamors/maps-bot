name: Maps Bot
on:
  workflow_dispatch:
  schedule:
    - cron: '0 7 * * 4'
    - cron: '0 11 * * 6'
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: '3.10'
    - run: pip install feedparser requests
    
    # Блок ручного теста (Выполняет ОБА скрипта друг за другом)
    - name: Test RU
      if: github.event_name == 'workflow_dispatch'
      run: python bot.py RU
    - name: Test World
      if: github.event_name == 'workflow_dispatch'
      run: python bot.py WORLD
    
    # Блоки для автоматической работы по расписанию
    - name: Cron RU
      if: github.event.schedule == '0 7 * * 4'
      run: python bot.py RU
    - name: Cron World
      if: github.event.schedule == '0 11 * * 6'
      run: python bot.py WORLD
