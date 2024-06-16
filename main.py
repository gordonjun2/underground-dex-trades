import requests
import json
import pytz
from datetime import datetime, timedelta
from tzlocal import get_localzone
from collections import deque
from urllib3.exceptions import InsecureRequestWarning
import urllib3
import time
import argparse
import sys
from itertools import groupby
from utils import *
import dexscreener
import vybe_network
from config import (BITQUERY_CLIENT_ID, BITQUERY_CLIENT_SECRET,
                    BITQUERY_V1_API_KEY, API_VERSION, API_VERSION_URL_MAP,
                    EXCLUDED_MINT_ADDRESSES, variables)

urllib3.disable_warnings(InsecureRequestWarning)

### Functions ###


def generate_oAuth():

    url = "https://oauth2.bitquery.io/oauth2/token"

    payload = 'grant_type=client_credentials&client_id={}&client_secret={}&scope=api'.format(
        BITQUERY_CLIENT_ID, BITQUERY_CLIENT_SECRET)

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}

    response = requests.request("POST",
                                url,
                                headers=headers,
                                data=payload,
                                verify=False)
    resp = json.loads(response.text)

    print("========== oAuth's reponse ==========")
    print(resp)
    print('=====================================')

    access_token = resp['access_token']

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {access_token}'
    }

    return headers


def get_api_base_url():

    if API_VERSION not in API_VERSION_URL_MAP:
        raise ValueError(
            f"API version {API_VERSION} is not supported. Supported API versions are {list(API_VERSION_URL_MAP.keys())}"
        )
    else:
        url = API_VERSION_URL_MAP[API_VERSION]

        return url


def bitqueryAPICall(payload, max_retries=10, retry_after=10):

    retry_count = 0

    while retry_count < max_retries:

        if API_VERSION == 'v1':
            response = requests.post(url,
                                     json=payload,
                                     headers=headers,
                                     verify=False)
        else:
            response = requests.post(url,
                                     headers=headers,
                                     data=json.dumps(payload),
                                     verify=False)

        if response.status_code == 200:
            try:
                dex_trades_data = response.json().get('data', {}).get(
                    'Solana', {}).get('DEXTrades', [])

                if not isinstance(dex_trades_data, list):
                    print(
                        'The retrieved DEX Trades data is in the wrong format. Skipping...'
                    )

                    dex_trades_data = []
            except:
                print('The DEX Trades data is missing. Skipping...')

                dex_trades_data = []

            return dex_trades_data

        elif response.status_code == 429:
            # TODO need to exit the program if API limit is reached
            retry_count += 1

            print(
                'Query failed and return code is 429. API call limit might be reached. Retrying ({}) after {} seconds...'
                .format(retry_count, retry_after))

            time.sleep(retry_after)

        else:
            retry_count += 1

            print(
                'Query failed and return code is {}. Retrying ({})...'.format(
                    response.status_code, retry_count))

    print('Maximum retries reached. Skipping...')

    return []


def accumulate_txn_signatures(mint_address):

    query = f"""
    query {{
    Solana {{
        DEXTrades(
        where: {{Transaction: {{Result: {{Success: true}}}}, Block: {{Time: {{since: "{two_days_before_utc_str}"}}}}, any: [{{Trade: {{Buy: {{Currency: {{MintAddress: {{is: "{mint_address}"}}}}}}}}}}, {{Trade: {{Sell: {{Currency: {{MintAddress: {{is: "{mint_address}"}}}}}}}}}}]}}
        orderBy: {{descending: Block_Time}}
        limitBy: {{by: Transaction_Signature, count: 1}}
        ) {{
        Trade {{
            Buy {{
            Currency {{
                MintAddress
            }}
            }}
            Sell {{
            Currency {{
                MintAddress
            }}
            }}
        }}
        Transaction {{
            Signature
        }}
        Block {{
            Time
        }}
        }}
    }}
    }}
    """

    payload = {'query': query, 'variables': variables}
    dex_trades_data = bitqueryAPICall(payload)

    new_mint_addresses = get_mint_addresses_and_unique_signatures(
        dex_trades_data)

    print('No. of DEX Trades queried for the mint address {}: {}'.format(
        mint_address, len(dex_trades_data)))

    return new_mint_addresses


def get_mint_addresses_and_unique_signatures(dex_trades_data):

    new_mint_addresses = set()

    for trade in dex_trades_data:
        buy_mint_address = trade['Trade']['Buy']['Currency']['MintAddress']
        sell_mint_address = trade['Trade']['Sell']['Currency']['MintAddress']

        if buy_mint_address not in EXCLUDED_MINT_ADDRESSES:
            new_mint_addresses.add(buy_mint_address)
        if sell_mint_address not in EXCLUDED_MINT_ADDRESSES:
            new_mint_addresses.add(sell_mint_address)

        signature = trade['Transaction']['Signature']
        unique_signatures.add(signature)

    return new_mint_addresses


