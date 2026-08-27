# chatbot2

Rasaを使ったニキビ向け美容商品推薦チャットボットです。

## 現在の会話フロー

1. 悩みを聞く（現在はニキビのみ実装）
2. ニキビの状態を聞く（赤 / 白）
3. 商品カテゴリを聞く（化粧水 / 乳液 / 美容液 / 洗顔）
4. 価格帯を聞く（1000円未満 / 1000〜1999円 / 2000円以上）
5. `rasa_db.products` から条件一致商品を最大3件取得
6. 商品名・価格・URLを返す

## 主なファイル

- `domain.yml`: intent、slot、ボタン、返答、custom action定義
- `data/nlu.yml`: NLU学習データ
- `data/stories.yml`: ニキビ相談の会話フロー
- `data/rules.yml`: 挨拶ルール
- `actions/actions.py`: `rasa_db` を検索して商品を返す処理
- `sql/init_products.sql`: 商品テーブル作成SQL
- `.env.example`: DB接続用環境変数の例

## AWSでの準備

### 1. リポジトリを取得

```bash
git clone https://github.com/phwhite-OT/chatbot2.git
cd chatbot2
```

実装ブランチを使う場合:

```bash
git checkout feature/rasa-acne-flow
```

### 2. Action Server用ライブラリ

既存のRasa環境を有効化したうえで実行します。

```bash
pip install -r requirements.txt
```

### 3. DB接続情報

実際のパスワードはGitHubに保存せず、AWS側で環境変数として設定します。

```bash
export DB_HOST="<DBホスト>"
export DB_NAME="rasa_db"
export DB_USER="<DBユーザー>"
export DB_PASSWORD="<DBパスワード>"
export DB_PORT="5432"
export DB_SSLMODE="prefer"
```

### 4. 商品テーブル

`rasa_db` に `sql/init_products.sql` を実行します。

テーブル構成:

| 列 | 内容 |
| --- | --- |
| `id` | 商品ID |
| `product_name` | 商品名 |
| `url` | 商品URL |
| `price` | 価格（整数・円） |
| `acne_symptom` | `赤` または `白` |
| `category` | `化粧水` / `乳液` / `美容液` / `洗顔` |

商品は例として次の形式で追加できます。

```sql
INSERT INTO products
(product_name, url, price, acne_symptom, category)
VALUES
('商品名', 'https://example.com/product', 1480, '赤', '化粧水');
```

### 5. Rasaの確認・学習

```bash
rasa data validate
rasa train --force
```

### 6. 起動

ターミナル1:

```bash
rasa run actions
```

ターミナル2:

```bash
rasa run --enable-api --cors "*"
```

ターミナルだけで試す場合は、Rasaサーバーの代わりに以下でも確認できます。

```bash
rasa shell
```

## DB検索条件

Rasa内部では以下のslotを保持します。

- `acne_state`: `red` / `white`
- `product_category`: `lotion` / `emulsion` / `serum` / `cleanser`
- `price_range`: `low` / `middle` / `high`

`actions/actions.py` で日本語のDB値へ変換してから検索します。

例:

```text
red + lotion + middle
```

はDB上では、

```text
赤 + 化粧水 + 1000〜1999円
```

として検索されます。

検索結果は `id` の昇順で最大3商品です。紹介したい順に商品を登録すれば、その順番を基本の表示順として使えます。

## セキュリティ

DBパスワードやAWS認証情報をGitHubへコミットしないでください。`.env` はGit管理対象外です。
