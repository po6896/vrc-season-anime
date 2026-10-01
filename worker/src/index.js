// /pv/{枠番号} を今季の PV (YouTube) へ、/music/{枠番号} を音楽リストの曲へ 302 で転送する。
// ワールドには枠番号の固定 URL しか焼けないため、中身の入れ替えをここで行う。
const SITE = "https://po6896.github.io/vrc-season-anime/";

export default {
  async fetch(req) {
    const m = new URL(req.url).pathname.match(/^\/(pv|music)\/(\d+)$/);
    if (!m) return new Response("not found", { status: 404 });
    const res = await fetch(SITE + (m[1] === "pv" ? "playlist.json" : "music.json"), { cf: { cacheTtl: 600 } });
    if (!res.ok) return new Response("playlist unavailable", { status: 502 });
    const data = await res.json();
    // music.json は VizVid の書き出し形式。曲を先頭から通しで数える（ワールド側も同じ数え方）
    const url = m[1] === "pv"
      ? data.items[Number(m[2])]?.youtube
      : data.flatMap((l) => l.entries || [])[Number(m[2])]?.url;
    if (!url) return new Response("empty slot", { status: 404 });
    return Response.redirect(url, 302);
  },
};
