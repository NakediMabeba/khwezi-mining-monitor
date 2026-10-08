import streamlit as st
import pandas as pd
import numpy as np
from datetime import date, datetime
from io import BytesIO

st.set_page_config(page_title="Khwezi Mining Monitor", page_icon="⛏️", layout="wide")

# -----------------------------
# Demo users and role permissions
# -----------------------------
USERS = {
    "admin": {"password": "admin123", "role": "Administrator", "name": "System Administrator"},
    "safety": {"password": "safety123", "role": "Safety Officer", "name": "Safety Officer"},
    "mining": {"password": "mining123", "role": "Mining Engineer", "name": "Mining Engineer"},
    "maintenance": {"password": "maint123", "role": "Maintenance Engineer", "name": "Maintenance Engineer"},
    "manager": {"password": "manager123", "role": "Manager", "name": "Mine Manager"},
}

PERMISSIONS = {
    "Administrator": {"dashboard", "safety", "incidents", "equipment", "maintenance", "risk", "alerts", "analytics", "reports", "users"},
    "Safety Officer": {"dashboard", "safety", "incidents", "risk", "alerts", "analytics", "reports"},
    "Mining Engineer": {"dashboard", "safety", "incidents", "equipment", "maintenance", "risk", "alerts", "analytics", "reports"},
    "Maintenance Engineer": {"dashboard", "equipment", "maintenance", "alerts", "analytics", "reports"},
    "Manager": {"dashboard", "safety", "incidents", "equipment", "maintenance", "risk", "alerts", "analytics", "reports"},
}

# Assignment prototype thresholds — NOT manufacturer/mine safety limits.
TEMP_WARNING, TEMP_CRITICAL = 80.0, 100.0
VIB_WARNING, VIB_CRITICAL = 5.0, 8.0


def load_csv(name, fallback):
    path = Path("data") / name
    if path.exists():
        try:
            return pd.read_csv(path)
        except Exception:
            pass
    return fallback.copy()

workers_default = pd.DataFrame([
    ["W001", "Production", "Driller", "Day", 96, "Complete", 2, 4, 0, "Low"],
    ["W002", "Plant", "Operator", "Night", 82, "Complete", 4, 2, 1, "Medium"],
    ["W003", "Engineering", "Technician", "Day", 100, "Complete", 1, 6, 0, "Low"],
    ["W004", "Production", "LHD Operator", "Night", 68, "Expired", 5, 1, 2, "High"],
    ["W005", "Maintenance", "Fitter", "Day", 91, "Complete", 3, 3, 1, "Medium"],
    ["W006", "Production", "Blaster", "Day", 88, "Complete", 2, 5, 0, "Low"],
], columns=["Worker ID","Department","Job Role","Shift","PPE Compliance (%)","Training Status","Fatigue Level","Safety Observations","Near Misses","Risk Level"])

incidents_default = pd.DataFrame([
    ["I001","2026-09-01","07:30","Day","North Pit","Production","Slip/Trip","Medium","No","No","Wet surface","Improve housekeeping","Open"],
    ["I002","2026-09-03","21:15","Night","Crusher Plant","Plant","Equipment Contact","High","Yes","Yes","Poor visibility","Repair lighting","Under Review"],
    ["I003","2026-09-07","10:10","Day","Workshop","Maintenance","Hand Injury","Low","Yes","No","Improper tool use","Toolbox talk","Closed"],
    ["I004","2026-09-12","23:40","Night","South Pit","Production","Fall of Ground","Critical","Yes","Yes","Loose ground","Barricade and inspect","Open"],
    ["I005","2026-09-18","14:20","Day","Plant","Plant","Near Miss","Medium","No","No","Pedestrian interaction","Review traffic plan","Closed"],
    ["I006","2026-09-24","02:10","Night","North Pit","Production","Vehicle Incident","High","No","No","Reversing near miss","Review reversing controls","Under Review"],
], columns=["Incident ID","Date","Time","Shift","Location","Department","Incident Type","Severity","Injury","Lost Time Injury","Cause","Corrective Action","Status"])

