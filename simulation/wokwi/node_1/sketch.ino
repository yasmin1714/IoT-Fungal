#include <DHTesp.h>
#include <WiFi.h>
#include <PubSubClient.h>

// ==========================================
// GRAIN FUNGAL HOTSPOT MONITORING
// ESP32 SENSOR NODE 1
// ==========================================

// Sensor pin configuration
#define MQ_PIN 34
#define DHT_PIN 15

// Node identification
const char* NODE_ID = "NODE_1";

// Sensor object
DHTesp dht;

// Illustrative simulation thresholds
const int NORMAL_LIMIT = 1200;
const int WARNING_LIMIT = 2500;

// WiFi configuration
const char* WIFI_SSID = "Wokwi-GUEST";
const char* WIFI_PASSWORD = "";

// MQTT broker
const char* MQTT_SERVER = "broker.hivemq.com";
const int MQTT_PORT = 1883;

// Use a unique project topic
const char* MQTT_TOPIC = "iot-fungal/demo-7f3a/NODE_1";

WiFiClient espClient;
PubSubClient mqttClient(espClient);

void connectWiFi() {
  Serial.println("Connecting to WiFi...");

  WiFi.begin(WIFI_SSID, WIFI_PASSWORD, 6);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }

  Serial.println("\nWiFi connected!");
  Serial.println(WiFi.localIP());
}

void reconnectMQTT() {
  while (!mqttClient.connected()) {
    Serial.println("Connecting to MQTT...");

    String clientId = "IoTFungal_NODE_1";

    if (mqttClient.connect(clientId.c_str())) {
      Serial.println("MQTT connected!");
    } else {
      Serial.print("MQTT connection failed: ");
      Serial.println(mqttClient.state());
      delay(3000);
    }
  }
}

// ==========================================
// SETUP
// ==========================================

void setup() {

  Serial.begin(115200);

  connectWiFi();

  mqttClient.setServer(MQTT_SERVER, MQTT_PORT);

  analogReadResolution(12);
  analogSetPinAttenuation(MQ_PIN, ADC_11db);

  dht.setup(DHT_PIN, DHTesp::DHT22);

  Serial.println();
  Serial.println("================================");
  Serial.println("GRAIN FUNGAL HOTSPOT MONITOR");
  Serial.println("ESP32 SENSOR NODE INITIALIZED");
  Serial.println("NODE ID: NODE_1");
  Serial.println("================================");
}

// ==========================================
// RISK CLASSIFICATION
// ==========================================

String classifyRisk(int gasValue) {

  if (gasValue < NORMAL_LIMIT) {
    return "NORMAL";
  }

  else if (gasValue < WARNING_LIMIT) {
    return "WARNING";
  }

  else {
    return "HIGH ANOMALY";
  }
}

// ==========================================
// MAIN LOOP
// ==========================================

void loop() {

  // Read gas-response input
  int gasValue = analogRead(MQ_PIN);

  // Read temperature and humidity
  TempAndHumidity sensorData = dht.getTempAndHumidity();

  float temperature = sensorData.temperature;
  float humidity = sensorData.humidity;

  // Check DHT sensor readings
  if (isnan(temperature) || isnan(humidity)) {

    Serial.println("ERROR: DHT sensor reading failed");

    delay(2000);
    return;
  }

  // Determine risk status
  String status = classifyRisk(gasValue);

  if (!mqttClient.connected()) {
    reconnectMQTT();
  }

  mqttClient.loop();

  String payload = "{";
  payload += "\"node_id\":\"NODE_1\",";
  payload += "\"gas_response\":" + String(gasValue) + ",";
  payload += "\"temperature\":" + String(temperature, 2) + ",";
  payload += "\"humidity\":" + String(humidity, 2) + ",";
  payload += "\"status\":\"" + status + "\"";
  payload += "}";

  bool published = mqttClient.publish(
    MQTT_TOPIC,
    payload.c_str()
  );

  if (published) {
    Serial.println("MQTT PUBLISH SUCCESS:");
    Serial.println(payload);
  } else {
    Serial.println("MQTT PUBLISH FAILED");
  }

  // ========================================
  // HUMAN-READABLE SERIAL OUTPUT
  // ========================================

  Serial.println();
  Serial.println("--------- SENSOR READING ---------");

  Serial.print("Node ID: ");
  Serial.println(NODE_ID);

  Serial.print("Gas Response: ");
  Serial.println(gasValue);

  Serial.print("Temperature: ");
  Serial.print(temperature, 2);
  Serial.println(" C");

  Serial.print("Humidity: ");
  Serial.print(humidity, 2);
  Serial.println(" %");

  Serial.print("Risk Status: ");
  Serial.println(status);

  // ========================================
  // STRUCTURED JSON OUTPUT
  // One JSON object per line
  // ========================================

  Serial.print("{");

  Serial.print("\"node_id\":\"");
  Serial.print(NODE_ID);

  Serial.print("\",\"gas_response\":");
  Serial.print(gasValue);

  Serial.print(",\"temperature\":");
  Serial.print(temperature, 2);

  Serial.print(",\"humidity\":");
  Serial.print(humidity, 2);

  Serial.print(",\"status\":\"");
  Serial.print(status);

  Serial.println("\"}");

  Serial.println("----------------------------------");

  // Read every 2 seconds
  delay(2000);
}
