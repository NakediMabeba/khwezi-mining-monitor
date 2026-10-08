# Khwezi Mining Monitor — MINN2020A Prototype

A Streamlit prototype based on the assignment brief. It demonstrates:

- Role-based login/access control
- Worker health and safety monitoring
- Safety incident database, search/filter and basic analysis
- Equipment database and condition monitoring
- Maintenance monitoring and availability indicators
- 1–5 likelihood × consequence risk assessment
- Automatic alerts and notifications
- Mining monitoring dashboard
- Interactive business-question analysis
- CSV report/data export

## Run locally

1. Install Python 3.10+.
2. Open a terminal in this project folder.
3. Run:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Open the Local URL shown in the terminal, normally `http://localhost:8501`.

## Demo accounts

| Username | Password | Role |
|---|---|---|
| admin | admin123 | Administrator |
| safety | safety123 | Safety Officer |
| mining | mining123 | Mining Engineer |
| maintenance | maint123 | Maintenance Engineer |
| manager | manager123 | Manager |

## Assignment mapping

The app covers the brief's access control, worker safety, incident database, equipment database, condition monitoring, maintenance monitoring, risk assessment, alerts, dashboard and interactive analysis requirements.

The assignment specifies these educational prototype thresholds: temperature `<80°C` normal, `80–100°C` warning, `>100°C` critical; vibration `<5 mm/s` normal, `5–8 mm/s` warning, `>8 mm/s` critical. They are explicitly not actual manufacturer or mine safety limits.

The CSV files in `data/` are sample data. Replace them with your group's dataset when ready.

## Deploy online

Upload the project to GitHub, then use Streamlit Community Cloud to deploy `app.py`. The same `requirements.txt` and `data/` folder should be included in the repository.

For a real production system, replace the demo login with secure authentication, password hashing, a database and secrets management.
