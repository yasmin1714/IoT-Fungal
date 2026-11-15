import json
from pathlib import Path
from datetime import datetime

import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    classification_report, confusion_matrix
)

try:
    from streamlit_autorefresh import st_autorefresh
    AUTO_REFRESH = True
except ImportError:
    AUTO_REFRESH = False

# ============================================================
# CONFIGURATION
# ============================================================
st.set_page_config(
    page_title="IoT Fungal | Operations Dashboard",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

REFRESH_SECONDS = 5
if AUTO_REFRESH:
    st_autorefresh(interval=REFRESH_SECONDS * 1000, key="iot_fungal_refresh")

BASE_DIR = Path(__file__).resolve().parent
DATASET_DIR = BASE_DIR / "dataset"
SENSOR_PATH = DATASET_DIR / "wokwi_sensor_data.csv"
ALERT_PATH = DATASET_DIR / "wokwi_alert_history.csv"
QUALITY_PATH = DATASET_DIR / "wokwi_data_quality.csv"
GATEWAY_PATH = DATASET_DIR / "mqtt_gateway_status.json"

NODES = ["NODE_1", "NODE_2", "NODE_3"]
FEATURES = ["gas_response", "temperature", "humidity"]
REQUIRED = ["timestamp", "node_id", "gas_response", "temperature", "humidity", "status"]

RISK_COLORS = {
    "NORMAL": "#23965F",
    "WARNING": "#E9A23B",
    "HIGH ANOMALY": "#D94B50",
    "NO DATA": "#9AA7A1",
}
NODE_COLORS = {
    "NODE_1": "#2476C7",
    "NODE_2": "#48A9A6",
    "NODE_3": "#E58A36",
}

# ============================================================
# STYLING
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
html, body, [class*="css"] {font-family:'DM Sans',sans-serif;}
.stApp {background:radial-gradient(circle at 8% 0%,rgba(31,132,96,.09),transparent 26%),linear-gradient(180deg,#f6faf8 0%,#f4f7fb 100%);}
h1,h2,h3 {font-family:'Manrope',sans-serif!important;letter-spacing:-.03em;}
.block-container {max-width:1500px;padding-top:1.4rem;padding-bottom:3rem;}
[data-testid="stMetric"] {background:rgba(255,255,255,.94);border:1px solid #e2eae6;border-radius:16px;padding:15px 18px;box-shadow:0 5px 18px rgba(22,55,43,.045);}
[data-testid="stMetricLabel"] {color:#63746d;font-weight:600;}
[data-testid="stMetricValue"] {color:#183c31;font-family:'Manrope',sans-serif;}
.hero {background:linear-gradient(115deg,#123f34 0%,#17634b 58%,#258264 100%);color:white;padding:27px 31px;border-radius:22px;box-shadow:0 14px 35px rgba(18,63,52,.17);margin-bottom:18px;}
.hero-kicker {color:#bde8d4;text-transform:uppercase;letter-spacing:.16em;font-size:.72rem;font-weight:700;margin-bottom:8px;}
.hero h1 {color:white!important;margin:0;font-size:clamp(1.8rem,3vw,2.6rem);}
.hero p {color:#d9eee5;margin:9px 0 0;font-size:1rem;}
.kicker {color:#26805f;font-size:.72rem;font-weight:800;letter-spacing:.13em;text-transform:uppercase;margin-bottom:3px;}
.node-card {background:white;border:1px solid #e2eae6;border-radius:17px;padding:17px 18px;box-shadow:0 6px 20px rgba(22,55,43,.045);min-height:195px;}
.node-top {display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;}
.node-name {font-family:'Manrope',sans-serif;color:#183c31;font-weight:800;font-size:1.08rem;}
.pill {border-radius:99px;padding:5px 10px;font-size:.70rem;font-weight:800;letter-spacing:.04em;display:inline-block;}
.online,.risk-normal {background:#e3f6ec;color:#167345;}
.offline {background:#fff0e9;color:#b64b27;}
.risk-warning {background:#fff4dc;color:#9a6500;}
.risk-high {background:#fde8e8;color:#b4232d;}
.node-reading {color:#183c31;font-size:1.55rem;font-weight:800;font-family:'Manrope',sans-serif;margin-top:7px;}
.node-sub,.small-note {color:#73827b;font-size:.82rem;}
.node-foot {border-top:1px solid #edf1ee;margin-top:12px;padding-top:10px;color:#6d7c75;font-size:.78rem;line-height:1.8;}
.status-strip {border:1px solid #e2eae6;background:white;border-radius:14px;padding:13px 16px;display:flex;justify-content:space-between;align-items:center;gap:12px;}
.stAlert {border-radius:14px;}
</style>
""", unsafe_allow_html=True)


# ============================================================
# FILE HELPERS
# ============================================================
@st.cache_data(ttl=3, show_spinner=False)
def load_csv(path_string, modified_ns):
    path = Path(path_string)
    if not path.exists() or path.stat().st_size == 0:
        return pd.DataFrame()
    return pd.read_csv(path)


def read_json(path):
    try:
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            return obj if isinstance(obj, dict) else {}
    except (OSError, json.JSONDecodeError):
        pass
    return {}


def load_sensor_data():
    if not SENSOR_PATH.exists():
        return pd.DataFrame()
    raw = load_csv(str(SENSOR_PATH), SENSOR_PATH.stat().st_mtime_ns)
    if raw.empty:
        return raw
    missing = [c for c in REQUIRED if c not in raw.columns]
    if missing:
        st.error("Sensor CSV is missing required columns: " + ", ".join(missing))
        st.stop()
    df = raw.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)
    for c in FEATURES:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["node_id"] = df["node_id"].astype(str)
    df["status"] = df["status"].astype(str)
    df = df.dropna(subset=REQUIRED)
    df = df[df["node_id"].isin(NODES)]
    return df.sort_values("timestamp").reset_index(drop=True)


def packet_age(value):
    if not value:
        return None
    ts = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(ts):
        return None
    return max(0.0, (pd.Timestamp.now(tz="UTC") - ts).total_seconds())


def formatted_time(value):
    if not value:
        return "No packet received"
    ts = pd.to_datetime(value, errors="coerce")
    if pd.isna(ts):
        return "Unknown"
    if ts.tzinfo is not None:
        ts = ts.tz_convert("Asia/Kolkata")
        return ts.strftime("%d %b %Y, %H:%M:%S IST")
    return ts.tz_localize("UTC").tz_convert("Asia/Kolkata").strftime("%d %b %Y, %H:%M:%S IST")


def to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.markdown("## 🌾 Control centre")
st.sidebar.caption("IoT-Fungal · Wokwi MQTT prototype")
offline_after = st.sidebar.slider("Node offline timeout (seconds)", 10, 180, 45, 5)
history_choice = st.sidebar.selectbox("Chart history", [50, 100, 250, 500, "All"], index=2)
test_size = st.sidebar.slider("Random Forest test split (%)", 20, 40, 25, 5)
st.sidebar.divider()
st.sidebar.markdown("**Data sources**")
st.sidebar.code(
    "wokwi_sensor_data.csv\nmqtt_gateway_status.json\nwokwi_alert_history.csv\nwokwi_data_quality.csv",
    language="text",
)
st.sidebar.caption("Auto-refresh every 5 seconds" if AUTO_REFRESH else "Auto-refresh unavailable; use browser refresh.")


# ============================================================
# LOAD DATA
# ============================================================
data = load_sensor_data()
gateway = read_json(GATEWAY_PATH)

if data.empty:
    st.markdown("""
    <div class="hero">
      <div class="hero-kicker">Edge-IoT · Prototype</div>
      <h1>🌾 Grain Storage Risk Monitor</h1>
      <p>Waiting for the first valid Wokwi MQTT sensor packet.</p>
    </div>
    """, unsafe_allow_html=True)
    st.warning("No sensor readings found. Start `python simulation/mqtt_receiver.py` and run your Wokwi nodes.")
    st.stop()

# Gateway counters describe only the current receiver process.
broker_connected = bool(gateway.get("broker_connected", False))
gateway_label = str(gateway.get("connection_status", "UNKNOWN")).upper()
session_received = to_int(gateway.get("total_received"))
session_accepted = to_int(gateway.get("accepted_packets"))
session_rejected = to_int(gateway.get("rejected_packets"))
gateway_nodes = gateway.get("nodes", {})
if not isinstance(gateway_nodes, dict):
    gateway_nodes = {}

latest_csv = data.groupby("node_id", as_index=False).tail(1).set_index("node_id")
cumulative_counts = data["node_id"].value_counts().to_dict()

node_states = {}
online_count = 0
for node in NODES:
    stats = gateway_nodes.get(node, {})
    if not isinstance(stats, dict):
        stats = {}

    csv_row = latest_csv.loc[node] if node in latest_csv.index else None
    last_seen = stats.get("last_seen")
    if not last_seen and csv_row is not None:
        last_seen = csv_row["timestamp"]

    age = packet_age(last_seen)
    online = age is not None and age <= offline_after
    online_count += int(online)

    if csv_row is not None:
        latest_status = str(csv_row["status"])
        gas = float(csv_row["gas_response"])
        temp = float(csv_row["temperature"])
        humidity = float(csv_row["humidity"])
    else:
        latest_status = str(stats.get("last_status") or "NO DATA")
        gas = stats.get("last_gas_response")
        temp = None
        humidity = None

    node_states[node] = {
        "online": online,
        "age": age,
        "last_seen": last_seen,
        "status": latest_status,
        "gas": gas,
        "temperature": temp,
        "humidity": humidity,
        "session_packets": to_int(stats.get("packets_received")),
        "total_packets": to_int(cumulative_counts.get(node)),
        "rate": to_int(stats.get("reception_rate_per_minute")),
    }

last_packet_age = packet_age(gateway.get("last_packet_received"))
if last_packet_age is None:
    last_packet_age = packet_age(data["timestamp"].max())


# ============================================================
# HERO + MQTT CONNECTION
# ============================================================
st.markdown("""
<div class="hero">
  <div class="hero-kicker">Edge-IoT · Live sensor intelligence</div>
  <h1>🌾 Grain Storage Risk Monitor</h1>
  <p>Multi-node sensor network · MQTT telemetry · Machine-learning-assisted risk screening</p>
</div>
""", unsafe_allow_html=True)

broker_label = "CONNECTED" if broker_connected else gateway_label
broker_color = "#167345" if broker_connected else "#B64B27"
broker_bg = "#E3F6EC" if broker_connected else "#FFF0E9"
st.markdown(f"""
<div class="status-strip">
  <div>
    <div class="kicker">MQTT gateway connection</div>
    <strong>{gateway.get('broker', 'broker.hivemq.com')}:{gateway.get('port', 1883)}</strong>
    <div class="small-note">Topic: {gateway.get('topic', 'iot-fungal/demo-7f3a/#')}</div>
  </div>
  <span class="pill" style="background:{broker_bg};color:{broker_color};">● {broker_label}</span>
</div>
""", unsafe_allow_html=True)

st.write("")
a, b, c, d = st.columns(4)
a.metric("Cumulative sensor records", f"{len(data):,}")
b.metric("Nodes currently online", f"{online_count} / 3")
c.metric("Gateway session accepted", f"{session_accepted:,}")
d.metric("Last packet age", f"{last_packet_age:.0f}s" if last_packet_age is not None else "—")
st.caption(
    f"Gateway session: {session_received} received · {session_accepted} accepted · "
    f"{session_rejected} rejected | Rendered {datetime.now().strftime('%d %b %Y · %H:%M:%S')}"
)


# ============================================================
# LIVE NODE CARDS
# ============================================================
st.markdown('<div class="kicker">Network operations</div>', unsafe_allow_html=True)
st.header("Live sensor network")
st.caption(f"Node status is inferred from each node's latest accepted packet using a {offline_after}-second timeout.")
cols = st.columns(3)

for col, node in zip(cols, NODES):
    state = node_states[node]
    with col:
        online_cls = "online" if state["online"] else "offline"
        online_text = "● ONLINE" if state["online"] else "● OFFLINE"
        risk_cls = {
            "NORMAL": "risk-normal",
            "WARNING": "risk-warning",
            "HIGH ANOMALY": "risk-high",
        }.get(state["status"], "offline")
        gas = f"{state['gas']:.0f}" if state["gas"] is not None else "—"
        temp = f"{state['temperature']:.1f} °C" if state["temperature"] is not None else "—"
        hum = f"{state['humidity']:.1f}%" if state["humidity"] is not None else "—"
        age = f"{state['age']:.1f}s ago" if state["age"] is not None else "No data"

        st.markdown(f"""
        <div class="node-card">
          <div class="node-top">
            <span class="node-name">{node}</span>
            <span class="pill {online_cls}">{online_text}</span>
          </div>
          <span class="pill {risk_cls}">{state['status']}</span>
          <div class="node-reading">{gas}</div>
          <div class="node-sub">Gas-response proxy · ADC counts</div>
          <div class="node-foot">
            🌡 {temp} &nbsp; · &nbsp; 💧 {hum}<br>
            Last seen: {formatted_time(state['last_seen'])}<br>
            Packet age: {age}<br>
            Session packets: {state['session_packets']} · Total records: {state['total_packets']}<br>
            Reception rate: {state['rate']} packets/min
          </div>
        </div>
        """, unsafe_allow_html=True)

if broker_connected:
    st.success("Python gateway reports an active MQTT broker connection.")
else:
    st.warning("Gateway does not currently report an active MQTT broker connection. Check mqtt_receiver.py.")
if online_count < 3:
    st.info(f"{3-online_count} node(s) have not transmitted within {offline_after} seconds. This does not necessarily mean the MQTT broker is disconnected.")


# ============================================================
# COMMUNICATION RELIABILITY
# ============================================================
st.markdown('<div class="kicker">Communication reliability</div>', unsafe_allow_html=True)
st.header("Packet reception and gateway session")
r1, r2, r3, r4 = st.columns(4)
r1.metric("Messages received", session_received)
r2.metric("Accepted packets", session_accepted)
r3.metric("Rejected packets", session_rejected)
acceptance = session_accepted / session_received * 100 if session_received else 0
r4.metric("Validation acceptance", f"{acceptance:.1f}%")
st.caption("Validation acceptance = accepted messages / received messages. It is not a radio packet-delivery ratio.")

rate_df = pd.DataFrame([
    {
        "Node": node,
        "Packets received this session": node_states[node]["session_packets"],
        "Recent reception rate (packets/min)": node_states[node]["rate"],
    }
    for node in NODES
])
rate_tab, session_tab = st.tabs(["Recent reception rate", "Session packet counts"])
with rate_tab:
    fig = px.bar(
        rate_df, x="Node", y="Recent reception rate (packets/min)",
        color="Node", text="Recent reception rate (packets/min)",
        color_discrete_map=NODE_COLORS,
    )
    fig.update_layout(height=320, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
with session_tab:
    fig = px.bar(
        rate_df, x="Node", y="Packets received this session",
        color="Node", text="Packets received this session",
        color_discrete_map=NODE_COLORS,
    )
    fig.update_layout(height=320, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with st.expander("View gateway status JSON"):
    st.json(gateway)


# ============================================================
# DATA QUALITY
# ============================================================
st.markdown('<div class="kicker">Data integrity</div>', unsafe_allow_html=True)
st.header("Data-quality monitoring")
quality_df = load_csv(
    str(QUALITY_PATH),
    QUALITY_PATH.stat().st_mtime_ns if QUALITY_PATH.exists() else 0,
)
q1, q2, q3 = st.columns(3)
q1.metric("Rejected packets this session", session_rejected)
q2.metric("Quality-log records", len(quality_df))
q3.metric("Accepted records in dataset", len(data))

if quality_df.empty:
    st.success("No rejected packets are recorded in the available quality log.")
else:
    st.warning(f"{len(quality_df)} invalid packet record(s) found.")
    st.dataframe(quality_df, use_container_width=True, hide_index=True)

audit_rows = []
for field, low, high in [
    ("gas_response", 0, 4095),
    ("temperature", -40, 80),
    ("humidity", 0, 100),
]:
    bad = int(((data[field] < low) | (data[field] > high)).sum())
    audit_rows.append({
        "Field": field,
        "Allowed range": f"{low} to {high}",
        "Out-of-range rows in stored dataset": bad,
    })
st.markdown("**Range audit of cumulative accepted dataset**")
st.dataframe(pd.DataFrame(audit_rows), use_container_width=True, hide_index=True)


# ============================================================
# TIMESTAMPED ALERT HISTORY
# ============================================================
st.markdown('<div class="kicker">Risk watch</div>', unsafe_allow_html=True)
st.header("Timestamped alert history")
alert_df = load_csv(
    str(ALERT_PATH),
    ALERT_PATH.stat().st_mtime_ns if ALERT_PATH.exists() else 0,
)
if not alert_df.empty:
    if "timestamp" in alert_df.columns:
        alert_df["timestamp"] = pd.to_datetime(alert_df["timestamp"], errors="coerce", utc=True)
        alert_df = alert_df.sort_values("timestamp", ascending=False)

    high_n = int((alert_df["status"] == "HIGH ANOMALY").sum()) if "status" in alert_df else 0
    warn_n = int((alert_df["status"] == "WARNING").sum()) if "status" in alert_df else 0
    x, y, z = st.columns(3)
    x.metric("Recorded alert events", len(alert_df))
    y.metric("HIGH ANOMALY events", high_n)
    z.metric("WARNING events", warn_n)

    selected_nodes = st.multiselect("Filter alerts by node", NODES, default=NODES)
    filtered_alerts = alert_df[alert_df["node_id"].isin(selected_nodes)] if "node_id" in alert_df else alert_df
    filtered_alerts = filtered_alerts.copy()
    if "timestamp" in filtered_alerts.columns:
        filtered_alerts["timestamp"] = pd.to_datetime(filtered_alerts["timestamp"], errors="coerce", utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%d %b %Y, %H:%M:%S IST")
    st.dataframe(filtered_alerts.head(250), use_container_width=True, hide_index=True)
else:
    st.info("No alert history yet. The receiver creates this CSV when WARNING or HIGH ANOMALY packets arrive.")


# ============================================================
# WAREHOUSE MAP
# ============================================================
st.markdown('<div class="kicker">Spatial overview</div>', unsafe_allow_html=True)
st.header("Warehouse zone map")
st.caption("Illustrative three-zone layout; positions are not measured warehouse coordinates.")
zones = {
    "NODE_1": (2, 3, "STORAGE ZONE 1"),
    "NODE_2": (6, 3, "STORAGE ZONE 2"),
    "NODE_3": (10, 3, "STORAGE ZONE 3"),
}
warehouse = go.Figure()
warehouse.add_shape(
    type="rect", x0=0, y0=0, x1=12, y1=6,
    line=dict(color="#49645B", width=4), fillcolor="#F0F5F2", layer="below"
)

for node, (x, y, label) in zones.items():
    state = node_states[node]
    status = state["status"]
    color = RISK_COLORS.get(status, RISK_COLORS["NO DATA"])
    connection = "ONLINE" if state["online"] else "OFFLINE"
    gas = f"{state['gas']:.0f}" if state["gas"] is not None else "—"

    warehouse.add_shape(
        type="rect", x0=x-1.5, y0=y-1.5, x1=x+1.5, y1=y+1.5,
        line=dict(color=color, width=3), fillcolor=color, opacity=.16, layer="below"
    )
    warehouse.add_trace(go.Scatter(
        x=[x], y=[y], mode="markers+text",
        marker=dict(size=62, color=color, line=dict(color="white", width=4)),
        text=[f"{node}<br>{connection}"], textposition="middle center",
        textfont=dict(color="white", size=10), name=node,
        customdata=[[label, status, connection, gas]],
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>Node: %{fullData.name}<br>"
            "Risk label: %{customdata[1]}<br>Connectivity: %{customdata[2]}<br>"
            "Gas-response proxy: %{customdata[3]}<extra></extra>"
        ),
    ))
    warehouse.add_annotation(
        x=x, y=y-1.12, text=label, showarrow=False,
        font=dict(color="#334B42", size=10)
    )

warehouse.add_annotation(
    x=6, y=5.55, text="<b>GRAIN STORAGE WAREHOUSE</b>",
    showarrow=False, font=dict(size=16, color="#25483B")
)
warehouse.update_layout(
    height=450, margin=dict(l=10, r=10, t=25, b=10),
    xaxis=dict(range=[-.5, 12.5], visible=False),
    yaxis=dict(range=[-.5, 6.5], visible=False, scaleanchor="x", scaleratio=1),
    plot_bgcolor="#F8FBF9", paper_bgcolor="rgba(0,0,0,0)", showlegend=False,
)
st.plotly_chart(warehouse, use_container_width=True)


# ============================================================
# SENSOR TELEMETRY
# ============================================================
st.markdown('<div class="kicker">Telemetry analytics</div>', unsafe_allow_html=True)
st.header("Live sensor readings over time")
chart_data = data if history_choice == "All" else data.tail(int(history_choice))
chart_data = chart_data.copy()
chart_data["timestamp_ist"] = pd.to_datetime(chart_data["timestamp"], errors="coerce", utc=True).dt.tz_convert("Asia/Kolkata")
gas_tab, temp_tab, hum_tab = st.tabs(["Gas-response proxy", "Temperature", "Humidity"])

with gas_tab:
    fig = px.line(
        chart_data, x="timestamp_ist", y="gas_response", color="node_id",
        markers=True, color_discrete_map=NODE_COLORS, title="Gas-response proxy by node"
    )
    fig.add_hline(y=1200, line_dash="dash", line_color="#E9A23B", annotation_text="Warning threshold")
    fig.add_hline(y=2500, line_dash="dash", line_color="#D94B50", annotation_text="High-anomaly threshold")
    fig.update_layout(height=390, hovermode="x unified", legend_title="Sensor node", xaxis_title="Time (IST)")
    st.plotly_chart(fig, use_container_width=True)

with temp_tab:
    fig = px.line(
        chart_data, x="timestamp_ist", y="temperature", color="node_id",
        markers=True, color_discrete_map=NODE_COLORS, title="Temperature by node"
    )
    fig.update_layout(height=390, hovermode="x unified", legend_title="Sensor node", xaxis_title="Time (IST)")
    st.plotly_chart(fig, use_container_width=True)

with hum_tab:
    fig = px.line(
        chart_data, x="timestamp_ist", y="humidity", color="node_id",
        markers=True, color_discrete_map=NODE_COLORS, title="Relative humidity by node"
    )
    fig.update_layout(height=390, hovermode="x unified", legend_title="Sensor node", xaxis_title="Time (IST)")
    st.plotly_chart(fig, use_container_width=True)


# ============================================================
# CUMULATIVE PACKET ACTIVITY
# ============================================================
st.markdown('<div class="kicker">Communication activity</div>', unsafe_allow_html=True)
st.header("Cumulative packet activity")
packet_counts = (
    data["node_id"].value_counts().reindex(NODES, fill_value=0)
    .rename_axis("Node").reset_index(name="Packets received")
)
fig = px.bar(
    packet_counts, x="Node", y="Packets received", color="Node",
    text="Packets received", color_discrete_map=NODE_COLORS
)
fig.update_layout(height=310, showlegend=False)
st.plotly_chart(fig, use_container_width=True)

with st.expander("View latest sensor packets"):
    st.dataframe(
        data.sort_values("timestamp", ascending=False).head(50).assign(timestamp=lambda d: pd.to_datetime(d["timestamp"], errors="coerce", utc=True).dt.tz_convert("Asia/Kolkata").dt.strftime("%d %b %Y, %H:%M:%S IST")),
        use_container_width=True, hide_index=True
    )


# ============================================================
# MACHINE LEARNING
# ============================================================
st.markdown('<div class="kicker">Model insights</div>', unsafe_allow_html=True)
st.header("Machine-learning analysis")
st.caption(
    "Models analyse programmed status labels and statistical patterns in simulated data; "
    "they do not establish fungal contamination."
)

class_counts = data["status"].value_counts()
if len(class_counts) >= 2 and class_counts.min() >= 2 and len(data) >= 12:
    X = data[FEATURES]
    y = data["status"]
    try:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size/100, random_state=42, stratify=y
        )
        rf = RandomForestClassifier(
            n_estimators=150, random_state=42, class_weight="balanced"
        )
        rf.fit(X_train, y_train)
        pred = rf.predict(X_test)

        accuracy = accuracy_score(y_test, pred)
        precision = precision_score(y_test, pred, average="macro", zero_division=0)
        recall = recall_score(y_test, pred, average="macro", zero_division=0)
        f1 = f1_score(y_test, pred, average="macro", zero_division=0)

        st.subheader("🌳 Random Forest · Programmed-label classification")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Test accuracy", f"{accuracy*100:.1f}%")
        m2.metric("Macro precision", f"{precision:.3f}")
        m3.metric("Macro recall", f"{recall:.3f}")
        m4.metric("Macro F1", f"{f1:.3f}")

        labels = list(rf.classes_)
        cm = confusion_matrix(y_test, pred, labels=labels)
        fig = px.imshow(
            cm, x=labels, y=labels, text_auto=True,
            color_continuous_scale="Greens",
            labels={"x": "Predicted", "y": "Actual", "color": "Count"},
            title="Held-out test confusion matrix"
        )
        fig.update_layout(height=370)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Classification report**")
        report = classification_report(y_test, pred, output_dict=True, zero_division=0)
        st.dataframe(pd.DataFrame(report).transpose().round(3), use_container_width=True)

        importance = pd.DataFrame({
            "Feature": FEATURES,
            "Importance": rf.feature_importances_
        }).sort_values("Importance", ascending=False)
        fig = px.bar(
            importance, x="Feature", y="Importance", color="Importance",
            color_continuous_scale="Greens", title="Random Forest feature importance"
        )
        st.plotly_chart(fig, use_container_width=True)
    except ValueError as error:
        st.warning(f"Random Forest evaluation could not run with this split: {error}")
else:
    st.info("Random Forest needs at least two records in each of at least two status classes.")

st.divider()
st.subheader("🌲 Isolation Forest · Unsupervised outlier screening")
if len(data) >= 10:
    try:
        scaled = StandardScaler().fit_transform(data[FEATURES])
        model = IsolationForest(contamination="auto", random_state=42)
        predictions = model.fit_predict(scaled)
        isolation_data = data.copy()
        isolation_data["isolation_status"] = [
            "ANOMALY" if value == -1 else "NORMAL" for value in predictions
        ]
        anomaly_n = int((isolation_data["isolation_status"] == "ANOMALY").sum())
        normal_n = int((isolation_data["isolation_status"] == "NORMAL").sum())

        i1, i2, i3 = st.columns(3)
        i1.metric("Records analysed", len(isolation_data))
        i2.metric("Statistical outliers", anomaly_n)
        i3.metric("Model-normal records", normal_n)

        dist = (
            isolation_data["isolation_status"].value_counts()
            .rename_axis("Result").reset_index(name="Count")
        )
        fig = px.pie(
            dist, names="Result", values="Count", hole=.58,
            color="Result",
            color_discrete_map={"ANOMALY": "#D94B50", "NORMAL": "#23965F"},
            title="Isolation Forest output"
        )
        fig.update_layout(height=360)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("**Isolation Forest output vs programmed status labels**")
        st.dataframe(
            pd.crosstab(isolation_data["status"], isolation_data["isolation_status"]),
            use_container_width=True
        )
    except ValueError as error:
        st.warning(f"Isolation Forest could not run: {error}")
else:
    st.info("Isolation Forest requires at least 10 sensor records.")


# ============================================================
# CSV EXPORTS
# ============================================================
st.markdown('<div class="kicker">Data management</div>', unsafe_allow_html=True)
st.header("Export datasets")
e1, e2, e3 = st.columns(3)

with e1:
    st.download_button(
        "⬇️ Sensor readings CSV",
        data=data.to_csv(index=False).encode("utf-8"),
        file_name="wokwi_sensor_data_export.csv",
        mime="text/csv",
        use_container_width=True
    )

with e2:
    alert_export = alert_df.copy()
    if not alert_export.empty and "timestamp" in alert_export.columns:
        alert_export["timestamp"] = alert_export["timestamp"].astype(str)
    st.download_button(
        "⬇️ Alert history CSV",
        data=alert_export.to_csv(index=False).encode("utf-8"),
        file_name="wokwi_alert_history_export.csv",
        mime="text/csv",
        disabled=alert_export.empty,
        use_container_width=True
    )

with e3:
    st.download_button(
        "⬇️ Data-quality log CSV",
        data=quality_df.to_csv(index=False).encode("utf-8"),
        file_name="wokwi_data_quality_export.csv",
        mime="text/csv",
        disabled=quality_df.empty,
        use_container_width=True
    )

with st.expander("Prototype scope and limitations"):
    st.markdown("""
    - The Wokwi potentiometer is a simulated analog gas-response proxy, not an MQ-135 measurement.
    - The DHT22 is a simulation substitute and readings may remain constant unless changed in Wokwi.
    - MQTT is used for this communication test; it is not physical LoRa/SX1278 communication.
    - Broker connection status comes from the Python gateway status file.
    - Node online/offline status is inferred from the age of each node's last accepted packet.
    - Reception rate is received packets in the recent 60-second window, not a packet-delivery ratio.
    - NORMAL, WARNING and HIGH ANOMALY are programmed simulation labels based on gas-response thresholds.
    - Random Forest metrics evaluate those programmed labels, not confirmed fungal detection.
    - Isolation Forest identifies statistical outliers, not fungal contamination.
    - Independent experimental measurements and laboratory validation are required before real-world fungal or mycotoxin detection claims.
    - Warehouse zone positions are illustrative.
    """)

st.caption(
    f"IoT Fungal Hotspot Monitoring · Wokwi MQTT prototype · "
    f"{'Auto-refresh every 5 seconds' if AUTO_REFRESH else 'Manual refresh'}"
)
