# Medicine Expiry & Stock Alert System

A beginner-friendly college mini-project built with Python Flask, SQLite, HTML, CSS, JavaScript, Pandas, NumPy, Matplotlib and Seaborn.

## Features
- Add medicine records with name, batch number, quantity, expiry date, minimum stock threshold and notes.
- Automatic status labels for expired medicines and medicines expiring within 30 days.
- Low-stock warnings when quantity is less than or equal to the configured threshold.
- Dashboard cards for total records, total units, expired, expiring-soon and low-stock records.
- Search inventory by medicine name or batch number.
- Delete inventory records.
- Export inventory as CSV.
- Stock chart generated with Pandas, Matplotlib and Seaborn.
- JSON analytics endpoint using NumPy.

## Requirements
- Python 3.10 or newer recommended
- Internet connection for the first-time dependency installation

## Setup on Windows (VS Code / PowerShell)

Open a terminal in the folder containing `app.py`, then run:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

If PowerShell blocks environment activation, use Command Prompt instead:

```bat
venv\Scripts\activate.bat
python -m pip install -r requirements.txt
python app.py
```

Open this URL in your browser:

http://127.0.0.1:5000

Keep the terminal open while using the app. Press `Ctrl+C` to stop the server.

## Setup on macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
python app.py
```

Then open http://127.0.0.1:5000

## Files created automatically
- `medicines.db`: SQLite database
- The chart is generated in memory at `/chart.png`
- CSV export is generated when you click Export CSV

To reset the demo inventory, stop the server and delete `medicines.db`; the database will be recreated next time the app starts. This deletes the saved records.

## Project structure

```text
Medicine_Expiry_Stock_Alert_System/
├── app.py
├── requirements.txt
├── README.md
├── templates/
│   └── index.html
└── static/
    ├── style.css
    └── script.js
```

## How it works
1. The HTML form submits medicine details to Flask.
2. Flask validates the fields and inserts data into SQLite using parameterized SQL.
3. The dashboard calculates expiry status using today's date and a 30-day warning window.
4. Stock at or below the medicine's minimum threshold is flagged as low stock.
5. Pandas prepares inventory data, Seaborn/Matplotlib render the chart, and NumPy calculates summary statistics.
6. The user can search records and export the inventory as CSV.

## College presentation summary
“This project helps households and small clinics maintain medicine inventory. It stores medicine names, quantities, batch numbers and expiry dates, then highlights expired, soon-to-expire and low-stock records. Flask handles the backend, SQLite stores records, and Pandas, NumPy, Matplotlib and Seaborn provide data analysis and visual reporting.”

## Important safety and deployment notes
- This is an educational inventory reminder, not a medical advice system. Always verify dates and quantities against the actual medicine packaging and local procedures.
- Expired medicines are flagged for appropriate handling; the app does not recommend taking them.
- The development server uses debug mode. Do not expose it directly to the public internet. A real deployment needs production hosting, authentication/authorization, HTTPS, backups, access controls, audit logging, and stronger operational safeguards.
- Data is stored locally in `medicines.db`; back it up if you need to preserve records.
c