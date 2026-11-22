import sqlite3
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


DB_PATH = "database.db"


def get_prices(skin_name):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        """
        SELECT recorded_at, skin_price
        FROM skin_prices
        WHERE skin_name = ?
        ORDER BY recorded_at
        """,
        (skin_name,),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def parse_date(s):
    # подстрой формат под то, как ты пишешь recorded_at
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt)
        except ValueError:
            continue
    raise ValueError(f"Не понял формат даты: {s!r}")


def plot_skin(skin_name, log_scale=True):
    rows = get_prices(skin_name)
    if not rows:
        print(f"Нет данных по скину: {skin_name}")
        return

    dates = [parse_date(r[0]) for r in rows]
    prices = [float(r[1]) for r in rows]

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(dates, prices, marker=3, linewidth=1)

    if log_scale:
        ax.set_yscale("log")

    ax.set_title(f"{skin_name} — история цены" + (" (log)" if log_scale else ""))
    ax.set_xlabel("Дата")
    ax.set_ylabel("Цена" + (" (log)" if log_scale else ""))
    ax.grid(True, which="both", alpha=0.3)

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
    fig.autofmt_xdate()

    plt.tight_layout()
    plt.show()


def main():
    skin = 'P90 "Radiation"'
    plot_skin(skin, log_scale=True)


if __name__ == "__main__":
    main()