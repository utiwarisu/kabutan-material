# Kabutan Material Site

株探の上昇率ランキングから上位銘柄を拾い、各銘柄の材料候補を1件ずつ選んで `docs/material.json` と `docs/material.csv` を生成する最小構成です。

## できること
- 株探ランキングからコード取得
- 各銘柄のニュース一覧から材料候補を抽出
- GitHub Pages で一覧表示
- GitHub Actions で定期更新

## 使い方
1. このフォルダを GitHub リポジトリに置く
2. Settings → Pages → Build and deployment → `Deploy from a branch`
3. Branch は `main`、Folder は `/docs`
4. Actions を有効化
5. `Update materials` を `Run workflow` で手動実行

## 補足
- 今は株探ベースです
- TDnet/Yahoo補完は `source` と `quality` を残しているので後から足しやすい構成です
- `NG_WORDS` / `WEAK_WORDS` を調整するとノイズ除去を変えられます