equipment_default = pd.DataFrame([
    ["TRK-001","Haul Truck","Sandvik","8200","74","4.2","38","Good","Good","Good","Available","18","94"],
    ["TRK-002","Haul Truck","Komatsu","9100","87","5.7","41","Good","Good","Good","Available","31","88"],
    ["LD-003","Loader","CAT","6200","79","4.8","35","Good","Worn","Good","Available","22","92"],
    ["DR-004","Drilling Machine","Epiroc","7100","103","9.2","47","Inspect","Good","Warning","Maintenance Due","55","75"],
    ["CR-005","Crusher","Metso","12600","96","6.4","58","Good","Good","Good","Under Maintenance","86","68"],
    ["CV-006","Conveyor","Metso","15400","72","3.1","44","Good","Good","Good","Available","12","96"],
], columns=["Equipment ID","Equipment Type","Manufacturer","Operating Hours","Temperature (°C)","Vibration (mm/s)","Fuel Consumption","Brake Status","Tyre Status","Engine Status","Maintenance Status","Downtime (h)","Availability (%)"])

equipment_default["Operating Hours"] = pd.to_numeric(equipment_default["Operating Hours"])
equipment_default["Temperature (°C)"] = pd.to_numeric(equipment_default["Temperature (°C)"])
equipment_default["Vibration (mm/s)"] = pd.to_numeric(equipment_default["Vibration (mm/s)"])
equipment_default["Downtime (h)"] = pd.to_numeric(equipment_default["Downtime (h)"])
equipment_default["Availability (%)"] = pd.to_numeric(equipment_default["Availability (%)"])

workers = load_csv("workers.csv", workers_default)
incidents = load_csv("incidents.csv", incidents_default)
equipment = load_csv("equipment.csv", equipment_default)

for c in ["PPE Compliance (%)","Fatigue Level","Safety Observations","Near Misses"]:
    workers[c] = pd.to_numeric(workers[c], errors="coerce").fillna(0)
for c in ["Temperature (°C)","Vibration (mm/s)","Operating Hours","Downtime (h)","Availability (%)"]:
    equipment[c] = pd.to_numeric(equipment[c], errors="coerce").fillna(0)

# -----------------------------
# Session state / login
# -----------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "username" not in st.session_state:
    st.session_state.username = ""


def login_page():
    st.title("⛏️ Khwezi Mining Monitor")
    st.subheader("Mining Health, Safety and Equipment Monitoring Application")
    st.info("Prototype for MINN2020A Computer Programming for Mining")
    with st.form("login"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True)
        if submitted:
            user = USERS.get(username.strip().lower())
            if user and password == user["password"]:
                st.session_state.logged_in = True
                st.session_state.username = username.strip().lower()
                st.rerun()
            else:
                st.error("Invalid username or password.")
    st.caption("Demo accounts: admin/admin123 • safety/safety123 • mining/mining123 • maintenance/maint123 • manager/manager123")


def equipment_status(row):
    t = float(row["Temperature (°C)"])
    v = float(row["Vibration (mm/s)"])
    if t > TEMP_CRITICAL or v > VIB_CRITICAL:
        return "CRITICAL"
    if t >= TEMP_WARNING or v >= VIB_WARNING:
        return "WARNING"
    return "NORMAL"


def risk_class(likelihood, consequence):
    score = int(likelihood) * int(consequence)
    if score <= 4:
        level = "Low"
    elif score <= 9:
        level = "Medium"
    elif score <= 16:
        level = "High"
    else:
        level = "Critical"
    return score, level


def build_alerts():
    alerts = []
    for _, r in equipment.iterrows():
        status = equipment_status(r)
        if status != "NORMAL":
            reason = []
            if float(r["Temperature (°C)"]) >= TEMP_WARNING:
                reason.append(f"temperature {r['Temperature (°C)']}°C")
            if float(r["Vibration (mm/s)"]) >= VIB_WARNING:
                reason.append(f"vibration {r['Vibration (mm/s)']} mm/s")
            alerts.append({"Priority": status, "Source": r["Equipment ID"], "Alert": "; ".join(reason), "Recommended Action": "Inspect equipment and initiate appropriate maintenance/safety procedures."})
    low_ppe = workers[workers["PPE Compliance (%)"] < 80]
    for _, r in low_ppe.iterrows():
        alerts.append({"Priority":"HIGH", "Source":r["Worker ID"], "Alert":f"Low PPE compliance ({r['PPE Compliance (%)']}%)", "Recommended Action":"Review PPE compliance and supervisor controls."})
    high_fatigue = workers[workers["Fatigue Level"] >= 5]
    for _, r in high_fatigue.iterrows():
        alerts.append({"Priority":"HIGH", "Source":r["Worker ID"], "Alert":f"High fatigue level ({r['Fatigue Level']}/5)", "Recommended Action":"Assess worker fitness for task and apply fatigue controls."})
    critical_inc = incidents[incidents["Severity"].astype(str).str.lower() == "critical"]
    for _, r in critical_inc.iterrows():
        alerts.append({"Priority":"CRITICAL", "Source":r["Incident ID"], "Alert":f"Critical safety incident at {r['Location']}", "Recommended Action":"Follow site emergency, investigation and corrective-action procedures."})
    return pd.DataFrame(alerts, columns=["Priority","Source","Alert","Recommended Action"])


