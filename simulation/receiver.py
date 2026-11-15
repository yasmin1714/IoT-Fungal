
import csv
import os
from datetime import datetime


class LoRaReceiver:

    def __init__(self):

        self.received_packets = 0

        # Store only the latest reading per node
        self.latest_status = {}

        # Dataset location
        self.dataset_path = os.path.join(
            os.path.dirname(__file__),
            "..",
            "dataset",
            "sensor_data.csv"
        )

        os.makedirs(
            os.path.dirname(self.dataset_path),
            exist_ok=True
        )

        # Create CSV file with headers if needed
        if not os.path.exists(self.dataset_path):

            with open(
                self.dataset_path,
                "w",
                newline=""
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "timestamp",
                    "node_id",
                    "gas_response",
                    "temperature",
                    "humidity",
                    "status"
                ])

    def receive_packet(self, packet):

        self.received_packets += 1

        # Extract information
        node_id = packet["node_id"]

        self.latest_status[node_id] = packet

        # Display received packet
        print("\n========== PACKET RECEIVED ==========")

        print("Receiver ID: ESP32_GATEWAY")
        print("Packet Number:", self.received_packets)

        print("Node ID:", node_id)
        print("Gas Response:", packet["gas_response"])
        print("Temperature:", packet["temperature"], "C")
        print("Humidity:", packet["humidity"], "%")
        print("Risk Status:", packet["status"])

        print("Timestamp:", packet["timestamp"])

        print("=====================================")

        # Save every packet to CSV
        with open(
            self.dataset_path,
            "a",
            newline=""
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                packet["timestamp"],
                node_id,
                packet["gas_response"],
                packet["temperature"],
                packet["humidity"],
                packet["status"]
            ])

    def show_summary(self):

        print("\n========== LATEST GATEWAY STATUS ==========")

        for node_id, packet in self.latest_status.items():

            print(
                node_id,
                "->",
                packet["status"]
            )

        print("\nTotal Packets:", self.received_packets)

        print("Dataset:", self.dataset_path)

        print("==========================================")
