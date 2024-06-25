import requests
import os
import json
import pytz
from datetime import datetime, timedelta
from tzlocal import get_localzone
from collections import deque
import warnings
import time
import argparse
import sys
import copy
from itertools import groupby
from utils import *
import dexscreener
from plot_graph import plot_nodes_edges_graph
from config import (BITQUERY_CLIENT_ID, BITQUERY_CLIENT_SECRET,
                    BITQUERY_V1_API_KEY, BITQUERY_API_VERSION,
                    BITQUERY_API_VERSION_URL_MAP, EXCLUDED_MINT_ADDRESSES,
                    variables, MAX_RETRIES, RETRY_AFTER,
                    MAX_NO_OF_SIGNATURES_PER_BATCH)

warnings.filterwarnings("ignore", module="urllib3")

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

    if BITQUERY_API_VERSION not in BITQUERY_API_VERSION_URL_MAP:
        raise ValueError(
            f"API version {BITQUERY_API_VERSION} is not supported. Supported API versions are {list(BITQUERY_API_VERSION_URL_MAP.keys())}"
        )
    else:
        url = BITQUERY_API_VERSION_URL_MAP[BITQUERY_API_VERSION]

        return url


def bitqueryAPICall(payload, max_retries=MAX_RETRIES, retry_after=RETRY_AFTER):

    retry_count = 0

    while retry_count < max_retries:

        if BITQUERY_API_VERSION == 'v1':
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
        where: {{Transaction: {{Result: {{Success: true}}}}, Block: {{Time: {{since: "{n_days_before_utc_str}"}}}}, any: [{{Trade: {{Buy: {{Currency: {{MintAddress: {{is: "{mint_address}"}}}}}}}}}}, {{Trade: {{Sell: {{Currency: {{MintAddress: {{is: "{mint_address}"}}}}}}}}}}]}}
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