def kpi_card(label, value, help_text=None):
    st.metric(label, value, help=help_text)


def can(page):
    return page in PERMISSIONS[USERS[st.session_state.username]["role"]]


def dashboard():
    st.title("📊 Mining Monitoring Dashboard")
    alerts = build_alerts()
    critical_alerts = int((alerts["Priority"] == "CRITICAL").sum()) if not alerts.empty else 0
    high_alerts = int(alerts["Priority"].isin(["HIGH","CRITICAL"]).sum()) if not alerts.empty else 0
    avg_avail = float(equipment["Availability (%)"].mean()) if len(equipment) else 0
    ppe = float(workers["PPE Compliance (%)"].mean()) if len(workers) else 0
    c = st.columns(6)
    vals = [len(workers), len(incidents), int(workers["Near Misses"].sum()), int((workers["Risk Level"].isin(["High","Critical"])).sum()), len(equipment), critical_alerts]
    labels = ["Total Workers","Safety Incidents","Near Misses","High-risk Workers","Total Equipment","Critical Alerts"]
    for col, label, value in zip(c, labels, vals):
        with col: kpi_card(label, value)
    c2 = st.columns(4)
    with c2[0]: kpi_card("Average PPE Compliance", f"{ppe:.1f}%")
    with c2[1]: kpi_card("Equipment Available", int((equipment["Maintenance Status"].str.lower() == "available").sum()))
    with c2[2]: kpi_card("Under Maintenance", int((equipment["Maintenance Status"].str.lower().str.contains("maintenance")).sum()))
    with c2[3]: kpi_card("Average Availability", f"{avg_avail:.1f}%")
    st.divider()
    left, right = st.columns(2)
    with left:
        st.subheader("Equipment condition")
        cond = equipment.copy()
        cond["Condition"] = cond.apply(equipment_status, axis=1)
        st.dataframe(cond[["Equipment ID","Equipment Type","Temperature (°C)","Vibration (mm/s)","Condition","Maintenance Status","Availability (%)"]], use_container_width=True, hide_index=True)
    with right:
        st.subheader("Active alerts")
        if alerts.empty:
            st.success("No alerts generated from the current prototype dataset.")
        else:
            st.dataframe(alerts, use_container_width=True, hide_index=True)
    st.caption("Prototype thresholds: temperature <80°C normal, 80–100°C warning, >100°C critical; vibration <5 mm/s normal, 5–8 warning, >8 critical. These are educational thresholds from the assignment and are not actual mine/manufacturer limits.")


def safety_page():
    st.title("🦺 Worker Health & Safety")
    tab1, tab2 = st.tabs(["Worker data", "Add worker"])
    with tab1:
        dept = st.multiselect("Department", sorted(workers["Department"].unique()))
        view = workers[workers["Department"].isin(dept)] if dept else workers
        st.dataframe(view, use_container_width=True, hide_index=True)
        st.subheader("Safety indicators")
        a,b,c = st.columns(3)
        a.metric("Average PPE compliance", f"{workers['PPE Compliance (%)'].mean():.1f}%")
        b.metric("Workers with low PPE", int((workers["PPE Compliance (%)"] < 80).sum()))
        c.metric("High fatigue workers", int((workers["Fatigue Level"] >= 5).sum()))
        st.bar_chart(workers.groupby("Department")["PPE Compliance (%)"].mean())
    with tab2:
        with st.form("add_worker"):
            wid = st.text_input("Worker ID")
            dept2 = st.selectbox("Department", ["Production","Plant","Engineering","Maintenance","Geology","Other"])
            role = st.text_input("Job role")
            shift = st.selectbox("Shift", ["Day","Night"])
            ppe = st.number_input("PPE compliance (%)", 0, 100, 100)
            training = st.selectbox("Training status", ["Complete","Expired","Pending"])
            fatigue = st.slider("Fatigue level", 1, 5, 1)
            obs = st.number_input("Safety observations", 0, 100, 0)
            near = st.number_input("Near misses", 0, 100, 0)
            submit = st.form_submit_button("Add worker")
            if submit:
                if not wid.strip() or not role.strip(): st.error("Worker ID and job role are required.")
                else:
                    level = "High" if ppe < 80 or fatigue >= 5 else ("Medium" if ppe < 90 or fatigue >= 3 else "Low")
                    new = pd.DataFrame([[wid.strip(),dept2,role.strip(),shift,ppe,training,fatigue,obs,near,level]], columns=workers.columns)
                    workers.loc[len(workers)] = new.iloc[0]
                    workers.to_csv(Path("data")/"workers.csv", index=False)
                    st.success("Worker added to the local CSV dataset. Refreshing data is automatic for this session.")