def bfs_accumulate_unique_signatures(mint_address, max_node_depth):
    """
    Traverse the tree of mint addresses up to the specified depth using BFS.
    
    :param mint_address: The starting mint address.
    :param max_node_depth: The depth to which the function should traverse.

    :return: A set of unique mint addresses.
    """
    if max_node_depth <= 0:
        return {mint_address}

    queue = deque([(mint_address, 0)])
    depth_node_count_dict = {0: 1}
    previous_node_depth = -1
    unique_mint_addresses = set()

    while queue:
        current_mint_address, current_node_depth = queue.popleft()

        if current_mint_address not in unique_mint_addresses:
            unique_mint_addresses.add(current_mint_address)

            if current_node_depth < max_node_depth:

                if previous_node_depth != current_node_depth:
                    mint_address_depth_count = 1
                else:
                    mint_address_depth_count += 1

                print('\nQuerying mint address {} from depth {} ({} / {})'.
                      format(current_mint_address, current_node_depth,
                             mint_address_depth_count,
                             depth_node_count_dict[current_node_depth]))
                children_mint_addresses = accumulate_txn_signatures(
                    current_mint_address)

                save_json_file(saved_unique_mint_addresses_file_path,
                               list(unique_mint_addresses))
                save_json_file(saved_unique_signatures_file_path,
                               list(unique_signatures))

                for children_mint_address in children_mint_addresses:
                    if children_mint_address not in unique_mint_addresses:
                        queue.append(
                            (children_mint_address, current_node_depth + 1))
                        if current_node_depth + 1 not in depth_node_count_dict:
                            depth_node_count_dict[current_node_depth + 1] = 1
                        else:
                            depth_node_count_dict[current_node_depth + 1] += 1

                previous_node_depth = current_node_depth

    return unique_mint_addresses


def get_dex_trades_data(unique_signatures,
                        max_no_of_signatures_per_batch=10000):

    unique_signatures_list = list(unique_signatures)
    total_unique_signatures = len(unique_signatures)

    for i in range(0, total_unique_signatures, max_no_of_signatures_per_batch):

        unique_signatures_batch = unique_signatures_list[
            i:i + max_no_of_signatures_per_batch]

        unique_signatures_batch_json = json.dumps(unique_signatures_batch)

        query = f"""
        query {{
        Solana {{
            DEXTrades(
            where: {{Transaction: {{Signature: {{in: {unique_signatures_batch_json}}}}}}}
            orderBy: {{ascendingByField: "Transaction_Signature", ascending: Trade_Index}}
            ) {{
            Trade {{
                Buy {{
                Amount
                AmountInUSD
                Currency {{
                    MintAddress
                    Name
                    Symbol
                }}
                PriceInUSD
                }}
                Dex {{
                    ProgramAddress
                    ProtocolName
                }}
                Sell {{
                Amount
                AmountInUSD
                Currency {{
                    MintAddress
                    Name
                    Symbol
                }}
                PriceInUSD
                }}
                Index
            }}
            Transaction {{
                Signature
            }}
            Block {{
                Time
            }}
            }}
        }}
        }}
        """

        start_number = i + 1

        if i + max_no_of_signatures_per_batch > total_unique_signatures:
            end_number = total_unique_signatures
        else:
            end_number = i + max_no_of_signatures_per_batch

        print('\nQuerying transaction signature {} - {} out of {}'.format(
            start_number, end_number, total_unique_signatures))

        payload = {'query': query, 'variables': variables}
        dex_trades_data = bitqueryAPICall(payload)

        if len(dex_trades_data) == 0:
            print(
                '\nNo DEX trades data retrieved in this batch of transaction signatures. Use newer transaction signatures instead.'
            )
            continue
        else:
            print(
                'No. of unprocessed DEX Trades queried for this batch of transaction signatures: {}'
                .format(len(dex_trades_data)))

        process_dex_trades_data(dex_trades_data)

        save_json_file(saved_trades_file_path, combined_dex_trades_data)
        save_json_file(saved_remaining_mint_addresses_file_path,
                       list(remaining_mint_addresses))


