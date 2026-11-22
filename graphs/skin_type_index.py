import sqlite3

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.ticker import LogLocator, ScalarFormatter, NullLocator
from matplotlib.widgets import TextBox

import numpy as np
import pandas as pd


DB_PATH = "database.db"

# --- типы скинов ---
SKIN_TYPES = ['Пушки', 'Ножи', 'Перчатки', 'Контейнеры', 'Наклейки', 'Брелоки', 'Граффити']

# --- настройки ---
WARMUP = 0


def load_daily_prices(db_path):
    """Возвращает DataFrame: date, skin_name, skin_type, price (средняя за день).
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
    types = pd.read_sql_query("SELECT skin_name, skin_type FROM skins", conn)
    conn.close()

    df["d"] = pd.to_datetime(df["d"], format="%Y-%m-%d", errors="coerce")
    df = df.dropna(subset=["d"])

    # --- ffill пропусков на календарь ---
    wide = df.pivot(index="d", columns="skin_name", values="price")
    full_idx = pd.date_range(wide.index.min(), wide.index.max(), freq="D")
    wide = wide.reindex(full_idx).ffill()

    df = wide.stack().rename("price").reset_index()
    df.columns = ["d", "skin_name", "price"]

    # прикрепить тип скина (свойство скина, не зависит от дня)
    df = df.merge(types, on="skin_name", how="left")
    df = df.sort_values(["skin_name", "d"])
    return df


def build_index(df, warmup=WARMUP, skin_types=None):
    df = df.sort_values(["skin_name", "d"]).copy()

    # фильтр по типам скинов
    if skin_types is not None:
        df = df[df["skin_type"].isin(skin_types)].copy()

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


def plot_index(idx_all, idx_dict=None, ylim=None):
    """
    idx_all  — общий индекс (или None)
    idx_dict — dict {label: idx} для нескольких линий
    """
    fig, ax = plt.subplots(figsize=(12, 7))
    fig.subplots_adjust(bottom=0.22)

    colors = ["steelblue", "darkorange", "seagreen", "crimson",
              "purple", "saddlebrown", "deeppink", "teal"]
    all_lines = []

    # общий индекс
    if idx_all is not None and not idx_all.empty:
        ax.plot(idx_all["d"], idx_all["index"], color="black", linewidth=1.5,
                label="все скины", zorder=4)
        all_lines.append(("все", idx_all))

    # отдельные группы
    if idx_dict:
        for i, (label, idx) in enumerate(idx_dict.items()):
            if idx.empty:
                continue
            color = colors[i % len(colors)]
            ax.plot(idx["d"], idx["index"], color=color, linewidth=1.5,
                    label=label, zorder=3)
            all_lines.append((label, idx))

    ax.set_yscale("log")
    if ylim is not None:
        ax.set_ylim(*ylim)

    ax.set_ylabel("индекс (лог-шкала)")
    ax.set_xlabel("дата")
    ax.set_title("Индекс рынка по типам скинов")
    ax.yaxis.set_major_locator(LogLocator(base=1.25, subs=(1.0,)))
    ax.yaxis.set_major_formatter(ScalarFormatter())
    ax.yaxis.set_minor_locator(NullLocator())
    ax.grid(True, alpha=0.3, which="major")
    ax.legend(loc="upper left")

    # --- клики ---
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

    default_d1 = idx_all["d"].iloc[0].strftime("%Y-%m-%d") if idx_all is not None and not idx_all.empty else "2024-01-01"
    default_d2 = idx_all["d"].iloc[-1].strftime("%Y-%m-%d") if idx_all is not None and not idx_all.empty else "2025-01-01"

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

    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    plt.setp(ax.get_xticklabels(), rotation=45, ha="right")

    fig.tight_layout(rect=[0, 0.15, 1, 1])
    return fig


def inspect_period(df, d1, d2, idx=None, top_n=20):
    """
    Разбирает, что произошло с индексом в диапазоне [d1, d2].
    """
    d1 = pd.Timestamp(d1)
    d2 = pd.Timestamp(d2)

    dfw = df.sort_values(["skin_name", "d"]).copy()
    dfw["ln_price"] = np.log(dfw["price"])
    dfw["r_skin"] = dfw.groupby("skin_name")["ln_price"].diff()
    dfw["age"] = dfw.groupby("skin_name").cumcount()
    dfw["gap"] = dfw.groupby("skin_name")["d"].diff().dt.days

    r = dfw[(dfw["age"] >= WARMUP) & (dfw["gap"] == 1)].dropna(subset=["r_skin"])
    r = r[(r["d"] >= d1) & (r["d"] <= d2)]

    agg = r.groupby("d")["r_skin"].agg(
        n="size",
        median="median",
        mean="mean",
        share_neg=lambda s: (s < 0).mean(),
        min="min",
        max="max",
    )
    print(f"=== ПЕРИОД {d1.date()} .. {d2.date()} ===")
    print(f"\nсводка по дням:")
    print(agg.to_string(float_format=lambda x: f"{x:+.4f}"))

    if idx is not None:
        sub_idx = idx[(idx["d"] >= d1) & (idx["d"] <= d2)]
        print(f"\nдинамика индекса:")
        print(sub_idx[["d", "r", "ln_index", "index", "pct"]].to_string(index=False))

    print(f"\nтоп-{top_n} падений за период:")
    worst = r.nsmallest(top_n, "r_skin")[["d", "skin_name", "price", "r_skin"]]
    print(worst.to_string(index=False))

    print(f"\nтоп-{top_n} ростов за период:")
    best = r.nlargest(top_n, "r_skin")[["d", "skin_name", "price", "r_skin"]]
    print(best.to_string(index=False))

    return agg, r


def find_index_like_skins(df, idx, top_n=20, min_days=100):
    """
    Находит скины, чьи дневные доходности ближе всего к индексу.
    """
    dfw = df.sort_values(["skin_name", "d"]).copy()
    dfw["ln_price"] = np.log(dfw["price"])
    dfw["r_skin"] = dfw.groupby("skin_name")["ln_price"].diff()

    idx_r = idx[["d", "r"]].rename(columns={"r": "r_index"})
    merged = dfw.merge(idx_r, on="d", how="inner").dropna(subset=["r_skin", "r_index"])

    rows = []
    for skin, g in merged.groupby("skin_name"):
        if len(g) < min_days:
            continue

        r_skin = g["r_skin"].values
        r_idx = g["r_index"].values

        corr = np.corrcoef(r_skin, r_idx)[0, 1]
        var_idx = np.var(r_idx, ddof=1)
        beta = np.cov(r_skin, r_idx, ddof=1)[0, 1] / var_idx if var_idx > 0 else np.nan
        rmse = np.sqrt(np.mean((r_skin - r_idx) ** 2))
        te = np.std(r_skin - r_idx, ddof=1)

        rows.append({
            "skin_name": skin,
            "n": len(g),
            "corr": corr,
            "beta": beta,
            "rmse": rmse,
            "te": te,
            "score": corr - te,
        })

    res = pd.DataFrame(rows).sort_values("corr", ascending=False)

    print(f"\n=== ТОП-{top_n} скинов, ближайших к индексу (по corr) ===")
    print(res.head(top_n).to_string(index=False))

    return res


def plot_by_type(df, types=SKIN_TYPES, ylim=None):
    """
    Отдельный график: по одной линии на каждый тип скина.
    df    — результат load_daily_prices (с колонкой skin_type)
    types — список типов
    """
    idx_dict = {}

    for t in types:
        sub = df[df["skin_type"] == t]
        if sub.empty:
            print(f"тип {t!r}: нет данных, пропуск")
            continue
        idx = build_index(sub)
        if idx.empty:
            print(f"тип {t!r}: пустой индекс, пропуск")
            continue
        idx_dict[t] = idx
        print(f"тип {t!r}: {sub['skin_name'].nunique()} скинов, "
              f"индекс ×{idx['index'].iloc[-1]:.3f}")

    fig = plot_index(
        idx_all=None,
        idx_dict=idx_dict,
        ylim=ylim,
    )
    return fig, idx_dict

def main():
    df = load_daily_prices(DB_PATH)

    print("типы скинов в данных (скинов):")
    print(df.groupby("skin_type")["skin_name"].nunique().to_string())

    fig_types, idx_by_type = plot_by_type(df, types=SKIN_TYPES)

    plt.show()

if __name__ == "__main__":
    main()