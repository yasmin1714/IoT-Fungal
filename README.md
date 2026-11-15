# IoT-Fungal: Grain Storage Risk Monitoring System

A multi-node IoT simulation prototype for monitoring environmental and gas-response signals in grain-storage zones, identifying unusual readings, and presenting them through a live dashboard.

> **Project status: Simulation Prototype**  
> The current demonstration is a simulation prototype using Wokwi ESP32 virtual microcontrollers, an analog potentiometer as a gas-response proxy, DHT22 as an environmental-sensor substitute, MQTT for message transport via HiveMQ public broker, and a Python/Streamlit dashboard. Physical hardware deployment (physical ESP32, MQ-135 gas sensor, DHT11 sensor, and SX1278 LoRa transceivers) and laboratory bio-validation are planned as future work.

---

## Visual Demonstration & Screenshots

### 1. Live Streamlit Risk Monitoring Dashboard
The Streamlit dashboard displays multi-node sensor network telemetry, gateway connectivity, real-time node online/offline states, alerts, and exploratory machine-learning screening.

![Grain Storage Risk Monitor Dashboard](screenshots/Screenshot%202026-11-15%20230319.png)

### 2. Wokwi ESP32 Sensor Node Simulation
Each simulated storage zone runs on a virtual ESP32 connected to an analog gas-response proxy (potentiometer) and DHT22 environmental sensor, publishing structured JSON telemetry over WiFi via MQTT to HiveMQ.

![Wokwi ESP32 Simulation Node](screenshots/Screenshot%202026-11-15%20231038.png)

---

## Overview

Post-harvest grain storage conditions can contribute to fungal growth and spoilage. This project explores a distributed sensing and monitoring workflow that could help flag unusual environmental or gas-response patterns across multiple storage zones.

Three simulated sensor nodes publish readings to an MQTT broker. A Python gateway receives and validates messages, stores the readings, records warning events, and exposes gateway status. A Streamlit dashboard visualizes node connectivity, recent packet reception, sensor trends, alert history, data quality, and exploratory machine-learning outputs.

The system is intended for **risk screening and prototype evaluation**, not as a validated fungal or mycotoxin detection instrument.

---

## Current Prototype Architecture

```text
┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐
│ Wokwi ESP32 Node 1 │   │ Wokwi ESP32 Node 2 │   │ Wokwi ESP32 Node 3 │
│ Gas-response proxy │   │ Gas-response proxy │   │ Gas-response proxy │
│ DHT22 substitute   │   │ DHT22 substitute   │   │ DHT22 substitute   │
└─────────┬──────────┘   └─────────┬──────────┘   └─────────┬──────────┘
          └───────────────────────┼────────────────────────┘
                                  │ MQTT
                                  ▼
                       ┌─────────────────────┐
                       │ MQTT broker         │
                       │ HiveMQ public broker│
                       └──────────┬──────────┘
                                  │
                                  ▼
                       ┌─────────────────────┐
                       │ Python MQTT gateway │
                       │ Validation + logging│
                       └──────────┬──────────┘
                                  │ CSV + JSON
                                  ▼
                       ┌─────────────────────┐
                       │ Streamlit dashboard │
                       │ Live monitoring     │
                       │ Alerts + ML analysis│
                       └─────────────────────┘
```

**Important:** MQTT is used for the current Wokwi simulation. This prototype does not yet demonstrate physical LoRa/SX1278 communication. The intended future hardware architecture uses ESP32 nodes with gas/environmental sensors and LoRa transceivers communicating with an ESP32 gateway.

---

## Features

- **Multi-Zone Monitoring:** Three simulated sensor nodes representing separate grain-storage zones.
- **MQTT Telemetry:** MQTT-based telemetry publishing and Python gateway reception via HiveMQ.
- **Packet Validation:** Validation for node identity, numeric values, and expected sensor ranges.
- **Node Health Tracking:** Per-node online/offline status inferred from the age of the latest accepted packet (45-second timeout).
- **Reception Metrics:** Recent packet reception rate (packets/min) for each node.
- **Gateway Statistics:** Gateway connection status and current-session packet counters.
- **Historical Logging:** Cumulative sensor readings stored in CSV format.
- **Alert History:** Timestamped WARNING and HIGH ANOMALY event tracking.
- **Quality Assurance:** Data-quality logging and invalid packet auditing.
- **Spatial Map:** Conceptual warehouse-zone visualization.
- **Live Visualizations:** Real-time gas-response proxy, temperature, and humidity charts.
- **Random Forest Model:** Supervised classification of the programmed simulation labels.
- **Isolation Forest Model:** Unsupervised statistical outlier screening for unusual patterns.
- **Export Capabilities:** CSV download options for sensor readings, alerts, and data-quality records.

