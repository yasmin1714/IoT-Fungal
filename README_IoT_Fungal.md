# IoT-Fungal: Grain Storage Risk Monitoring System

A multi-node IoT simulation prototype for monitoring environmental and gas-response signals in grain-storage zones, identifying unusual readings, and presenting them through a live dashboard.

> **Project status:** Simulation prototype. The current demonstration uses Wokwi ESP32 simulations, a potentiometer as a simulated gas-response input, DHT22 as an environmental-sensor substitute, MQTT for message transport, and a Python/Streamlit dashboard. Physical sensor deployment and laboratory validation are future work.

## Overview

Post-harvest grain storage conditions can contribute to fungal growth and spoilage. This project explores a distributed sensing and monitoring workflow that could help flag unusual environmental or gas-response patterns across multiple storage zones.

Three simulated sensor nodes publish readings to an MQTT broker. A Python gateway receives and validates messages, stores the readings, records warning events, and exposes gateway status. A Streamlit dashboard visualizes node connectivity, recent packet reception, sensor trends, alert history, data quality, and exploratory machine-learning outputs.

The system is intended for **risk screening and prototype evaluation**, not as a validated fungal or mycotoxin detection instrument.

## Current prototype architecture

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

## Features

- Three simulated sensor nodes representing separate grain-storage zones.
- MQTT-based telemetry publishing and Python gateway reception.
- Packet validation for node identity, numeric values, and expected sensor ranges.
- Per-node online/offline status inferred from the age of the latest accepted packet.
- Recent packet reception rate for each node.
- Gateway connection status and current-session packet counters.
- Cumulative sensor readings stored in CSV files.
- Timestamped warning and high-anomaly event history.
- Data-quality logging and range checks.
- Warehouse-zone visualization.
- Live gas-response proxy, temperature, and humidity charts.
- Random Forest classification of the programmed simulation labels.
- Isolation Forest for exploratory statistical outlier screening.
- CSV export options for sensor readings, alerts, and data-quality records.

## Technology stack

| Layer                      | Tools                                                                |
| -------------------------- | -------------------------------------------------------------------- |
| Simulation                 | Wokwi                                                                |
| Microcontroller simulation | ESP32                                                                |
| Sensor inputs              | Potentiometer (gas-response proxy), DHT22 (environmental substitute) |
| Messaging                  | MQTT, Paho MQTT, public HiveMQ broker                                |
| Backend / data handling    | Python, Pandas                                                       |
| Dashboard                  | Streamlit, Plotly                                                    |
| Machine learning           | Scikit-learn, Random Forest, Isolation Forest                        |
| Data storage               | CSV, JSON                                                            |

## Repository structure

The repository is expected to follow this structure. Adjust the tree if your final project contains additional files or a different layout.

```text
IoT-Fungal/
├── app.py
├── machine_learning.py
├── isolation_forest.py
├── requirements.txt
├── README.md
├── .gitignore
├── simulation/
│   ├── mqtt_receiver.py
│   ├── sensor_nodes.py
│   ├── receiver.py
│   └── lora_network.py
├── dataset/
│   ├── .gitkeep
│   └── (generated CSV and JSON files)
└── screenshots/
    └── (dashboard screenshots)
```

Generated data files may be created when the gateway is running. Do not commit private credentials, virtual environments, caches, or unnecessary large generated datasets.

## Getting started

### 1. Prerequisites

- Windows, macOS, or Linux
- Python 3.10 or a compatible version
- Git
- A Wokwi account and the three ESP32 simulation projects
- Internet access for the public MQTT broker

### 2. Clone the repository

```bash
git clone https://github.com/<your-github-username>/<your-repository-name>.git
cd <your-repository-name>
```

### 3. Create and activate a virtual environment

**Windows PowerShell**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use the appropriate execution-policy setting for your machine or activate the environment from Command Prompt:

```cmd
.venv\Scripts\activate.bat
```

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 4. Install dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If you are preparing `requirements.txt` manually, the current dashboard/gateway workflow uses packages such as:

```text
streamlit
streamlit-autorefresh
pandas
plotly
scikit-learn
paho-mqtt
numpy
```

Use the repository's committed `requirements.txt` as the source of truth.

### 5. Configure the MQTT topic

The current demonstration uses the public broker:

- Broker: `broker.hivemq.com`
- Port: `1883`
- Topic pattern: `iot-fungal/demo-7f3a/#`

Each Wokwi node should publish to its own topic under the same prefix, for example:

```text
iot-fungal/demo-7f3a/NODE_1
iot-fungal/demo-7f3a/NODE_2
iot-fungal/demo-7f3a/NODE_3
```

The topic prefix and broker settings in the Wokwi firmware and `simulation/mqtt_receiver.py` must match.

> The public broker is suitable only for a demonstration. Use a private broker and appropriate authentication/TLS for any serious deployment. Do not publish sensitive information to a public MQTT topic.

### 6. Start the Python MQTT gateway

