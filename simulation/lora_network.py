
import json
import time
import random

from sensor_nodes import nodes
from receiver import LoRaReceiver


# ==========================================
# SIMULATED LORA COMMUNICATION CHANNEL
# ==========================================

class LoRaChannel:

    def __init__(self):
        self.transmission_count = 0
        self.success_count = 0
        self.failed_count = 0

    def transmit(self, packet):

        self.transmission_count += 1

        print("\n========== LORA TRANSMISSION ==========")

        print("Sequence:", packet["sequence"])
        print("Source:", packet["payload"]["node_id"])

        # Simulated radio transmission delay
        time.sleep(0.3)

        # Simulate packet delivery
        delivery_success = random.random() > 0.05

        if not delivery_success:

            self.failed_count += 1

            print("[SIMULATED LORA] Packet lost!")
            return None

        # Serialize and deserialize JSON packet
        encoded_packet = json.dumps(packet)
        decoded_packet = json.loads(encoded_packet)

        # Illustrative simulated radio metrics
        simulated_rssi = random.randint(-110, -65)
        simulated_snr = round(random.uniform(-5, 10), 2)

        decoded_packet["radio_simulation"] = {
            "rssi_dbm": simulated_rssi,
            "snr_db": simulated_snr
        }

        self.success_count += 1

        print("[SIMULATED LORA] Packet received!")
        print("RSSI (simulated):", simulated_rssi, "dBm")
        print("SNR (simulated):", simulated_snr, "dB")

        return decoded_packet


# ==========================================
# GATEWAY INITIALIZATION
# ==========================================

gateway = LoRaReceiver()
channel = LoRaChannel()

print("\n======================================")
print("GRAIN FUNGAL HOTSPOT MONITOR")
print("THREE-NODE LORA NETWORK SIMULATION")
print("======================================")

print("Registered nodes:")

for node in nodes:
    print("-", node.node_id)


# ==========================================
# MAIN NETWORK LOOP
# ==========================================

try:

    cycle = 1

    while True:

        print("\n\n========== NETWORK CYCLE", cycle, "==========")

        for node in nodes:

            # Generate sensor reading
            reading = node.generate_reading()

            # Create structured packet
            packet = {
                "sequence": channel.transmission_count + 1,
                "network": "GRAIN_LORA_NETWORK",
                "payload": reading
            }

            # Simulated transmission
            received_packet = channel.transmit(packet)

            # Gateway reception
            if received_packet is not None:

                gateway.receive_packet(
                    received_packet["payload"]
                )

        # Display gateway summary
        gateway.show_summary()

        print("\nTransmission statistics:")
        print("Total transmitted:", channel.transmission_count)
        print("Successfully delivered:", channel.success_count)
        print("Failed packets:", channel.failed_count)

        cycle += 1

        time.sleep(3)


except KeyboardInterrupt:

    print("\n\n======================================")
    print("LORA NETWORK SIMULATION STOPPED")
    print("======================================")

    print("Total transmitted:", channel.transmission_count)
    print("Successfully delivered:", channel.success_count)
    print("Failed packets:", channel.failed_count)