---

## Technology Stack

| Layer                      | Tools / Technologies                                                 |
| -------------------------- | -------------------------------------------------------------------- |
| Simulation                 | Wokwi Web Simulator                                                  |
| Microcontroller Simulation | ESP32 DevKit v4                                                      |
| Sensor Inputs              | Potentiometer (gas-response proxy), DHT22 (environmental substitute) |
| Messaging / Transport      | MQTT, Paho MQTT, HiveMQ public broker (`broker.hivemq.com:1883`)     |
| Backend / Data Handling    | Python 3.10+, Pandas                                                 |
| Dashboard UI               | Streamlit, Plotly, Streamlit Autorefresh                             |
| Machine Learning           | Scikit-learn (Random Forest Classifier, Isolation Forest)            |
| Data Persistence           | CSV, JSON                                                            |

---

## Repository Structure

```text
IoT-Fungal/
├── app.py                     # Streamlit live risk monitoring dashboard
├── machine_learning.py        # Random Forest classification module
├── isolation_forest.py        # Isolation Forest outlier detection module
├── requirements.txt           # Python dependencies
├── README.md                  # Project documentation & instructions
├── .gitignore                 # Git ignore rules (.venv, caches, etc.)
├── simulation/
│   ├── mqtt_receiver.py       # Python MQTT gateway listener & data logger
│   ├── sensor_nodes.py        # Python-based multi-node sensor generator
│   ├── receiver.py            # Simulated LoRa packet receiver & logger
│   ├── lora_network.py        # Simulated LoRa RF channel model
│   └── wokwi/                 # Wokwi simulation hardware diagrams & sketches
│       ├── diagram.json       # Common Wokwi circuit diagram (ESP32 + Pot + DHT22)
│       ├── libraries.txt      # Required Arduino libraries
│       ├── node_1/            # Node 1 firmware sketch & circuit
│       │   ├── sketch.ino
│       │   ├── diagram.json
│       │   └── libraries.txt
│       ├── node_2/            # Node 2 firmware sketch & circuit
│       │   ├── sketch.ino
│       │   ├── diagram.json
│       │   └── libraries.txt
│       └── node_3/            # Node 3 firmware sketch & circuit
│           ├── sketch.ino
│           ├── diagram.json
│           └── libraries.txt
├── dataset/
│   ├── sensor_data.csv        # Baseline sensor log
│   ├── wokwi_sensor_data.csv  # Live accepted sensor readings from Wokwi
│   ├── wokwi_alert_history.csv# Recorded warning & anomaly alerts
│   └── mqtt_gateway_status.json# Gateway runtime state & packet counters
└── screenshots/               # Dashboard and simulation screenshots
    ├── Screenshot 2026-11-15 230319.png
    ├── Screenshot 2026-11-15 231038.png
    └── ...
```

---

## Getting Started

### 1. Prerequisites

- Python 3.10 or newer
- Git
- Modern web browser
- Internet connectivity (to communicate with the public HiveMQ broker)

### 2. Clone the Repository

```bash
git clone https://github.com/yasmin1714/IoT-Fungal.git
cd IoT-Fungal
```

### 3. Create and Activate a Virtual Environment

**Windows PowerShell:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If script execution is disabled in PowerShell:
```cmd
.venv\Scripts\activate.bat
```

**macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Configure the MQTT Topic

The demonstration communicates over the public HiveMQ broker:
- **Broker:** `broker.hivemq.com`
- **Port:** `1883`
- **Topic Wildcard:** `iot-fungal/demo-7f3a/#`

