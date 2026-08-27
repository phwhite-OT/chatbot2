import logging
import os
from typing import Any, Dict, List, Text, Tuple

import psycopg2
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher

logger = logging.getLogger(__name__)


ACNE_STATE_MAP = {
    "red": "赤",
    "white": "白",
    "赤": "赤",
    "白": "白",
    "赤い": "赤",
    "白い": "白",
    "赤ニキビ": "赤",
    "白ニキビ": "白",
}

CATEGORY_MAP = {
    "lotion": "化粧水",
    "emulsion": "乳液",
    "serum": "美容液",
    "cleanser": "洗顔",
    "化粧水": "化粧水",
    "乳液": "乳液",
    "美容液": "美容液",
    "洗顔": "洗顔",
    "洗顔料": "洗顔",
}

PRICE_RANGE_MAP: Dict[str, Tuple[int, int]] = {
    "low": (0, 999),
    "middle": (1000, 1999),
    "high": (2000, 999999999),
    "1000円未満": (0, 999),
    "1000～1999円": (1000, 1999),
    "1000〜1999円": (1000, 1999),
    "2000円以上": (2000, 999999999),
}


class ActionRecommendProducts(Action):
    def name(self) -> Text:
        return "action_recommend_products"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:
        acne_state_raw = tracker.get_slot("acne_state")
        category_raw = tracker.get_slot("product_category")
        price_range_raw = tracker.get_slot("price_range")

        acne_state = ACNE_STATE_MAP.get(str(acne_state_raw))
        category = CATEGORY_MAP.get(str(category_raw))
        price_bounds = PRICE_RANGE_MAP.get(str(price_range_raw))

        if not acne_state or not category or not price_bounds:
            logger.warning(
                "Recommendation conditions are incomplete: acne_state=%r, category=%r, price_range=%r",
                acne_state_raw,
                category_raw,
                price_range_raw,
            )
            dispatcher.utter_message(
                text="条件をうまく受け取れなかったみたい。もう一度最初から選び直してみてね。"
            )
            return []

        min_price, max_price = price_bounds

        db_host = os.getenv("DB_HOST")
        db_name = os.getenv("DB_NAME", "rasa_db")
        db_user = os.getenv("DB_USER")
        db_password = os.getenv("DB_PASSWORD")
        db_port = os.getenv("DB_PORT", "5432")
        db_sslmode = os.getenv("DB_SSLMODE", "prefer")

        if not db_host or not db_user or not db_password:
            logger.error("Database environment variables are not configured.")
            dispatcher.utter_message(
                text="商品データベースの接続設定がまだ完了していないみたい。管理者に確認してみてね。"
            )
            return []

        query = """
            SELECT
                product_name,
                url,
                price
            FROM products
            WHERE acne_symptom = %s
              AND category = %s
              AND price BETWEEN %s AND %s
            ORDER BY id ASC
            LIMIT 3;
        """

        try:
            with psycopg2.connect(
                host=db_host,
                database=db_name,
                user=db_user,
                password=db_password,
                port=db_port,
                sslmode=db_sslmode,
            ) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        query,
                        (acne_state, category, min_price, max_price),
                    )
                    products = cursor.fetchall()

        except psycopg2.Error:
            logger.exception("Failed to query products from rasa_db.")
            dispatcher.utter_message(
                text="商品データの取得中にエラーが起きちゃった。少し時間を置いてもう一度試してみてね。"
            )
            return []

        if not products:
            dispatcher.utter_message(
                text="その条件に合う商品はまだ登録されていないみたい。条件を少し変えて探してみてね。"
            )
            return []

        lines = [
            "教えてくれた条件をもとに、合いそうな商品を選んでみたよ。",
            "",
        ]

        for index, (product_name, url, price) in enumerate(products, start=1):
            lines.append(f"{index}. {product_name}")
            lines.append(f"価格：{price}円")
            if url:
                lines.append(str(url))
            lines.append("")

        dispatcher.utter_message(text="\n".join(lines).strip())
        return []
