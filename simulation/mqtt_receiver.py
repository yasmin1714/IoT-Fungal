"""IoT-Fungal MQTT receiver. Stores UTC timestamps; dashboard renders them in IST."""
import csv, json, math, time, uuid
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
import paho.mqtt.client as mqtt

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "dataset"
OUT.mkdir(parents=True, exist_ok=True)
SENSOR, ALERT = OUT / "wokwi_sensor_data.csv", OUT / "wokwi_alert_history.csv"
QUALITY, STATUS = OUT / "wokwi_data_quality.csv", OUT / "mqtt_gateway_status.json"
BROKER, PORT, TOPIC = "broker.hivemq.com", 1883, "iot-fungal/demo-7f3a/#"
NODES = ("NODE_1", "NODE_2", "NODE_3")
FIELDS = ["timestamp", "node_id", "gas_response", "temperature", "humidity", "status", "topic"]
QFIELDS = ["timestamp", "topic", "reason", "payload"]
lock = Lock()
recent, counts = defaultdict(deque), defaultdict(int)
last_seen, last_status, last_gas = {}, {}, {}
last_temp, last_humidity = {}, {}
session = {"total_received": 0, "accepted_packets": 0, "rejected_packets": 0,
           "broker_connected": False, "connection_status": "STARTING",
           "last_connected": None, "last_disconnected": None, "last_packet_received": None}

def now_utc():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def append_csv(path, row, fields):
    exists = path.exists() and path.stat().st_size > 0
    with path.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        if not exists: w.writeheader()
        w.writerow(row)

def save_status():
    epoch = time.time()
    with lock:
        nodes = {}
        for n in NODES:
            while recent[n] and epoch - recent[n][0] > 60: recent[n].popleft()
            nodes[n] = {"packets_received": counts[n], "last_seen": last_seen.get(n),
                        "last_status": last_status.get(n), "last_gas_response": last_gas.get(n),
                        "last_temperature": last_temp.get(n), "last_humidity": last_humidity.get(n),
                        "reception_rate_per_minute": len(recent[n])}
        obj = {"broker": BROKER, "port": PORT, "topic": TOPIC, **session,
               "nodes": nodes, "updated_at": now_utc()}
    tmp = STATUS.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, indent=2), encoding="utf-8")
    tmp.replace(STATUS)

def reject(reason, topic, raw):
    append_csv(QUALITY, {"timestamp": now_utc(), "topic": topic,
                         "reason": reason, "payload": raw[:1000]}, QFIELDS)
    with lock: session["rejected_packets"] += 1
    save_status()
    print("[REJECTED]", reason)

def number(v):
    try:
        x = float(v)
        return math.isfinite(x), x
    except (TypeError, ValueError):
        return False, None

def expected_status(gas):
    return "HIGH ANOMALY" if gas >= 2500 else "WARNING" if gas >= 1200 else "NORMAL"

def on_connect(client, userdata, flags, reason_code, properties=None):
    ok = int(reason_code) == 0
    with lock:
        session["broker_connected"] = ok
        session["connection_status"] = "CONNECTED" if ok else f"CONNECT_FAILED ({reason_code})"
        if ok: session["last_connected"] = now_utc()
    if ok:
        client.subscribe(TOPIC, qos=0)
        print(f"[CONNECTED] {BROKER}:{PORT} subscribed to {TOPIC}")
    else: print("[CONNECT FAILED]", reason_code)
    save_status()

def on_disconnect(client, userdata, disconnect_flags, reason_code, properties=None):
    with lock:
        session["broker_connected"] = False
        session["connection_status"] = "DISCONNECTED"
        session["last_disconnected"] = now_utc()
    save_status()
    print("[DISCONNECTED]", reason_code)

def on_message(client, userdata, message):
    raw = message.payload.decode("utf-8", errors="replace")
    with lock:
        session["total_received"] += 1
        session["last_packet_received"] = now_utc()
    try:
        p = json.loads(raw)
        if not isinstance(p, dict): raise ValueError("JSON root must be an object")
    except (json.JSONDecodeError, ValueError) as e:
        reject(f"Invalid JSON: {e}", message.topic, raw); return
    node = str(p.get("node_id", "")).strip()
    if node not in NODES:
        reject("Unknown or missing node_id", message.topic, raw); return
    okg, gas = number(p.get("gas_response"))
    okt, temp = number(p.get("temperature"))
    okh, hum = number(p.get("humidity"))
    if not (okg and okt and okh):
        reject("Sensor values must be finite numeric values", message.topic, raw); return
    if not (0 <= gas <= 4095 and gas.is_integer()):
        reject("gas_response must be integer 0..4095", message.topic, raw); return
    if not (-40 <= temp <= 80):
        reject("temperature outside -40..80 C", message.topic, raw); return
    if not (0 <= hum <= 100):
        reject("humidity outside 0..100 percent", message.topic, raw); return
    label = expected_status(int(gas))
    supplied = str(p.get("status", label)).strip().upper()
    if supplied != label:
        reject(f"Status mismatch: expected {label}, received {supplied}", message.topic, raw); return

    stamp = now_utc()
    row = {"timestamp": stamp, "node_id": node, "gas_response": int(gas),
           "temperature": round(temp, 2), "humidity": round(hum, 2),
           "status": label, "topic": message.topic}
    append_csv(SENSOR, row, FIELDS)
    if label != "NORMAL": append_csv(ALERT, row, FIELDS)
    epoch = time.time()
    with lock:
        session["accepted_packets"] += 1
        counts[node] += 1
        recent[node].append(epoch)
        while recent[node] and epoch - recent[node][0] > 60: recent[node].popleft()
        last_seen[node], last_status[node], last_gas[node] = stamp, label, int(gas)
        last_temp[node], last_humidity[node] = round(temp, 2), round(hum, 2)
    save_status()
    print(f"[{stamp}] {node} gas={int(gas)} temp={temp:.1f} humidity={hum:.1f} {label}")

def main():
    client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                         client_id="IoTFungalGateway_" + uuid.uuid4().hex[:10],
                         protocol=mqtt.MQTTv311)
    client.on_connect, client.on_disconnect, client.on_message = on_connect, on_disconnect, on_message
    client.reconnect_delay_set(min_delay=1, max_delay=30)
    save_status()
    print(f"Gateway: {BROKER}:{PORT} | {TOPIC}")
    while True:
        try:
            client.connect(BROKER, PORT, 60)
            client.loop_forever(retry_first_connection=True)
        except KeyboardInterrupt:
            print("Stopping gateway..."); break
        except Exception as e:
            with lock:
                session["broker_connected"] = False
                session["connection_status"] = f"CONNECTION_ERROR: {type(e).__name__}"
                session["last_disconnected"] = now_utc()
            save_status()
            print("[CONNECTION ERROR]", e, "— retrying in 5 seconds")
            time.sleep(5)
    try: client.disconnect()
    except Exception: pass
    with lock:
        session["broker_connected"] = False
        session["connection_status"] = "STOPPED"
    save_status()

if __name__ == "__main__":
    main()
