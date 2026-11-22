import sqlite3
from datetime import datetime

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import LogLocator, ScalarFormatter, NullLocator
from matplotlib.widgets import TextBox

import numpy as np
import pandas as pd


DB_PATH = "database.db"

# --- настройки ---
WARMUP = 0

# какую коллекцию смотреть
TARGET_COLLECTION = "Revenge"


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


def build_index(df, warmup=WARMUP, collections=None):
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


def top_skins_by_last_index(df, collections=None, top_n=10, date=None):
    """
    Топ-N скинов по нормированной цене (price / first_price) на последней дате.
    Если collections задан — только скины из этих коллекций.
    Если date задан — на конкретную дату (строки YYYY-MM-DD).
    Возвращает DataFrame: skin_name, collection_name, last_date, index.
    """
    sub = df.copy()
    if collections is not None:
        sub = sub[sub["collection_name"].isin(collections)]

    sub = sub.sort_values(["skin_name", "d"]).copy()
    if sub.empty:
        return pd.DataFrame(columns=["skin_name", "collection_name", "last_date", "index"])

    # нормировка каждого скина на первую цену
    first = sub.groupby("skin_name")["price"].transform("first")
    sub["index"] = sub["price"] / first

    if date is not None:
        # только указанная дата
        sub = sub[sub["d"] == pd.Timestamp(date)]
        last = (
            sub[["skin_name", "collection_name", "d", "index"]]
            .rename(columns={"d": "last_date"})
        )
    else:
        # последняя доступная дата каждого скина
        last = (
            sub.sort_values("d")
               .groupby("skin_name")
               .tail(1)[["skin_name", "collection_name", "d", "index"]]
               .rename(columns={"d": "last_date"})
        )

    last = last.sort_values("index", ascending=False).reset_index(drop=True)
    return last.head(top_n)


def _add_interactivity(fig, ax, all_lines, default_d1, default_d2):
    """Клики мышью и TextBox: ×N между двумя точками / двумя датами."""
    state = {"clicks": [], "artists": [], "press_xy": None, "dragged": False}

    def onclick(event):
        if event.button != 1:
            return
        if event.inaxes != ax or event.xdata is None or event.ydata is None:
            return
        if state["dragged"]:
            state["dragged"] = False
            return

        t = mdates.num2date(event.xdata).replace(tzinfo=None)

        best = None
        for label, idx in all_lines:
            if idx.empty:
                continue
            i = (idx["d"] - t).abs().idxmin()
            dist = abs((idx["d"].iloc[i] - t).total_seconds())
            if best is None or dist < best[0]:
                best = (dist, label, idx, i)

        if best is None:
            return

        _, label, idx, i = best
        state["clicks"].append((label, idx, i))

        sc = ax.scatter(idx["d"].iloc[i], idx["index"].iloc[i],
                        color="black", s=50, zorder=6)
        state["artists"].append(sc)

        if len(state["clicks"]) == 2:
            (l1, idx1, i1), (l2, idx2, i2) = state["clicks"]
            v1 = idx1["index"].iloc[i1]
            v2 = idx2["index"].iloc[i2]
            ratio = v2 / v1
            d1 = idx1["d"].iloc[i1].strftime("%Y-%m-%d")
            d2 = idx2["d"].iloc[i2].strftime("%Y-%m-%d")
            ax.set_title(f"{l1} {d1} ×{v1:.3f} → {l2} {d2} ×{v2:.3f} = ×{ratio:.3f}")

            for a in state["artists"]:
                a.remove()
            state["artists"].clear()
            state["clicks"].clear()

        fig.canvas.draw_idle()

    def on_press(event):
        if event.button == 1 and event.inaxes == ax:
            state["press_xy"] = (event.x, event.y)
            state["dragged"] = False

    def on_motion(event):
        if state["press_xy"] is None:
            return
        x0, y0 = state["press_xy"]
        if abs(event.x - x0) > 3 or abs(event.y - y0) > 3:
            state["dragged"] = True

    def on_release(event):
        state["press_xy"] = None

    fig.canvas.mpl_connect("button_press_event", on_press)
    fig.canvas.mpl_connect("motion_notify_event", on_motion)
    fig.canvas.mpl_connect("button_release_event", on_release)
    fig.canvas.mpl_connect("button_press_event", onclick)

    # --- TextBox ---
    ax_d1 = fig.add_axes([0.15, 0.08, 0.20, 0.04])
    ax_d2 = fig.add_axes([0.45, 0.08, 0.20, 0.04])

    tb1 = TextBox(ax_d1, "Дата 1: ", initial=default_d1)
    tb2 = TextBox(ax_d2, "Дата 2: ", initial=default_d2)

    state_tb = {"artists": []}

    def apply_dates(_):
        for a in state_tb["artists"]:
            a.remove()
        state_tb["artists"].clear()

        try:
            d1 = pd.Timestamp(tb1.text.strip())
            d2 = pd.Timestamp(tb2.text.strip())
        except Exception:
            ax.set_title("неверный формат даты (нужно YYYY-MM-DD)")
            fig.canvas.draw_idle()
            return

        parts = []
        for label, idx in all_lines:
            if idx.empty:
                continue
            i1 = (idx["d"] - d1).abs().idxmin()
            i2 = (idx["d"] - d2).abs().idxmin()
            v1, v2 = idx["index"].iloc[i1], idx["index"].iloc[i2]
            sc = ax.scatter([idx["d"].iloc[i1], idx["d"].iloc[i2]],
                            [v1, v2], color="black", s=40, zorder=6)
            state_tb["artists"].append(sc)
            parts.append(f"{label} ×{v2/v1:.3f}")

        ax.set_title("  |  ".join(parts))
        fig.canvas.draw_idle()

    tb1.on_submit(apply_dates)
    tb2.on_submit(apply_dates)