Each node publishes to its respective topic:
- Node 1: `iot-fungal/demo-7f3a/NODE_1`
- Node 2: `iot-fungal/demo-7f3a/NODE_2`
- Node 3: `iot-fungal/demo-7f3a/NODE_3`

> **Note:** The public HiveMQ broker is suitable for testing and demonstration. For production deployment, use a private authenticated MQTT broker with TLS encryption.

### 6. Start the Python MQTT Gateway

In your first terminal, start the gateway receiver to listen for telemetry:
```bash
python simulation/mqtt_receiver.py
```
Leave this process running. It validates incoming packets and records them to `dataset/wokwi_sensor_data.csv`.

### 7. Run the Wokwi ESP32 Simulations

Open the simulation projects in [Wokwi](https://wokwi.com) (or load `simulation/wokwi/node_1/sketch.ino`, etc.):
- [Node 3 Simulation Reference](https://wokwi.com/projects/480762598568121345)
- Verify WiFi and MQTT connection in the serial terminal.
- Adjust the potentiometer in Wokwi to simulate changing gas concentrations.

### 8. Launch the Streamlit Dashboard

In a second terminal (with `.venv` activated):
```bash
streamlit run app.py
```
Open your browser at:
```text
http://localhost:8501
```

---

## Simulation Labels and Thresholds

The simulation firmware classifies gas-response proxy values into risk tiers:

| Gas-Response Proxy Value | Programmed Status | Description |
| :----------------------- | :---------------- | :---------- |
| **Below 1200**           | `NORMAL`          | Safe operating baseline |
| **1200 – 2499**          | `WARNING`         | Elevated gas response |
| **2500 and above**       | `HIGH ANOMALY`    | Significant divergence / anomaly |

> **Disclaimer:** These thresholds illustrate alert triggering and dashboard responsiveness. They are not biological thresholds for fungal spores or mycotoxin levels.

---

## Machine Learning Modules

### Random Forest Classifier
- Trained dynamically on the telemetry dataset and programmed labels.
- Evaluates feature importances across gas response, temperature, and humidity.
- Provides test-split classification metrics (Accuracy, Precision, Recall, F1) and a confusion matrix.
- Illustrates how supervised learning can replicate rule-based categorizations.

### Isolation Forest Outlier Detection
- Unsupervised anomaly detection that flags statistical deviations in the multivariate sensor space.
- Useful for detecting unexpected combinations (e.g. abnormal temperature and humidity spikes) without explicit labels.

---

## Limitations and Future Work

### Limitations of Current Prototype
1. **Simulation Prototype:** All data originates from Wokwi virtual microcontrollers.
2. **Gas Sensor Proxy:** The potentiometer acts as an analog signal source, not an MQ-135 chemical sensor.
3. **Environmental Sensor Substitute:** DHT22 is simulated in place of planned physical DHT11 hardware.
4. **Transport Layer:** MQTT is currently used; physical SX1278 LoRa transceivers are not yet connected.
5. **No Biological Confirmation:** Model predictions and threshold alerts do not confirm the presence of live fungal organisms or mycotoxins.

### Planned Hardware Roadmap
- [ ] Assemble physical ESP32 boards with MQ-135 and DHT11 sensors.
- [ ] Interface SX1278 LoRa SPI transceivers for long-range, low-power node-to-gateway telemetry.
- [ ] Calibrate MQ-135 sensors against controlled gas concentrations in sealed test chambers.
- [ ] Collect empirical physical dataset across varying temperature/humidity regimes.
- [ ] Integrate validated microbiological test labels for supervised model training.

---

## Demonstration Video

**YouTube Video:** [https://www.youtube.com/watch?v=eDVbarhVdLc](https://www.youtube.com/watch?v=eDVbarhVdLc)

---

## Author

**Yasmin Devaragattu**  
GitHub: [@yasmin1714](https://github.com/yasmin1714)  
Project Repository: [https://github.com/yasmin1714/IoT-Fungal](https://github.com/yasmin1714/IoT-Fungal)

---

## License & Academic Disclaimer

This repository is developed for academic research, education, and simulation prototype demonstration. It is not a certified agricultural food-safety or grain-quality inspection device.