def incidents_page():
    st.title("🚨 Safety Incident Database")
    tab1, tab2 = st.tabs(["Incident records", "Add incident"])
    with tab1:
        q = st.text_input("Search incidents")
        sev = st.multiselect("Severity", sorted(incidents["Severity"].unique()))
        view = incidents.copy()
        if q: view = view[view.astype(str).apply(lambda row: row.str.contains(q, case=False, na=False).any(), axis=1)]
        if sev: view = view[view["Severity"].isin(sev)]
        st.dataframe(view, use_container_width=True, hide_index=True)
        st.subheader("Incident analysis")
        c1,c2 = st.columns(2)
        with c1:
            st.write("Incidents by department")
            st.bar_chart(incidents["Department"].value_counts())
        with c2:
            st.write("Incidents by shift")
            st.bar_chart(incidents["Shift"].value_counts())
        st.write("Incident types")
        st.bar_chart(incidents["Incident Type"].value_counts())
    with tab2:
        with st.form("incident_form"):
            iid = st.text_input("Incident ID")
            d = st.date_input("Date", value=date.today())
            t = st.time_input("Time")
            shift = st.selectbox("Shift", ["Day","Night"])
            loc = st.text_input("Location")
            dept = st.selectbox("Department", ["Production","Plant","Maintenance","Engineering","Other"])
            itype = st.selectbox("Incident type", ["Slip/Trip","Equipment Contact","Hand Injury","Fall of Ground","Vehicle Incident","Near Miss","Other"])
            severity = st.selectbox("Severity", ["Low","Medium","High","Critical"])
            injury = st.selectbox("Injury", ["No","Yes"])
            lti = st.selectbox("Lost-time injury", ["No","Yes"])
            cause = st.text_input("Cause")
            action = st.text_input("Corrective action")
            status = st.selectbox("Status", ["Open","Under Review","Closed"])
            submit = st.form_submit_button("Add incident")
            if submit:
                if not iid.strip() or not loc.strip(): st.error("Incident ID and location are required.")
                else:
                    new = [iid.strip(),str(d),str(t)[:5],shift,loc.strip(),dept,itype,severity,injury,lti,cause,action,status]
                    incidents.loc[len(incidents)] = new
                    incidents.to_csv(Path("data")/"incidents.csv", index=False)
                    st.success("Incident added to the local CSV dataset.")


def equipment_page():
    st.title("🚜 Equipment Database & Condition Monitoring")
    view = equipment.copy()
    view["Condition"] = view.apply(equipment_status, axis=1)
    st.dataframe(view, use_container_width=True, hide_index=True)
    st.subheader("Condition summary")
    counts = view["Condition"].value_counts()
    c1,c2,c3 = st.columns(3)
    c1.metric("Normal", int(counts.get("NORMAL",0)))
    c2.metric("Warning", int(counts.get("WARNING",0)))
    c3.metric("Critical", int(counts.get("CRITICAL",0)))
    st.subheader("Temperature and vibration")
    chart = view.set_index("Equipment ID")[["Temperature (°C)","Vibration (mm/s)"]]
    st.line_chart(chart)


