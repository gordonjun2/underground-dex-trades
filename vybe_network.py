import requests
from datetime import datetime, timedelta
import time
from config import VYBE_NETWORK_X_API_KEY


def get_token_details(mint_address):

    url = "https://api.vybenetwork.xyz/token/{}".format(mint_address)

    headers = {
        "accept": "application/json",
        "X-API-KEY": VYBE_NETWORK_X_API_KEY
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:

        token_details = response.json()

        return token_details

    else:
        print(
            'Query failed and return code is {}. API call limit might be reached. Please try again in a while.'
            .format(response.status_code))

        return {}


def get_token_holders_time_series(mint_address, days_ago=7, interval='hour'):

    now = datetime.now()
    datetime_days_ago = now - timedelta(days=days_ago)
    datetime_days_ago_timestamp = int(
        time.mktime(datetime_days_ago.timetuple()))

    url = "https://api.vybenetwork.xyz/token/{}/holders-ts?startTime={}&interval={}".format(
        mint_address, datetime_days_ago_timestamp, interval)

    headers = {
        "accept": "application/json",
        "X-API-KEY": VYBE_NETWORK_X_API_KEY
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        token_holders_time_series = response.json().get('data', [])

        return token_holders_time_series

    else:
        print(
            'Query failed and return code is {}. API call limit might be reached. Please try again in a while.'
            .format(response.status_code))

        return []


def get_token_volume_time_series(mint_address, days_ago=7, interval='hour'):

    now = datetime.now()
    datetime_days_ago = now - timedelta(days=days_ago)
    datetime_days_ago_timestamp = int(
        time.mktime(datetime_days_ago.timetuple()))

    url = "https://api.vybenetwork.xyz/token/{}/transfer-volume?startTime={}&interval={}".format(
        mint_address, datetime_days_ago_timestamp, interval)

    headers = {
        "accept": "application/json",
        "X-API-KEY": VYBE_NETWORK_X_API_KEY
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:
        token_holders_time_series = response.json().get('data', [])

        return token_holders_time_series

    else:
        print(
            'Query failed and return code is {}. API call limit might be reached. Please try again in a while.'
            .format(response.status_code))

        return []


def get_token_balances(owner_address):

    url = "https://api.vybenetwork.xyz/account/token-balance/{}".format(
        owner_address)

    headers = {
        "accept": "application/json",
        "X-API-KEY": VYBE_NETWORK_X_API_KEY
    }

    response = requests.get(url, headers=headers, verify=False)

    if response.status_code == 200:

        token_balances = response.json()

        return token_balances

    else:
        print(
            'Query failed and return code is {}. API call limit might be reached. Please try again in a while.'
            .format(response.status_code))

        return {}
