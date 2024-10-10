import requests
import json
from datetime import datetime, timedelta
import schedule
import time
import os



# Configuration
UNIFI_CONTROLLER_IP = "192.168.0.1"  # Replace with your UniFi Controller IP
UNIFI_USERNAME =  os.getenv("USER", "admin") # Replace with your UniFi username
UNIFI_PASSWORD = os.getenv("PASSWORD", "password")  # Replace with your UniFi password
DEVICE_MAC = "ac:8b:a9:83:f3:1f"  # U-LTE-Pro MAC address
BILLING_CYCLE_START_DAY = 17  # Replace with your billing cycle start day

# API endpoints
LOGIN_URL = f"https://{UNIFI_CONTROLLER_IP}:443/api/login"
DEVICE_URL = f"https://{UNIFI_CONTROLLER_IP}:443/api/s/default/stat/device/{DEVICE_MAC}"

# Disable SSL warnings (use with caution in production)
requests.packages.urllib3.disable_warnings()

class LTEDataTracker:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.cumulative_usage = 0
        self.last_reset = None

    def login(self):
        response = self.session.post(LOGIN_URL, json={"username": UNIFI_USERNAME, "password": UNIFI_PASSWORD})
        response.raise_for_status()

    def get_device_data(self):
        response = self.session.get(DEVICE_URL)
        response.raise_for_status()
        return response.json()['data'][0]

    def calculate_usage(self):
        device_data = self.get_device_data()
        lte_rx_bytes = device_data['stat'].get('lte_rxbytes', 0)
        lte_tx_bytes = device_data['stat'].get('lte_txbytes', 0)
        current_usage = lte_rx_bytes + lte_tx_bytes

        if self.last_reset is None or self.should_reset_usage():
            self.cumulative_usage = current_usage
            self.last_reset = datetime.now()
        else:
            self.cumulative_usage += current_usage

        return self.cumulative_usage

    def should_reset_usage(self):
        now = datetime.now()
        if self.last_reset is None:
            return True
        if now.day == BILLING_CYCLE_START_DAY and now.month != self.last_reset.month:
            return True
        return False

    def run(self):
        try:
            self.login()
            usage = self.calculate_usage()
            print(f"Cumulative LTE data usage: {usage / (1024*1024):.2f} MB")
        except Exception as e:
            print(f"Error: {str(e)}")

def job():
    tracker = LTEDataTracker()
    tracker.run()

# Run the job every hour
schedule.every().second.do(job)

if __name__ == "__main__":
    print("LTE Data Usage Tracker started. Press Ctrl+C to exit.")
    while True:
        schedule.run_pending()
        time.sleep(1)