
import random
from datetime import datetime


NORMAL_LIMIT = 1200
WARNING_LIMIT = 2500


class SensorNode:

    def __init__(self, node_id, gas_value, temperature, humidity):

        self.node_id = node_id
        self.gas_value = gas_value
        self.temperature = temperature
        self.humidity = humidity

    def classify_risk(self, gas):

        if gas < NORMAL_LIMIT:
            return "NORMAL"

        elif gas < WARNING_LIMIT:
            return "WARNING"

        return "HIGH ANOMALY"

    def generate_reading(self):

        gas = max(
            0,
            min(4095, self.gas_value + random.randint(-30, 30))
        )

        temperature = self.temperature + random.uniform(-0.5, 0.5)
        humidity = self.humidity + random.uniform(-1, 1)

        return {
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "node_id": self.node_id,
            "gas_response": gas,
            "temperature": round(temperature, 2),
            "humidity": round(humidity, 2),
            "status": self.classify_risk(gas)
        }


# Three distributed storage nodes

nodes = [
    SensorNode("NODE_1", 500, 27, 55),
    SensorNode("NODE_2", 1800, 29, 68),
    SensorNode("NODE_3", 3000, 30, 75)
]


if __name__ == "__main__":

    import time

    print("GRAIN STORAGE SENSOR SIMULATION")

    try:
        while True:

            for node in nodes:
                print(node.generate_reading())

            time.sleep(3)

    except KeyboardInterrupt:
        print("Simulation stopped.")
