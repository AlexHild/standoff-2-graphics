import sqlite3

import numpy as np
import pandas as pd

import preferences as pr

DB_PATH = "database.db"

TARGET_COLLECTIONS = pr.preferenced_collections


def load_daily_prices(db_path):
    """Возвращает DataFrame: date, skin_name, collection_name, price (средняя за день).
    Пропуски заполнены последней известной ценой (ffill)."""
    conn = sqlite3.connect(db_path)
    query = """
        SELECT
            date(p.recorded_at) AS d,
            p.skin_name         AS skin_name,
            AVG(p.skin_price)   AS price
        FROM skin_prices p
        GROUP BY date(p.recorded_at), p.skin_name
        ORDER BY d, p.skin_name
    """
    df = pd.read_sql_query(query, conn)
    coll = pd.read_sql_query("SELECT skin_name, collection_name FROM skins", conn)
    conn.close()

    df["d"] = pd.to_datetime(df["d"], format="%Y-%m-%d", errors="coerce")
    df = df.dropna(subset=["d"])

    # --- ffill пропусков на календарь ---
    wide = df.pivot(index="d", columns="skin_name", values="price")

    full_idx = pd.date_range(wide.index.min(), wide.index.max(), freq="D")
    wide = wide.reindex(full_idx)

    wide = wide.ffill()
    df = (
        wide.stack()
            .rename("price")
            .reset_index()
    )
    df.columns = ["d", "skin_name", "price"]

    df = df.merge(coll, on="skin_name", how="left")
    df = df.sort_values(["skin_name", "d"])
    return df


def build_index(df, collections=None):
    df = df.sort_values(["skin_name", "d"]).copy()

    if collections is not None:
        df = df[df["collection_name"].isin(collections)].copy()

    if df.empty:
        return pd.DataFrame(columns=["d", "r", "ln_index", "index", "pct"])

    base = df.groupby("skin_name")["price"].transform("first")
    df["ln_rel"] = np.log(df["price"] / base)

    all_days = df[["d"]].drop_duplicates().sort_values("d")

    daily = df.groupby("d")["ln_rel"].median().rename("ln_rel_med").reset_index()
    daily = all_days.merge(daily, on="d", how="left")
    daily["ln_rel_med"] = daily["ln_rel_med"].ffill()

    daily["r"] = daily["ln_rel_med"].diff()
    daily["ln_index"] = daily["r"].fillna(0).cumsum()
    daily["index"] = np.exp(daily["ln_index"])
    daily["pct"] = np.expm1(daily["r"]) * 100
    return daily


def top_skins_by_last_index(df, collections=None, top_n=100, date=None):
    """
    Топ-N предметов по нормированной цене (price / first_price) на последней дате.
    collections — фильтр по коллекциям
    """
    sub = df.copy()
    if collections is not None:
        sub = sub[sub["collection_name"].isin(collections)]

    sub = sub.sort_values(["skin_name", "d"]).copy()
    if sub.empty:
        return pd.DataFrame(columns=["skin_name", "collection_name", "last_date", "index"])

    first = sub.groupby("skin_name")["price"].transform("first")
    sub["index"] = sub["price"] / first

    if date is not None:
        sub = sub[sub["d"] == pd.Timestamp(date)]
        last = (
            sub[["skin_name", "collection_name", "d", "index"]]
            .rename(columns={"d": "last_date"})
        )
    else:
        last = (
            sub.sort_values("d")
               .groupby("skin_name")
               .tail(1)[["skin_name", "collection_name", "d", "index"]]
               .rename(columns={"d": "last_date"})
        )

    last = last.sort_values("index", ascending=False).reset_index(drop=True)
    return last.head(top_n)


def main():
    df = load_daily_prices(DB_PATH)

    print(f"всего предметов: {len(df)}")

    idx_c = build_index(df, collections=TARGET_COLLECTIONS)

    if idx_c.empty:
        print(f"Нет данных для коллекций: {TARGET_COLLECTIONS}")
        return

    all_items = top_skins_by_last_index(
        df,
        collections=TARGET_COLLECTIONS,
        top_n=500,
    )
    all_items = all_items.sort_values("index", ascending=False).reset_index(drop=True)

    print(f"\n=== ВСЕ предметы из {len(TARGET_COLLECTIONS)} коллекций ===")
    print(f"всего предметов: {len(all_items)}")
    print()
    print(all_items.to_string(index=False))


if __name__ == "__main__":
    main()