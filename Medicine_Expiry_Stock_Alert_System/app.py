from datetime import date, datetime, timedelta
from pathlib import Path
import sqlite3
import io
import csv

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from flask import Flask, render_template, request, redirect, url_for, flash, send_file, abort

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "medicines.db"
ALLOWED_DATE_FORMAT = "%Y-%m-%d"

app = Flask(__name__)
app.secret_key = "change-this-for-a-real-deployment"
app.config["MAX_CONTENT_LENGTH"] = 1 * 1024 * 1024  # 1 MB request limit for forms/imports
EXPIRY_WARNING_DAYS = 30
DEFAULT_LOW_STOCK = 10


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS medicines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                batch_number TEXT NOT NULL DEFAULT '',
                quantity INTEGER NOT NULL CHECK(quantity >= 0),
                expiry_date TEXT NOT NULL,
                min_stock INTEGER NOT NULL DEFAULT 10 CHECK(min_stock >= 0),
                notes TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
        """)
        conn.commit()


def parse_date(value):
    try:
        return datetime.strptime(value, ALLOWED_DATE_FORMAT).date()
    except (TypeError, ValueError):
        return None


def get_medicines():
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM medicines ORDER BY expiry_date ASC, name ASC").fetchall()
    result = []
    today = date.today()
    for row in rows:
        item = dict(row)
        expiry = parse_date(item["expiry_date"])
        days_left = (expiry - today).days if expiry else None
        item["days_left"] = days_left
        if days_left is not None and days_left < 0:
            item["expiry_status"] = "Expired"
        elif days_left is not None and days_left <= EXPIRY_WARNING_DAYS:
            item["expiry_status"] = "Expiring soon"
        else:
            item["expiry_status"] = "OK"
        item["low_stock"] = item["quantity"] <= item["min_stock"]
        result.append(item)
    return result


@app.route("/")
def index():
    medicines = get_medicines()
    total_items = len(medicines)
    total_units = sum(m["quantity"] for m in medicines)
    expired_count = sum(m["expiry_status"] == "Expired" for m in medicines)
    expiring_count = sum(m["expiry_status"] == "Expiring soon" for m in medicines)
    low_stock_count = sum(m["low_stock"] for m in medicines)
    return render_template(
        "index.html",
        medicines=medicines,
        total_items=total_items,
        total_units=total_units,
        expired_count=expired_count,
        expiring_count=expiring_count,
        low_stock_count=low_stock_count,
        today=date.today().isoformat(),
        warning_days=EXPIRY_WARNING_DAYS
    )


@app.route("/add", methods=["POST"])
def add_medicine():
    name = request.form.get("name", "").strip()
    batch = request.form.get("batch_number", "").strip()
    quantity_raw = request.form.get("quantity", "").strip()
    expiry_raw = request.form.get("expiry_date", "").strip()
    min_stock_raw = request.form.get("min_stock", str(DEFAULT_LOW_STOCK)).strip()
    notes = request.form.get("notes", "").strip()

    if not name or len(name) > 120:
        flash("Medicine name is required and must be 120 characters or fewer.", "error")
        return redirect(url_for("index"))
    try:
        quantity = int(quantity_raw)
        min_stock = int(min_stock_raw)
        if quantity < 0 or min_stock < 0:
            raise ValueError
    except ValueError:
        flash("Quantity and minimum stock must be whole numbers greater than or equal to zero.", "error")
        return redirect(url_for("index"))
    expiry = parse_date(expiry_raw)
    if expiry is None:
        flash("Please provide a valid expiry date.", "error")
        return redirect(url_for("index"))
    if len(batch) > 80 or len(notes) > 500:
        flash("Batch number or notes are too long.", "error")
        return redirect(url_for("index"))

    with get_db() as conn:
        conn.execute(
            """INSERT INTO medicines
               (name, batch_number, quantity, expiry_date, min_stock, notes, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, batch, quantity, expiry.isoformat(), min_stock, notes, datetime.now().isoformat(timespec="seconds"))
        )
        conn.commit()
    flash(f"{name} added to inventory.", "success")
    return redirect(url_for("index"))


@app.route("/delete/<int:medicine_id>", methods=["POST"])
def delete_medicine(medicine_id):
    with get_db() as conn:
        conn.execute("DELETE FROM medicines WHERE id = ?", (medicine_id,))
        conn.commit()
    flash("Medicine record deleted.", "success")
    return redirect(url_for("index"))


@app.route("/export.csv")
def export_csv():
    medicines = get_medicines()
    output = io.StringIO()
    fields = ["id", "name", "batch_number", "quantity", "expiry_date", "min_stock", "expiry_status", "days_left", "low_stock", "notes", "created_at"]
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(medicines)
    memory = io.BytesIO(output.getvalue().encode("utf-8-sig"))
    memory.seek(0)
    return send_file(memory, mimetype="text/csv", as_attachment=True, download_name="medicine_inventory.csv")


@app.route("/chart.png")
def chart():
    medicines = get_medicines()
    if not medicines:
        medicines = []
    df = pd.DataFrame(medicines)
    fig, ax = plt.subplots(figsize=(8, 4.5))
    sns.set_theme(style="whitegrid")
    if not df.empty:
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
        chart_df = df.sort_values("quantity", ascending=False).head(10)
        sns.barplot(data=chart_df, x="quantity", y="name", ax=ax)
        ax.set_title("Top 10 medicines by current stock")
        ax.set_xlabel("Units in stock")
        ax.set_ylabel("Medicine")
    else:
        ax.text(0.5, 0.5, "Add medicines to see stock analytics", ha="center", va="center")
        ax.set_axis_off()
    fig.tight_layout()
    image = io.BytesIO()
    fig.savefig(image, format="png", dpi=140, bbox_inches="tight")
    plt.close(fig)
    image.seek(0)
    return send_file(image, mimetype="image/png")


@app.route("/analytics")
def analytics():
    medicines = get_medicines()
    quantities = np.array([m["quantity"] for m in medicines], dtype=float)
    average_stock = float(np.mean(quantities)) if quantities.size else 0.0
    median_stock = float(np.median(quantities)) if quantities.size else 0.0
    return {
        "medicine_records": len(medicines),
        "total_units": int(np.sum(quantities)) if quantities.size else 0,
        "average_units_per_record": round(average_stock, 2),
        "median_units_per_record": round(median_stock, 2),
        "low_stock_records": sum(m["low_stock"] for m in medicines),
        "expired_records": sum(m["expiry_status"] == "Expired" for m in medicines),
        "expiring_soon_records": sum(m["expiry_status"] == "Expiring soon" for m in medicines),
    }


@app.errorhandler(413)
def too_large(_error):
    flash("Request too large.", "error")
    return redirect(url_for("index"))


init_db()

if __name__ == "__main__":
    # Local college demo only. Do not use debug mode on a public production server.
    app.run(debug=True)
