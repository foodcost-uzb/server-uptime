"""Внешняя проверка сайтов сервера 161.97.68.205. Сайт жив, если ответил кодом < 500 (страница, редирект, 404 —
программа за nginx отвечает); лежит — нет ответа или 502/503/504. Тревога только после 3 неудач за ~1 мин.
Состояние — state.json в репозитории (коммитится, только когда меняется): тревога при падении, напоминание
раз в 30 мин, «снова работает» при подъёме. Лежит всё сразу — одно сообщение «сервер не отвечает»."""
import json, os, time, urllib.parse, urllib.request, urllib.error
from datetime import datetime, timedelta, timezone

SITES = json.load(open("sites.json", encoding="utf-8"))
REMIND = 1800
TASHKENT = timezone(timedelta(hours=5))


def code(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "server-uptime"})
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self, *a, **k): return None
        return urllib.request.build_opener(NoRedirect).open(req, timeout=20).status
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0


def alive(c): return 0 < c < 500


def send(text):
    data = urllib.parse.urlencode({"chat_id": os.environ["TG_CHAT"], "text": text}).encode()
    try:
        urllib.request.urlopen(f"https://api.telegram.org/bot{os.environ['TG_TOKEN']}/sendMessage", data, timeout=20)
    except Exception as e:
        print("telegram:", e)


def main():
    now, when = time.time(), datetime.now(TASHKENT).strftime("%d.%m %H:%M")
    if os.environ.get("TEST") == "true":
        send(f"🔔 Внешняя проверка подключена ({when} Ташкент): {len(SITES)} сайтов сервера раз в 5 минут.")
    bad = {}
    for name, url in SITES.items():
        for i in range(3):
            c = code(url)
            if alive(c): break
            if i < 2: time.sleep(20)
        print(f"{c:>3} {name}")
        if not alive(c):
            bad[name] = c
    try:
        state = json.load(open("state.json"))
    except (FileNotFoundError, ValueError):
        state = {}
    new = [n for n in bad if n not in state]
    still = [n for n in bad if n in state and now - state[n]["told"] >= REMIND]
    back = [n for n in state if n not in bad]
    fmt = lambda ns: "\n".join(f"• {n} — {'нет ответа' if not bad.get(n) else 'код ' + str(bad[n])}" for n in ns)
    whole = len(bad) == len(SITES)
    if new or still:
        if whole:
            send(f"🚨 Сервер 161.97.68.205 не отвечает ({when} Ташкент) — лежат все {len(SITES)} сайтов и боты на нём."
                 "\nЕсли не поднимется сам: my.contabo.com → VPS 161.97.68.205 → Restart.")
        else:
            head = "🚨 Не отвечает" if new else "⏳ Всё ещё не отвечает"
            send(f"{head} ({when} Ташкент):\n{fmt(new + still)}")
    if back:
        send(f"✅ Снова работает ({when} Ташкент):\n" + "\n".join(f"• {n}" for n in back))
    out = {n: {"since": state.get(n, {}).get("since", now),
               "told": now if (n in new or n in still) else state[n]["told"]} for n in bad}
    if out != state:
        json.dump(out, open("state.json", "w"), ensure_ascii=False, indent=1)
        open(os.environ.get("GITHUB_OUTPUT", "/dev/null"), "a").write("changed=true\n")


main()
