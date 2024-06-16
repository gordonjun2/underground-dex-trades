import requests
import datetime
from urllib3.exceptions import InsecureRequestWarning
import urllib3
from utils import save_json_file
from config import VYBE_NETWORK_X_API_KEY

urllib3.disable_warnings(InsecureRequestWarning)

url = "https://api.vybenetwork.xyz/tokens?sortByDesc=marketCap&limit=1000&page=0"

headers = {"accept": "application/json", "X-API-KEY": VYBE_NETWORK_X_API_KEY}

response = requests.get(url, headers=headers, verify=False)

if response.status_code == 200:
    print("\nRequest successful!")
    tokens_data = response.json().get('data', [])
    print('\nNo. of tokens queried: {}'.format(len(tokens_data)))

    mint_addresses = [token['mintAddress'] for token in tokens_data]

else:
    raise Exception('Query failed and return code is {}.'.format(
        response.status_code))

current_datetime = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
file_name = f"vybe_network_highest_mcap_mint_addresses_{current_datetime}.json"

save_json_file(file_name, mint_addresses)
