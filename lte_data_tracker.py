import requests
import json
from datetime import datetime, timedelta
import schedule
import time
import os

# Configuration
UNIFI_CONTROLLER_IP = "192.168.0.1"
UNIFI_USERNAME = os.getenv("USER", "admin")
UNIFI_PASSWORD = os.getenv("PASSWORD", "password")
DEVICE_MAC = "ac:8b:a9:83:f3:1f"
BILLING_CYCLE_START_DAY = 17
DATA_FILE = "lte_usage_data.json"

# API endpoints
LOGIN_URL = f"https://{UNIFI_CONTROLLER_IP}:443/api/auth/login"
DEVICE_URL = f"https://{UNIFI_CONTROLLER_IP}:443/proxy/network/api/s/default/stat/device/{DEVICE_MAC}"

requests.packages.urllib3.disable_warnings()

class LTEDataTracker:
    def __init__(self):
        self.session = requests.Session()
        self.session.verify = False
        self.load_data()

    def load_data(self):
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                self.cumulative_usage = data.get('cumulative_usage', 0)
                last_reset = data.get('last_reset')
                self.last_reset = datetime.fromisoformat(last_reset) if last_reset else None
        else:
            self.cumulative_usage = 0
            self.last_reset = None

    def save_data(self):
        data = {
            'cumulative_usage': self.cumulative_usage,
            'last_reset': self.last_reset.isoformat() if self.last_reset else None
        }
        with open(DATA_FILE, 'w') as f:
            json.dump(data, f)

    def login(self):
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        payload = {
            "username": UNIFI_USERNAME,
            "password": UNIFI_PASSWORD
        }
        response = self.session.post(LOGIN_URL, headers=headers, json=payload)
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

        self.save_data()
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
            print(f"Last reset: {self.last_reset}")
        except Exception as e:
            print(f"Error: {str(e)}")

def job():
    tracker = LTEDataTracker()
    tracker.run()

# Run the job every hour
schedule.every().hour.do(job)

if __name__ == "__main__":
    print("LTE Data Usage Tracker started. Press Ctrl+C to exit.")
    while True:
        schedule.run_pending()
        time.sleep(1)