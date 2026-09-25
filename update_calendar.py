import urllib.request
import re
from pathlib import Path

SOURCE = "https://api-prod.mancity.com/fixturecalendars/v1/DownloadCalendar?calendar=mens&lang=en"
OUTPUT = Path("man-city-calendar.ics")

TEAM_MAP = {
    "Manchester City": "曼城", "Man City": "曼城",
    "Liverpool": "利物浦", "Paris Saint-Germain": "巴黎聖日耳曼", "PSG": "巴黎聖日耳曼",
    "Ipswich Town": "伊普斯維奇", "AEK Athens": "AEK 雅典",
    "Aston Villa": "阿斯頓維拉", "Brighton and Hove Albion": "布萊頓",
    "Brighton & Hove Albion": "布萊頓", "RB Leipzig": "RB 萊比錫",
    "Nottingham Forest": "諾丁漢森林", "Fulham": "富勒姆", "Napoli": "拿坡里",
    "Arsenal": "兵工廠", "Leeds United": "里茲聯", "Brentford": "布倫特福德",
    "Barcelona": "巴塞隆納", "FC Barcelona": "巴塞隆納", "Chelsea": "切爾西",
    "Hull City": "赫爾城", "Newcastle United": "紐卡索聯", "Everton": "艾佛頓",
    "Tottenham Hotspur": "托特納姆熱刺", "Tottenham": "托特納姆熱刺",
    "RC Lens": "朗斯", "Sporting CP": "里斯本競技", "Coventry City": "考文垂",
    "Manchester United": "曼聯", "AFC Bournemouth": "伯恩茅斯", "Bournemouth": "伯恩茅斯",
    "Crystal Palace": "水晶宮", "Sunderland": "桑德蘭", "Porto": "波爾圖", "FC Porto": "波爾圖",
}

COMP_MAP = {
    "Premier League": "英超",
    "UEFA Champions League": "歐冠",
    "Champions League": "歐冠",
    "FA Cup": "足總盃",
    "Carabao Cup": "聯賽盃",
    "League Cup": "聯賽盃",
    "Community Shield": "社區盾",
}

def unfold(s):
    return re.sub(r"\r?\n[ \t]", "", s)

def esc(v):
    return v.replace("\\", "\\\\").replace(";", r"\;").replace(",", r"\,").replace("\n", r"\n")

def translate(text):
    for a, b in sorted(TEAM_MAP.items(), key=lambda x: -len(x[0])):
        text = text.replace(a, b)
    for a, b in sorted(COMP_MAP.items(), key=lambda x: -len(x[0])):
        text = text.replace(a, b)
    return text

req = urllib.request.Request(SOURCE, headers={"User-Agent": "man-city-calendar-github-action/1.0"})
raw = urllib.request.urlopen(req, timeout=30).read().decode("utf-8-sig", errors="replace")
raw = unfold(raw)

events = re.findall(r"BEGIN:VEVENT\r?\n(.*?)\r?\nEND:VEVENT", raw, flags=re.S)
if not events:
    raise RuntimeError("Official Manchester City feed returned no events.")

out = [
    "BEGIN:VCALENDAR",
    "VERSION:2.0",
    "PRODID:-//tracy50//Manchester City TW Calendar//ZH-TW",
    "CALSCALE:GREGORIAN",
    "METHOD:PUBLISH",
    "X-WR-CALNAME:曼城",
    "X-WR-TIMEZONE:Asia/Taipei",
    "X-PUBLISHED-TTL:PT1H",
]

for body in events:
    lines = body.splitlines()
    props = []
    has_alarm = False
    for line in lines:
        if line.startswith("BEGIN:VALARM"):
            has_alarm = True
        if line.startswith("SUMMARY:"):
            line = "SUMMARY:" + esc(translate(line[len("SUMMARY:"):]))
        elif line.startswith("DESCRIPTION:"):
            line = "DESCRIPTION:" + esc(translate(line[len("DESCRIPTION:"):]))
        elif line.startswith("LOCATION:"):
            line = "LOCATION:" + esc(translate(line[len("LOCATION:"):]))
        elif line.startswith("CATEGORIES:"):
            line = "CATEGORIES:" + esc(translate(line[len("CATEGORIES:"):]))
        props.append(line)

    out.append("BEGIN:VEVENT")
    out.extend(props)
    if not has_alarm:
        out += [
            "BEGIN:VALARM",
            "TRIGGER:-PT30M",
            "ACTION:DISPLAY",
            "DESCRIPTION:曼城比賽將於 30 分鐘後開賽",
            "END:VALARM",
        ]
    out.append("END:VEVENT")

out.append("END:VCALENDAR")
OUTPUT.write_text("\r\n".join(out) + "\r\n", encoding="utf-8")
print(f"Updated {OUTPUT} from official Manchester City feed ({len(events)} events).")