def process_dex_trades_data(dex_trades_data):

    for _, transactions in groupby(
            dex_trades_data, key=lambda x: x['Transaction']['Signature']):
        transactions_list = list(transactions)

        first_transaction = transactions_list[0]
        last_transaction = transactions_list[-1]

        first_transaction_trade = first_transaction['Trade']
        last_transaction_trade = last_transaction['Trade']
        transaction_block = first_transaction['Block']
        transaction_transaction = first_transaction['Transaction']

        first_transaction_trade_sell_mint_address = first_transaction_trade[
            'Sell']['Currency']['MintAddress']
        last_transaction_trade_buy_mint_address = last_transaction_trade[
            'Buy']['Currency']['MintAddress']

        # Check if MEV
        if first_transaction_trade_sell_mint_address == last_transaction_trade_buy_mint_address:
            continue

        # Check if addresses are excluded
        elif (first_transaction_trade_sell_mint_address
              in EXCLUDED_MINT_ADDRESSES
              or last_transaction_trade_buy_mint_address
              in EXCLUDED_MINT_ADDRESSES):
            continue

        else:
            summarized_trade = {
                'Block': transaction_block,
                'Trade': {
                    'Sell': first_transaction_trade['Sell'],
                    'Buy': last_transaction_trade['Buy']
                },
                'Transaction': transaction_transaction
            }

            combined_dex_trades_data.append(summarized_trade)
            remaining_mint_addresses.add(
                first_transaction_trade_sell_mint_address)
            remaining_mint_addresses.add(
                last_transaction_trade_buy_mint_address)


## Main Program ##