Open a terminal in the repository root and run:

```bash
python simulation/mqtt_receiver.py
```

Keep this terminal running. It subscribes to the configured MQTT topic, validates incoming messages, and writes accepted readings and gateway status to the `dataset/` directory.

### 7. Start the Wokwi nodes

Open and run all three Wokwi ESP32 simulations. Confirm that each node publishes messages using its unique node ID and topic.

### 8. Launch the dashboard

Open a second terminal in the repository root, activate the same virtual environment, and run:

```bash
streamlit run app.py
```

Open the local URL printed by Streamlit, normally:

```text
http://localhost:8501
```

The dashboard refreshes periodically while the gateway and simulations are running.

## Data files

The gateway/dashboard workflow uses the following files in `dataset/`:

| File                       | Purpose                                                                        |
| -------------------------- | ------------------------------------------------------------------------------ |
| `wokwi_sensor_data.csv`    | Cumulative accepted sensor readings                                            |
| `wokwi_alert_history.csv`  | Timestamped WARNING and HIGH ANOMALY events                                    |
| `wokwi_data_quality.csv`   | Rejected/invalid packet log; may not exist if no invalid packets have occurred |
| `mqtt_gateway_status.json` | Current gateway connection and session statistics                              |

The dashboard distinguishes **current gateway-session counters** from **cumulative CSV records**. Restarting the gateway can reset session counters while previously saved CSV records remain.

## Simulation labels and thresholds

The current firmware assigns status labels from the simulated gas-response value:

| Gas-response proxy | Programmed status |
| -----------------: | ----------------- |
|         Below 1200 | NORMAL            |
|          1200–2499 | WARNING           |
|     2500 and above | HIGH ANOMALY      |

These are prototype thresholds for generating and demonstrating alerts. They are not validated biological thresholds for fungal growth, fungal VOCs, or mycotoxin presence.

## Machine-learning modules

### Random Forest

The dashboard trains/evaluates a Random Forest classifier using the available simulated sensor readings and their programmed status labels. The reported accuracy, precision, recall, F1-score, confusion matrix, and feature importance describe how well the model reproduces those labels on the selected data split.

Because the labels are generated from programmed thresholds, these metrics **must not be interpreted as real-world fungal detection accuracy**.

### Isolation Forest

Isolation Forest is used as an unsupervised outlier-screening demonstration over the available sensor features. It flags statistically unusual records relative to the data supplied to it.

An outlier is not proof of fungal contamination. The output is exploratory and depends on the simulated data distribution and model settings.

## Important limitations and responsible interpretation

1. **No physical sensor measurements yet:** The current results are generated by Wokwi simulations.
2. **Gas-response proxy:** The Wokwi potentiometer supplies an analog value to imitate changing gas-sensor response. It is not an MQ-135 measurement and does not measure a specific VOC.
3. **Environmental sensor substitute:** DHT22 is used in the simulation in place of the planned DHT11 hardware.
4. **MQ-135 selectivity:** In a future physical prototype, MQ-135 is a broad-response metal-oxide gas sensor. It is not selective for fungal VOCs or mycotoxins and requires appropriate calibration and validation.
5. **MQTT, not physical LoRa:** Current message transport is MQTT over the Wokwi/network simulation. Physical SX1278/LoRa communication has not yet been tested.
6. **Programmed labels:** NORMAL, WARNING, and HIGH ANOMALY are assigned using the configured gas-response thresholds.
7. **Machine-learning results:** The models analyse simulated values and programmed labels/statistical patterns. They do not establish fungal contamination.
8. **No laboratory confirmation:** Independent experiments, reference measurements, and laboratory testing are required before making claims about fungal species or mycotoxin detection.
9. **Illustrative warehouse map:** Zone positions are conceptual and are not measured warehouse coordinates.
10. **Public MQTT broker:** The public HiveMQ broker is for demonstration only; it is not intended for production or sensitive data.

## Planned future work

- Assemble the physical ESP32 sensor nodes and gateway.
- Integrate and calibrate the selected gas and environmental sensors.
- Implement and test physical SX1278 LoRa communication.
- Collect real measurements under controlled storage conditions.
- Obtain appropriate reference labels through laboratory or validated testing.
- Evaluate sensor drift, repeatability, false alarms, and detection performance.
- Retrain and validate machine-learning models using independently collected data.
- Evaluate deployment reliability, power consumption, and long-term operation.

## Demo

**YouTube demonstration:** [https://www.youtube.com/watch?v=eDVbarhVdLc]

The demo video will show the Wokwi sensor-node simulations, MQTT gateway, live Streamlit dashboard, alert history, telemetry charts, and exploratory machine-learning sections.

## Author

**[Yasmin Devaragattu]**

## Disclaimer

This repository presents an academic simulation prototype for experimentation and learning. It is not a certified food-safety, grain-quality, fungal-detection, or mycotoxin-detection system. Do not use its simulated outputs to make storage, health, or food-safety decisions.
