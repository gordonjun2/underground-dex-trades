import requests
import os
import datetime
from urllib3.exceptions import InsecureRequestWarning
import urllib3
from utils import save_json_file
from config import BIRDEYE_AGENT_ID, BIRDEYE_USER_AGENT

urllib3.disable_warnings(InsecureRequestWarning)

url = "https://multichain-api.birdeye.so/solana/gems"
payload = {
    "export": False,
    "limit": 50,
    "offset": 0,
    "query": [],
    "sort_by": "v24hUSD",
    "sort_type": "desc"
}

headers = {
    "Accept": "application/json, text/plain, */*",
    "Accept-Encoding": "gzip, deflate, br, zstd",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
    "Agent-Id": BIRDEYE_AGENT_ID,
    "Origin": "https://birdeye.so",
    "Referer": "https://birdeye.so/",
    "User-Agent": BIRDEYE_USER_AGENT
}

response = requests.post(url, headers=headers, json=payload, verify=False)

if response.status_code == 200:
    print("\nRequest successful!")

    try:
        tokens_data = response.json().get('data', {}).get('items', [])

        if not isinstance(tokens_data, list):
            tokens_data = []
    except:
        tokens_data = []

    mint_addresses = [token['address'] for token in tokens_data]

else:
    raise Exception('\nQuery failed and return code is {}.'.format(
        response.status_code))

saved_data_folder_file_path = './saved_data'
if not os.path.exists(saved_data_folder_file_path):
    os.makedirs(saved_data_folder_file_path)

current_datetime = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
file_name = f"{saved_data_folder_file_path}/birdeye_highest_24hr_volume_mint_addresses_{current_datetime}.json"

save_json_file(file_name, mint_addresses)
