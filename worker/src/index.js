// /pv/{枠番号} を今季の PV (YouTube) へ 302 で転送する。
// ワールドには枠番号の固定 URL しか焼けないため、中身の入れ替えをここで行う。
const PLAYLIST = "https://po6896.github.io/vrc-season-anime/playlist.json";

export default {
  async fetch(req) {
    const m = new URL(req.url).pathname.match(/^\/pv\/(\d+)$/);
    if (!m) return new Response("not found", { status: 404 });
    const res = await fetch(PLAYLIST, { cf: { cacheTtl: 600 } });
    if (!res.ok) return new Response("playlist unavailable", { status: 502 });
    const item = (await res.json()).items[Number(m[1])];
    if (!item) return new Response("empty slot", { status: 404 });
    return Response.redirect(item.youtube, 302);
  },
};
