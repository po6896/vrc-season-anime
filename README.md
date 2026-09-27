# vrc-season-anime

VRChat の動画プレイヤー向けに、今季アニメの PV 再生リストとサムネイルのまとめ画像を週 1 回生成して GitHub Pages に置く。

- `playlist.json` … 枠番号ごとの作品名・YouTube URL・まとめ画像内の位置
- `atlas/{0..9}.jpg` … サムネイル 24 枚 (6x4、1 枚 341x480) を 1 枚にまとめた画像

枠数 240・まとめ画像 10 枚は固定。ワールド側は固定 URL を焼き込み、中身だけが季節ごとに入れ替わる。

データ: [AniList API](https://anilist.co) (非公式の利用。非商用)。サムネイルと PV の権利は各権利者に帰属する。
