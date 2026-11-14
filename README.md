# server-uptime

Внешняя проверка сайтов сервера 161.97.68.205 раз в 5 минут (GitHub Actions): `check.py`, список — `sites.json`.
Упал — сообщение в Telegram, напоминание раз в 30 мин, поднялся — «снова работает». Состояние — `state.json`.
Секреты: `TG_TOKEN` (бот), `TG_CHAT` (кому писать). Ручной тест: `gh workflow run uptime.yml -f test=true`.
Боты без сайта и контейнеры Docker проверяет сторож на самом сервере (`~/scripts/services-watchdog.py`, cron).