def get_dex_trades_data(
        unique_signatures,
        max_no_of_signatures_per_batch=MAX_NO_OF_SIGNATURES_PER_BATCH):

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
                    'Sell': copy.deepcopy(first_transaction_trade['Sell']),
                    'Buy': copy.deepcopy(last_transaction_trade['Buy'])
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
        LOAD_SIGNATURES: load the transaction signatures from a saved JSON file and retrieve DEX trades data, \
        LOAD_TRADES: skip the query process and load the DEX trades data from a saved JSON file, and \
        PLOT: skip the query process and load the graph data from a saved JSON file."
    )
    parser.add_argument(
        '-a',
        '--address',
        type=str,
        help="The first mint address to query. REQURED for BFS mode.")
    parser.add_argument(
        '-d',
        '--depth',
        type=int,
        default=2,
        help=
        "The depth to which the function should traverse. Default is 2. REQURED for BFS mode."
    )
    parser.add_argument(
        '-f',
        '--file',
        type=str,
        help=
        "The file to load the JSON that contains the list of mint addresses, the list of unique signatures, or the DEX trades data. REQURED for INPUT, LOAD_SIGNATURES, LOAD_TRADES, PLOT mode."
    )
    parser.add_argument(
        '-af',
        '--addresses_file',
        type=str,
        help=
        "The file to load the JSON that contains the list of remaining mint addresses. REQURED for LOAD_TRADES mode."
    )
    parser.add_argument(
        '-s',
        '--since_days',
        type=int,
        default=2,
        help=
        "The number of days before the current local time to query the DEX trades data. Default is 2."
    )
    parser.add_argument(
        '-v',
        '--volume',
        type=float,
        default=0,
        help=
        "The minimum volume threshold in USD for the DEX trades data to be displayed for graph plot. Default is 0."
    )
    parser.add_argument(
        '-pfn',
        '--plot_filter_names',
        type=str,
        default='',
        help=
        "Filter token name and its related token name to be displayed for graph plot. Use comma separator. Use EITHER plot_filter_names or plot_filter_symbols but not both. Eg. 'dogwifhat,nubcat'."
    )
    parser.add_argument(
        '-pfs',
        '--plot_filter_symbols',
        type=str,
        default='',
        help=
        "Filter token symbol and its related token symbol to be displayed for graph plot. Use comma separator. Use EITHER plot_filter_names or plot_filter_symbols but not both. Eg. 'WIF,NUB'."
    )
    args = parser.parse_args()

    mode = str(args.mode).upper()
    mint_address = args.address
    max_node_depth = args.depth
    file_path = args.file
    addresses_file_path = args.addresses_file
    since_days = args.since_days
    volume_threshold = args.volume
    plot_filter_names = args.plot_filter_names
    plot_filter_symbols = args.plot_filter_symbols

    if mode not in ['BFS', 'INPUT', 'LOAD_SIGNATURES', 'LOAD_TRADES', 'PLOT']:
        print(
            "\nMode {} is not supported. Supported modes are BFS, INPUT, LOAD_SIGNATURES, LOAD_TRADES, and PLOT.\n"
            .format(mode))
        sys.exit(1)

    if plot_filter_names and plot_filter_symbols:
        print(
            "\nUse EITHER plot_filter_names or plot_filter_symbols but not both.\n"
        )
        sys.exit(1)
    elif plot_filter_names:
        filter_type = 'NAME'
    elif plot_filter_symbols:
        filter_type = 'SYMBOL'
    else:
        filter_type = 'NONE'

    # Start time for the script
    start_time = time.time()

    # Get current datetime
    current_datetime = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Get datetime two days before the current local time
    local_timezone = get_localzone()
    current_time = datetime.now(local_timezone)
    n_days_before = current_time - timedelta(days=since_days)
    n_days_before_utc = n_days_before.astimezone(pytz.utc)
    n_days_before_utc_str = n_days_before_utc.strftime('%Y-%m-%dT%H:%M:%SZ')

    unique_signatures = set()
    combined_dex_trades_data = []
    remaining_mint_addresses = set()
    graph_data = {'nodes': {}, 'edges': {}}
    earliest_local_block_time = datetime.max.replace(tzinfo=local_timezone)
    latest_local_block_time = datetime.min.replace(tzinfo=local_timezone)

    saved_data_folder_file_path = './saved_data'
    if not os.path.exists(saved_data_folder_file_path):
        os.makedirs(saved_data_folder_file_path)

    print('\n')

    url = get_api_base_url()

    if BITQUERY_API_VERSION == 'v1':
        headers = {'X-API-KEY': BITQUERY_V1_API_KEY}
    else:
        headers = generate_oAuth()

    if mode in ['BFS', 'INPUT', 'LOAD_SIGNATURES', 'LOAD_TRADES']:

        if mode in 'BFS':

            print("\nMode: {}".format(mode))
            print("First Mint Address: {}".format(mint_address))
            print("Max Node Depth: {}".format(max_node_depth))
            print("No. of days ago to query the data from: {}".format(
                since_days))
            print(
                "Minimum Volume Threshold in USD: {}".format(volume_threshold))

            if mint_address in ['', None]:
                print(
                    "\nPlease provide the first mint address to query in BFS mode.\n"
                )
                sys.exit(1)

            saved_unique_mint_addresses_file_path = f"{saved_data_folder_file_path}/unique_mint_addresses_BFS_{mint_address}_{current_datetime}.json"
            saved_unique_signatures_file_path = f"{saved_data_folder_file_path}/unique_signatures_BFS_{mint_address}_{current_datetime}.json"
            saved_trades_file_path = f"{saved_data_folder_file_path}/combined_dex_trades_data_BFS_{mint_address}_{current_datetime}.json"
            saved_remaining_mint_addresses_file_path = f"{saved_data_folder_file_path}/remaining_mint_addresses_BFS_{mint_address}_{current_datetime}.json"

            unique_mint_addresses = bfs_accumulate_unique_signatures(
                mint_address, max_node_depth)
            total_no_of_unique_mint_addresses = len(unique_mint_addresses)

            print('\nNo. of unprocessed unique mint addresses retrieved: {}'.
                  format(total_no_of_unique_mint_addresses))

            print('\nNo. of unique signatures retrieved: {}'.format(
                len(unique_signatures)))

            get_dex_trades_data(unique_signatures)

        elif mode == 'INPUT':

            print("\nMode: {}".format(mode))
            print("File Path to the List of Mint Addresses: {}".format(
                file_path))
            print("No. of days ago to query the data from: {}".format(
                since_days))
            print(
                "Minimum Volume Threshold in USD: {}".format(volume_threshold))

            if file_path in ['', None]:
                print(
                    "\nPlease provide the file path to load the list of mint addresses in INPUT mode.\n"
                )
                sys.exit(1)

            unique_mint_addresses = load_json_file(file_path)
            unique_mint_addresses = set(unique_mint_addresses) - set(
                EXCLUDED_MINT_ADDRESSES)
            total_no_of_unique_mint_addresses = len(unique_mint_addresses)

            print('\nNo. of unprocessed unique mint addresses retrieved: {}'.
                  format(total_no_of_unique_mint_addresses))

            saved_unique_signatures_file_path = f"{saved_data_folder_file_path}/unique_signatures_INPUT_{current_datetime}.json"
            saved_trades_file_path = f"{saved_data_folder_file_path}/combined_dex_trades_data_INPUT_{current_datetime}.json"
            saved_remaining_mint_addresses_file_path = f"{saved_data_folder_file_path}/remaining_mint_addresses_INPUT_{current_datetime}.json"

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

        elif mode == 'LOAD_SIGNATURES':

            print("\nMode: {}".format(mode))
            print("File Path to the Saved Unique Signatures: {}".format(
                file_path))
            print("No. of days ago to query the data from: {}".format(
                since_days))
            print(
                "Minimum Volume Threshold in USD: {}".format(volume_threshold))

            if file_path in ['', None]:
                print(
                    "\nPlease provide the file path to load the uniques signatures in LOAD_SIGNATURES mode.\n"
                )
                sys.exit(1)

            unique_signatures = load_json_file(file_path)

            print('\nNo. of unique signatures retrieved: {}'.format(
                len(unique_signatures)))

            saved_trades_file_path = f"{saved_data_folder_file_path}/combined_dex_trades_data_LOAD_{current_datetime}.json"
            saved_remaining_mint_addresses_file_path = f"{saved_data_folder_file_path}/remaining_mint_addresses_LOAD_{current_datetime}.json"

            get_dex_trades_data(unique_signatures)

        else:

            print("\nMode: {}".format(mode))
            print(
                "File Path to the Saved DEX Trades Data: {}".format(file_path))
            print("File Path to the Saved Remaining Mint Addresses: {}".format(
                addresses_file_path))
            print("No. of days ago to query the data from: {}".format(
                since_days))
            print(
                "Minimum Volume Threshold in USD: {}".format(volume_threshold))

            if file_path in ['', None]:
                print(
                    "\nPlease provide the file path to load the DEX trades data in LOAD_TRADES mode.\n"
                )
                sys.exit(1)

            if addresses_file_path in ['', None]:
                print(
                    "\nPlease provide the file path to load the remaining mint addresses in LOAD_TRADES mode.\n"
                )
                sys.exit(1)

            combined_dex_trades_data = load_json_file(file_path)
            remaining_mint_addresses = load_json_file(addresses_file_path)

        print('\nNo. of processed DEX Trades data retrieved: {}'.format(
            len(combined_dex_trades_data)))

        print('\nNo. of processed unique mint addresses retrieved: {}'.format(
            len(remaining_mint_addresses)))

        if combined_dex_trades_data:

            token_details_dict = dexscreener.get_token_details(
                list(remaining_mint_addresses))

            for dex_trade in combined_dex_trades_data:

                block_time = dex_trade['Block']['Time']
                local_block_time = convert_utc_to_user_timezone(block_time)

                if local_block_time < earliest_local_block_time:
                    earliest_local_block_time = local_block_time
                if local_block_time > latest_local_block_time:
                    latest_local_block_time = local_block_time

                trade_sell = dex_trade['Trade']['Sell']
                trade_buy = dex_trade['Trade']['Buy']

                trade_sell_mint_address = trade_sell['Currency']['MintAddress']
                trade_buy_mint_address = trade_buy['Currency']['MintAddress']

                for mint_address in [
                        trade_sell_mint_address, trade_buy_mint_address
                ]:
                    if mint_address not in graph_data['nodes']:
                        token_details = token_details_dict.get(
                            mint_address, {})

                        if not token_details:
                            continue

                        token_website_detail = token_details.get(
                            'info', {}).get('websites', [])
                        if token_website_detail:
                            token_website = token_website_detail[0].get(
                                'url', '')
                        else:
                            token_website = ''

                        token_telegram = ''
                        token_twitter = ''
                        token_socials_detail = token_details.get(
                            'info', {}).get('socials', [])
                        for token_social in token_socials_detail:
                            if token_social['type'] == 'telegram':
                                token_telegram = token_social.get('url', '')
                            elif token_social['type'] == 'twitter':
                                token_twitter = token_social.get('url', '')

                        graph_data['nodes'][mint_address] = {
                            'mint_address': mint_address,
                            'name': token_details.get('name', ''),
                            'symbol': token_details.get('symbol', ''),
                            'volume': token_details.get('volume', {}),
                            'price_change':
                            token_details.get('priceChange', {}),
                            'liquidity': token_details.get('liquidity', {}),
                            'fdv': token_details.get('fdv', 0),
                            'website': token_website,
                            'telegram': token_telegram,
                            'twitter': token_twitter
                        }

                if trade_sell_mint_address not in graph_data[
                        'nodes'] or trade_buy_mint_address not in graph_data[
                            'nodes']:
                    continue

                trade_sell_amount_in_usd = trade_sell['AmountInUSD']
                if trade_sell_amount_in_usd == '0' or not can_be_float(
                        trade_sell_amount_in_usd):
                    trade_buy_amount_in_usd = trade_buy['AmountInUSD']
                    if trade_buy_amount_in_usd == '0' or not can_be_float(
                            trade_buy_amount_in_usd):
                        trade_sell_amount = trade_sell['Amount']
                        trade_sell_price_in_usd = trade_sell['PriceInUSD']
                        if trade_sell_amount == '0' or not can_be_float(
                                trade_sell_amount
                        ) or trade_sell_price_in_usd == 0:
                            trade_buy_amount = trade_buy['Amount']
                            trade_buy_price_in_usd = trade_buy['PriceInUSD']
                            if trade_buy_amount == '0' or not can_be_float(
                                    trade_buy_amount
                            ) or trade_buy_price_in_usd == 0:
                                trade_amount_in_usd = 0
                            else:
                                trade_amount_in_usd = float(
                                    trade_buy_amount) * trade_buy_price_in_usd
                        else:
                            trade_amount_in_usd = float(
                                trade_sell_amount) * trade_sell_price_in_usd
                    else:
                        trade_amount_in_usd = float(trade_buy_amount_in_usd)
                else:
                    trade_amount_in_usd = float(trade_sell_amount_in_usd)

                edge_key_main = trade_sell_mint_address + '-' + trade_buy_mint_address
                edge_key_reverse = trade_buy_mint_address + '-' + trade_sell_mint_address

                if edge_key_main not in graph_data[
                        'edges'] and edge_key_reverse not in graph_data[
                            'edges']:
                    graph_data['edges'][edge_key_main] = trade_amount_in_usd
                else:
                    if edge_key_main in graph_data['edges']:
                        graph_data['edges'][
                            edge_key_main] += trade_amount_in_usd
                    else:
                        graph_data['edges'][
                            edge_key_reverse] -= trade_amount_in_usd

            graph_data['transaction_window'] = {
                'earliest_local_block_time':
                earliest_local_block_time.strftime('%Y-%m-%d %H:%M:%S %Z'),
                'latest_local_block_time':
                latest_local_block_time.strftime('%Y-%m-%d %H:%M:%S %Z')
            }

            saved_graph_data_file_path = f"{saved_data_folder_file_path}/graph_data_{current_datetime}.json"

            save_json_file(saved_graph_data_file_path, graph_data)

        else:
            print('\nNo DEX Trades data retrieved.')

    else:
        print("\nMode: {}".format(mode))
        print("File Path to the Saved Graph Data: {}".format(file_path))
        print("No. of days ago to query the data from: {}".format(since_days))
        print("Minimum Volume Threshold in USD: {}".format(volume_threshold))

        if file_path in ['', None]:
            print(
                "\nPlease provide the file path to load the graph data data in PLOT mode.\n"
            )
            sys.exit(1)

        graph_data = load_json_file(file_path)

    if filter_type == 'NAME':
        plot_filter_name_list = plot_filter_names.strip().replace(
            ' ', '').split(',')
        plot_filter_name_upper_list = [
            s.upper() for s in plot_filter_name_list
        ]
        node_data = graph_data['nodes']
        plot_filtered_addresses = [
            mint_address for mint_address in node_data
            if node_data[mint_address]['name'].upper() in
            plot_filter_name_upper_list
        ]
        is_filtered = 'YES'

    elif filter_type == 'SYMBOL':
        plot_filter_symbol_list = plot_filter_symbols.strip().replace(
            ' ', '').split(',')
        plot_filter_symbol_upper_list = [
            s.replace('$', '').upper() for s in plot_filter_symbol_list
        ]
        node_data = graph_data['nodes']
        plot_filtered_addresses = [
            mint_address for mint_address in node_data
            if node_data[mint_address]['symbol'].replace('$', '').upper() in
            plot_filter_symbol_upper_list
        ]
        is_filtered = 'YES'

    else:
        plot_filtered_addresses = []

        if volume_threshold > 0:
            is_filtered = 'YES'
        else:
            is_filtered = 'NO'

    plot_nodes_edges_graph(graph_data, plot_filtered_addresses,
                           volume_threshold, is_filtered)

    print('\nTotal time taken: {:.2f} seconds'.format(time.time() -
                                                      start_time))

# Nodes and Edges Data Structure

# graph = {
#     'nodes': {
#         'A': {'name': 'Node A', 'index': 1, 'website': 'www.google.com'},
#         'B': {'name': 'Node B', 'index': 2, 'website': 'www.youtube.com'},
#         'C': {'name': 'Node C', 'index': 3, 'website': 'www.bbclan.com'},
#         'D': {'name': 'Node D', 'index': 4, 'website': 'wwww.netflix.com'},
#     },
#     'edges': {
#         'A-B': 5,
#         'A-C': 3,
#         'B-A': 4,
#         'C-D': 8
#     }
# }