def plot_collection_skins(df, collection, idx_collection=None, ylim=None):
    """
    Рисует ВСЕ скины одной коллекции (нормированные на первый день)
    + индекс коллекции (медиана) чёрным.
    """
    sub = df[df["collection_name"] == collection].copy()
    if sub.empty:
        print(f"нет скинов в коллекции {collection}")
        return None

    sub = sub.sort_values(["skin_name", "d"])
    first = sub.groupby("skin_name")["price"].transform("first")
    sub["norm"] = sub["price"] / first

    fig, ax = plt.subplots(figsize=(12, 7))
    fig.subplots_adjust(bottom=0.22)

    all_lines = []

    skins = sub["skin_name"].unique()
    cmap = plt.get_cmap("tab20")
    for i, skin in enumerate(skins):
        s = sub[sub["skin_name"] == skin]
        color = cmap(i % 20)
        ax.plot(s["d"], s["norm"], color=color, linewidth=1, alpha=0.7, label=skin)
        s2 = s.rename(columns={"norm": "index"})
        all_lines.append((skin, s2))

    if idx_collection is not None and not idx_collection.empty:
        ax.plot(idx_collection["d"], idx_collection["index"], color="black",
                linewidth=2.5, label=f"{collection} (index)", zorder=5)
        all_lines.append((f"{collection} (index)", idx_collection))

    ax.set_yscale("log")
    if ylim is not None:
        ax.set_ylim(*ylim)

    ax.set_ylabel("нормированная цена (лог-шкала)")
    ax.set_xlabel("дата")
    ax.set_title(f"Коллекция {collection}: скины + индекс")
    ax.yaxis.set_major_locator(LogLocator(base=1.25, subs=(1.0,)))
    ax.yaxis.set_major_formatter(ScalarFormatter())
    ax.yaxis.set_minor_locator(NullLocator())
    ax.grid(True, alpha=0.3, which="major")
    ax.legend(loc="upper left", fontsize=7, ncol=2)

    default_d1 = idx_collection["d"].iloc[0].strftime("%Y-%m-%d") if idx_collection is not None and not idx_collection.empty else "2024-01-01"
    default_d2 = idx_collection["d"].iloc[-1].strftime("%Y-%m-%d") if idx_collection is not None and not idx_collection.empty else "2025-01-01"

    _add_interactivity(fig, ax, all_lines, default_d1, default_d2)

    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    fig.tight_layout(rect=[0, 0.15, 1, 1])
    return fig


def main():
    df = load_daily_prices(DB_PATH)

    # индекс выбранной коллекции
    idx_c = build_index(df, collections=[TARGET_COLLECTION])

    if idx_c.empty:
        print(f"Нет данных для коллекции {TARGET_COLLECTION}")
        return

    # --- все скины коллекции по индексу на последней дате ---
    all_skins = top_skins_by_last_index(
        df, collections=[TARGET_COLLECTION], top_n=10_000
    )
    all_skins = all_skins.sort_values("index", ascending=False).reset_index(drop=True)

    print(f"\n=== ВСЕ скины коллекции {TARGET_COLLECTION} (от лучшего к худшему) ===")
    print(f"всего: {len(all_skins)}")
    print(all_skins.to_string(index=False))

    fig = plot_collection_skins(df, TARGET_COLLECTION, idx_c)
    plt.show()


if __name__ == "__main__":
    main()