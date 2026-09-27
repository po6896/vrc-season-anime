"""今季アニメの PV 再生リストとサムネのまとめ画像を作る。

出力 (site/):
  playlist.json   枠番号 -> 作品名・YouTube URL・まとめ画像内の位置
  atlas/{k}.jpg   サムネ COLS x ROWS 枚を 1 枚にまとめた画像 (VRChat の画像読込は 5 秒に 1 回のため)

ワールドには枠番号の固定 URL しか焼けないので、枠数 SLOTS とまとめ画像の枚数は常に一定にする。
データ元: AniList API (非商用・無料)。
"""
import datetime
import io
import json
import time
import urllib.request
from pathlib import Path

from PIL import Image

SLOTS = 240
COLS, ROWS = 6, 4
CELL_W, CELL_H = 341, 480
PER_ATLAS = COLS * ROWS
ATLASES = SLOTS // PER_ATLAS
UA = "vrc-season-anime/0.1"
OUT = Path(__file__).parent / "site"

FIELDS = "id idMal format title{romaji native} coverImage{extraLarge} trailer{id site}"
Q_SEASON = """query($s:MediaSeason,$y:Int,$p:Int){Page(page:$p,perPage:50){pageInfo{hasNextPage}
media(season:$s,seasonYear:$y,type:ANIME,isAdult:false,sort:POPULARITY_DESC){%s}}}""" % FIELDS
# 前の季節から続いている作品。長寿番組や海外作品で溢れないよう日本の TV/ONA に限る
Q_CONT = """query($p:Int,$before:FuzzyDateInt){Page(page:$p,perPage:50){pageInfo{hasNextPage}
media(status:RELEASING,type:ANIME,isAdult:false,countryOfOrigin:"JP",format_in:[TV,TV_SHORT,ONA],
startDate_lesser:$before,sort:POPULARITY_DESC){%s}}}""" % FIELDS


def gql(query, variables):
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request("https://graphql.anilist.co", body, {
        "Content-Type": "application/json", "Accept": "application/json", "User-Agent": UA})
    for i in range(4):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.load(r)["data"]["Page"]
        except urllib.error.HTTPError as e:
            if e.code != 429 or i == 3:
                raise
            time.sleep(int(e.headers.get("Retry-After", 60)))


def fetch_all(query, variables):
    items, page = [], 1
    while True:
        d = gql(query, {**variables, "p": page})
        items += d["media"]
        if not d["pageInfo"]["hasNextPage"]:
            return items
        page += 1
        time.sleep(1)


def current_season(today):
    season = ["WINTER", "SPRING", "SUMMER", "FALL"][(today.month - 1) // 3]
    start = datetime.date(today.year, (today.month - 1) // 3 * 3 + 1, 1)
    return today.year, season, int(start.strftime("%Y%m%d"))


def fit(img):
    """アスペクトを保って枠に収め、余白は黒。"""
    img = img.convert("RGB")
    img.thumbnail((CELL_W, CELL_H), Image.LANCZOS)
    cell = Image.new("RGB", (CELL_W, CELL_H))
    cell.paste(img, ((CELL_W - img.width) // 2, (CELL_H - img.height) // 2))
    return cell


def main():
    year, season, season_start = current_season(datetime.date.today())
    new = fetch_all(Q_SEASON, {"s": season, "y": year})
    seen = {m["id"] for m in new}
    cont = [m for m in fetch_all(Q_CONT, {"before": season_start}) if m["id"] not in seen]

    items = []
    for kind, group in (("new", new), ("continuing", cont)):
        for m in group:
            t = m.get("trailer") or {}
            if t.get("site") == "youtube" and t.get("id"):
                items.append((kind, m))
    items = items[:SLOTS]

    (OUT / "atlas").mkdir(parents=True, exist_ok=True)
    atlases = [Image.new("RGB", (CELL_W * COLS, CELL_H * ROWS)) for _ in range(ATLASES)]
    entries = []
    for slot, (kind, m) in enumerate(items):
        a, c = divmod(slot, PER_ATLAS)
        req = urllib.request.Request(m["coverImage"]["extraLarge"], headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=30) as r:
            atlases[a].paste(fit(Image.open(io.BytesIO(r.read()))), (c % COLS * CELL_W, c // COLS * CELL_H))
        entries.append({
            "slot": slot,
            "kind": kind,
            "title": m["title"]["native"] or m["title"]["romaji"],
            "title_romaji": m["title"]["romaji"],
            "format": m["format"],
            "anilist_id": m["id"],
            "mal_id": m["idMal"],
            "youtube": f"https://www.youtube.com/watch?v={m['trailer']['id']}",
            "atlas": a,
            "cell": c,
        })
        time.sleep(0.2)
    for k, img in enumerate(atlases):
        img.save(OUT / "atlas" / f"{k}.jpg", quality=85)

    (OUT / "playlist.json").write_text(json.dumps({
        "year": year, "season": season,
        "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "count": len(entries), "slots": SLOTS, "atlases": ATLASES,
        "cols": COLS, "rows": ROWS, "cell_w": CELL_W, "cell_h": CELL_H,
        "items": entries,
    }, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{year} {season}: new {len(new)} / continuing {len(cont)} -> {len(entries)} slots with PV")


if __name__ == "__main__":
    main()