def maintenance_page():
    st.title("🔧 Equipment Maintenance Monitoring")
    e = equipment.copy()
    e["Condition"] = e.apply(equipment_status, axis=1)
    e["Maintenance Flag"] = np.select([
        e["Maintenance Status"].astype(str).str.contains("Maintenance", case=False),
        e["Downtime (h)"] > 50,
        e["Availability (%)"] < 80,
        e["Condition"].isin(["WARNING","CRITICAL"])
    ], ["Under maintenance / due","Excessive downtime","Low availability","Repeated/condition alert"], default="Monitor")
    st.dataframe(e[["Equipment ID","Equipment Type","Maintenance Status","Downtime (h)","Availability (%)","Condition","Maintenance Flag"]], use_container_width=True, hide_index=True)
    st.subheader("Maintenance indicators")
    a,b,c = st.columns(3)
    a.metric("Low availability", int((e["Availability (%)"] < 80).sum()))
    b.metric("Excessive downtime", int((e["Downtime (h)"] > 50).sum()))
    c.metric("Maintenance/condition flags", int((e["Maintenance Flag"] != "Monitor").sum()))
    st.write("Availability is calculated as Operating Time / (Downtime + Operating Time) × 100. The sample dataset already contains availability values for demonstration.")


def risk_page():
    st.title("⚠️ Risk Assessment")
    st.write("RiskScore = Likelihood × Consequence, using the assignment's 1–5 scale.")
    c1,c2 = st.columns(2)
    with c1: likelihood = st.slider("Likelihood", 1, 5, 3)
    with c2: consequence = st.slider("Consequence", 1, 5, 3)
    score, level = risk_class(likelihood, consequence)
    st.metric("Risk score", score)
    if level == "Critical": st.error(f"CRITICAL RISK — score {score}. Immediate attention is required by the prototype rule.")
    elif level == "High": st.warning(f"HIGH RISK — score {score}. Review controls and corrective actions.")
    elif level == "Medium": st.info(f"MEDIUM RISK — score {score}. Monitor and apply controls.")
    else: st.success(f"LOW RISK — score {score}.")
    st.subheader("Classification")
    st.table(pd.DataFrame({"Score range":["1–4","5–9","10–16","17–25"],"Classification":["Low","Medium","High","Critical"]}))


def alerts_page():
    st.title("🔔 Alerts & Notifications")
    alerts = build_alerts()
    if alerts.empty:
        st.success("No active alerts.")
        return
    priority = st.multiselect("Priority", sorted(alerts["Priority"].unique()))
    view = alerts[alerts["Priority"].isin(priority)] if priority else alerts
    for _, r in view.iterrows():
        msg = f"**{r['Priority']}** — {r['Source']}: {r['Alert']}  \nRecommended action: {r['Recommended Action']}"
        if r["Priority"] == "CRITICAL": st.error(msg)
        elif r["Priority"] == "HIGH": st.warning(msg)
        else: st.info(msg)
    st.download_button("Download alerts CSV", view.to_csv(index=False).encode(), "mining_alerts.csv", "text/csv")