if __name__ == "__main__":

    # Get arguments from terminal
    parser = argparse.ArgumentParser(
        description="Get parameters for the script.")
    parser.add_argument(
        '-m',
        '--mode',
        type=str,
        default='BFS',
        help=
        "BFS: use Breadth First Search to traverse and query the tree of the provided mint address up to the specified depth and retrieve transaction signatures and DEX trades data, \
        INPUT: provide a list of mint addresses to query and retrieve transaction signatures and DEX trades data, \
        LOAD_SIGNATURES: load the transaction signatures from a saved JSON file and retrieve DEX trades data, and \
        LOAD_TRADES: skip the query process and load the DEX trades data from a saved JSON file."
    )
    parser.add_argument(
        '-a',
        '--address',
        type=str,
        help="The first mint address to query. REQURING for BFS mode.")
    parser.add_argument(
        '-d',
        '--depth',
        type=int,
        default=2,
        help="The depth to which the function should traverse. Default is 2.")
    parser.add_argument(
        '-f',
        '--file',
        type=str,
        help=
        "The file to load the JSON that contains the list of mint addresses, the list of unique signatires, or the DEX trades data. REQURED for INPUT, LOAD_SIGNATURES, and LOAD_TRADES mode."
    )
    parser.add_argument(
        '-af',
        '--addresses_file',
        type=str,
        help=
        "The file to load the JSON that contains the list of remaining mint addresses. REQURED for LOAD_TRADES mode."
    )
    parser.add_argument(
        '-v',
        '--volume',
        type=float,
        default=0,
        help=
        "The minimum volume threshold for the DEX trades data to be displayed for graph plot. Default is 0."
    )
    args = parser.parse_args()

    mode = str(args.mode).upper()
    mint_address = args.address
    max_node_depth = args.depth
    file_path = args.file
    addresses_file_path = args.addresses_file
    volume_threshold = args.volume

    if mode not in ['BFS', 'INPUT', 'LOAD_SIGNATURES', 'LOAD_TRADES']:
        print(
            "\nMode {} is not supported. Supported modes are BFS, INPUT, and LOAD.\n"
            .format(mode))
        sys.exit(1)

    # Get current datetime
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Get datetime two days before the current local time
    local_timezone = get_localzone()
    current_time = datetime.now(local_timezone)
    two_days_before = current_time - timedelta(days=5)
    two_days_before_utc = two_days_before.astimezone(pytz.utc)
    two_days_before_utc_str = two_days_before_utc.strftime(
        '%Y-%m-%dT%H:%M:%SZ')

    unique_signatures = set()
    combined_dex_trades_data = []
    remaining_mint_addresses = set()
    start_time = time.time()

    print('\n')

    url = get_api_base_url()

    if API_VERSION == 'v1':
        headers = {'X-API-KEY': BITQUERY_V1_API_KEY}
    else:
        headers = generate_oAuth()

    if mode in 'BFS':

        print("\nMode: {}".format(mode))
        print("First Mint Address: {}".format(mint_address))
        print("Max Node Depth: {}".format(max_node_depth))
        print("Minimum Volume Threshold: {}".format(volume_threshold))

        if mint_address in ['', None]:
            print(
                "\nPlease provide the first mint address to query in BFS mode.\n"
            )
            sys.exit(1)

        saved_unique_mint_addresses_file_path = f"unique_mint_addresses_BFS_{mint_address}_{current_datetime}.json"
        saved_unique_signatures_file_path = f"unique_signatures_BFS_{mint_address}_{current_datetime}.json"
        saved_trades_file_path = f"combined_dex_trades_data_BFS_{mint_address}_{current_datetime}.json"
        saved_remaining_mint_addresses_file_path = f"remaining_mint_addresses_BFS_{mint_address}_{current_datetime}.json"

        unique_mint_addresses = bfs_accumulate_unique_signatures(
            mint_address, max_node_depth)
        total_no_of_unique_mint_addresses = len(unique_mint_addresses)

        print('\nNo. of unique mint addresses retrieved: {}'.format(
            total_no_of_unique_mint_addresses))

        print('\nNo. of unique signatures retrieved: {}'.format(
            len(unique_signatures)))

        get_dex_trades_data(unique_signatures)

        print('\nNo. of processed DEX Trades data retrieved: {}'.format(
            len(combined_dex_trades_data)))

        print('\nTotal time taken to query: {:.2f} seconds\n'.format(
            time.time() - start_time))

    elif mode == 'INPUT':

        print("\nMode: {}".format(mode))
        print("File Path to the List of Mint Addresses: {}".format(file_path))
        print("Minimum Volume Threshold: {}".format(volume_threshold))

        if file_path in ['', None]:
            print(
                "\nPlease provide the file path to load the list of mint addresses in INPUT mode.\n"
            )
            sys.exit(1)

        unique_mint_addresses = load_json_file(file_path)
        unique_mint_addresses = set(unique_mint_addresses) - set(
            EXCLUDED_MINT_ADDRESSES)
        total_no_of_unique_mint_addresses = len(unique_mint_addresses)

        print('\nNo. of unique mint addresses retrieved: {}'.format(
            total_no_of_unique_mint_addresses))

        saved_unique_signatures_file_path = f"unique_signatures_INPUT_{current_datetime}.json"
        saved_trades_file_path = f"combined_dex_trades_data_INPUT_{current_datetime}.json"

        mint_address_count = 1

        for mint_address in unique_mint_addresses:
            print('\nQuerying mint address {} ({} / {})'.format(
                mint_address, mint_address_count,
                total_no_of_unique_mint_addresses))

            accumulate_txn_signatures(mint_address)

            save_json_file(saved_unique_signatures_file_path,
                           list(unique_signatures))

            mint_address_count += 1

        print('\nNo. of unique signatures retrieved: {}'.format(
            len(unique_signatures)))

        get_dex_trades_data(unique_signatures)

        print('\nNo. of processed DEX Trades data retrieved: {}'.format(
            len(combined_dex_trades_data)))

        print('\nTotal time taken to query: {:.2f} seconds\n'.format(
            time.time() - start_time))

    elif mode == 'LOAD_SIGNATURES':

        print("\nMode: {}".format(mode))
        print("File Path to the Saved Unique Signatures: {}".format(file_path))
        print("Minimum Volume Threshold: {}".format(volume_threshold))

        if file_path in ['', None]:
            print(
                "\nPlease provide the file path to load the uniques signatures in LOAD_SIGNATURES mode.\n"
            )
            sys.exit(1)

        unique_signatures = load_json_file(file_path)

        print('\nNo. of unique signatures retrieved: {}'.format(
            len(unique_signatures)))

        saved_trades_file_path = f"combined_dex_trades_data_LOAD_{current_datetime}.json"

        get_dex_trades_data(unique_signatures)

        print('\nNo. of processed DEX Trades data retrieved: {}'.format(
            len(combined_dex_trades_data)))

        print('\nTotal time taken to query: {:.2f} seconds\n'.format(
            time.time() - start_time))

    else:

        print("\nMode: {}".format(mode))
        print("File Path to the Saved DEX Trades Data: {}".format(file_path))
        print("Minimum Volume Threshold: {}".format(volume_threshold))

        if file_path in ['', None]:
            print(
                "\nPlease provide the file path to load the DEX trades data in LOAD_TRADES mode.\n"
            )
            sys.exit(1)

        combined_dex_trades_data = load_json_file(file_path)
        remaining_mint_addresses = load_json_file(addresses_file_path)

        print('\nNo. of processed DEX Trades data retrieved: {}'.format(
            len(combined_dex_trades_data)))

        print(
            '\nTotal time taken to load: {:.2f} seconds\n'.format(time.time() -
                                                                  start_time))

    token_details_dict = dexscreener.get_token_details(
        list(remaining_mint_addresses))

# Nodes and Edges Data Structure

# graph = {
#     'nodes': {
#         'A': {'name': 'Node A', 'value': 1},
#         'B': {'name': 'Node B', 'value': 2},
#         'C': {'name': 'Node C', 'value': 3},
#         'D': {'name': 'Node D', 'value': 4},
#     },
#     'edges': [
#         {'source': 'A', 'target': 'B', 'weight': 5},
#         {'source': 'A', 'target': 'C', 'weight': 3},
#         {'source': 'B', 'target': 'D', 'weight': 4},
#         {'source': 'C', 'target': 'D', 'weight': 2}
#     ]
# }