def analytics_page():
    st.title("📈 Interactive Data Analysis")
    question = st.selectbox("Choose a mining engineering question", [
        "How many safety incidents occurred?",
        "Which department has the highest number of incidents?",
        "Which shift records the most incidents?",
        "What percentage of workers comply with PPE requirements?",
        "How many near misses have been recorded?",
        "Which incident types occur most frequently?",
        "How many incidents are high or critical?",
        "Which equipment has the highest downtime?",
        "Which equipment has the lowest availability?",
        "Which equipment has the highest vibration?",
        "Which equipment has the highest operating temperature?",
        "What is the average equipment availability?",
        "Which equipment type has the highest downtime?",
        "What percentage of monitored equipment is operating normally?",
        "How many critical alerts are currently active?",
    ])
    if question == "How many safety incidents occurred?": st.metric("Safety incidents", len(incidents))
    elif question == "Which department has the highest number of incidents?": st.dataframe(incidents["Department"].value_counts().rename("Incident Count"), use_container_width=True)
    elif question == "Which shift records the most incidents?": st.dataframe(incidents["Shift"].value_counts().rename("Incident Count"), use_container_width=True)
    elif question == "What percentage of workers comply with PPE requirements?": st.metric("Average PPE compliance", f"{workers['PPE Compliance (%)'].mean():.1f}%")
    elif question == "How many near misses have been recorded?": st.metric("Near misses", int(workers["Near Misses"].sum()))
    elif question == "Which incident types occur most frequently?": st.dataframe(incidents["Incident Type"].value_counts().rename("Count"), use_container_width=True)
    elif question == "How many incidents are high or critical?": st.metric("High/Critical incidents", int(incidents["Severity"].isin(["High","Critical"]).sum()))
    elif question == "Which equipment has the highest downtime?": st.dataframe(equipment.nlargest(5,"Downtime (h)")[["Equipment ID","Equipment Type","Downtime (h)"]], use_container_width=True, hide_index=True)
    elif question == "Which equipment has the lowest availability?": st.dataframe(equipment.nsmallest(5,"Availability (%)")[["Equipment ID","Equipment Type","Availability (%)"]], use_container_width=True, hide_index=True)
    elif question == "Which equipment has the highest vibration?": st.dataframe(equipment.nlargest(5,"Vibration (mm/s)")[["Equipment ID","Equipment Type","Vibration (mm/s)"]], use_container_width=True, hide_index=True)
    elif question == "Which equipment has the highest operating temperature?": st.dataframe(equipment.nlargest(5,"Temperature (°C)")[["Equipment ID","Equipment Type","Temperature (°C)"]], use_container_width=True, hide_index=True)
    elif question == "What is the average equipment availability?": st.metric("Average availability", f"{equipment['Availability (%)'].mean():.1f}%")
    elif question == "Which equipment type has the highest downtime?": st.dataframe(equipment.groupby("Equipment Type")["Downtime (h)"].mean().sort_values(ascending=False).rename("Average Downtime (h)"), use_container_width=True)
    elif question == "What percentage of monitored equipment is operating normally?": st.metric("Normal equipment", f"{(equipment.apply(equipment_status, axis=1).eq('NORMAL').mean()*100):.1f}%")
    elif question == "How many critical alerts are currently active?": st.metric("Critical alerts", int((build_alerts()["Priority"] == "CRITICAL").sum()))


def reports_page():
    st.title("📄 Reports & Data Export")
    st.write("Export the prototype datasets for inclusion in analysis or reporting.")
    for label, df, filename in [("Workers",workers,"workers.csv"),("Incidents",incidents,"incidents.csv"),("Equipment",equipment,"equipment.csv"),("Alerts",build_alerts(),"alerts.csv")]:
        st.subheader(label)
        st.download_button(f"Download {filename}", df.to_csv(index=False).encode(), filename, "text/csv", key=f"dl_{filename}")
    st.subheader("Current application summary")
    summary = pd.DataFrame({"KPI":["Total workers","Safety incidents","Near misses","Total equipment","Average PPE compliance","Average equipment availability","Critical alerts"],"Value":[len(workers),len(incidents),int(workers["Near Misses"].sum()),len(equipment),f"{workers['PPE Compliance (%)'].mean():.1f}%",f"{equipment['Availability (%)'].mean():.1f}%",int((build_alerts()["Priority"] == "CRITICAL").sum())]})
    st.dataframe(summary, use_container_width=True, hide_index=True)


def users_page():
    st.title("👤 User Management")
    st.warning("This is a classroom prototype. Passwords are stored in the code and are not suitable for a real production system.")
    rows=[]
    for username,u in USERS.items(): rows.append([username,u["name"],u["role"],", ".join(sorted(PERMISSIONS[u["role"]]))])
    st.dataframe(pd.DataFrame(rows,columns=["Username","Name","Role","Permissions"]), use_container_width=True, hide_index=True)


def main_app():
    user = USERS[st.session_state.username]
    st.sidebar.title("⛏️ Khwezi Mining")
    st.sidebar.write(f"**{user['name']}**")
    st.sidebar.caption(user["role"])
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.username = ""
        st.rerun()
    pages = [("Dashboard","dashboard"),("Worker Safety","safety"),("Safety Incidents","incidents"),("Equipment","equipment"),("Maintenance","maintenance"),("Risk Assessment","risk"),("Alerts","alerts"),("Analytics","analytics"),("Reports","reports"),("Manage Users","users")]
    available = [(label,key) for label,key in pages if can(key)]
    selected = st.sidebar.radio("Navigation", [x[0] for x in available])
    fn = dict(available)[selected]
    {"dashboard":dashboard,"safety":safety_page,"incidents":incidents_page,"equipment":equipment_page,"maintenance":maintenance_page,"risk":risk_page,"alerts":alerts_page,"analytics":analytics_page,"reports":reports_page,"users":users_page}[fn]()

if not st.session_state.logged_in:
    login_page()
else:
    main_app()
