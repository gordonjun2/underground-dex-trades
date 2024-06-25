import requests
import os
import sys
import datetime
from urllib3.exceptions import InsecureRequestWarning
import urllib3
import argparse
from utils import save_json_file
from config import EXCLUDED_MINT_ADDRESSES

urllib3.disable_warnings(InsecureRequestWarning)

if __name__ == "__main__":

    # Get arguments from terminal
    parser = argparse.ArgumentParser(
        description="Get parameters for the script.")
    parser.add_argument(
        '-pt',
        '--pool_type',
        type=str,
        default='all',
        help="Pool Type. Available values : all, concentrated, standard.")
    parser.add_argument(
        '-psf',
        '--pool_sort_field',
        type=str,
        default='volume24h',
        help=
        "Pool Field. Available values : default, liquidity, volume24h, fee24h, apr24h, volume7d, fee7d, apr7d, volume30d, fee30d, apr30d."
    )
    parser.add_argument('-st',
                        '--sort_type',
                        type=str,
                        default='desc',
                        help="Sort Type. Available values : desc, asc.")
    parser.add_argument('-ps',
                        '--page_size',
                        type=int,
                        default=50,
                        help="Page Size. Max is 1000. Default is 50.")
    parser.add_argument('-p',
                        '--page',
                        type=int,
                        default=1,
                        help="Page Index. Default is 1.")
    args = parser.parse_args()

    pool_type = str(args.pool_type).lower()
    pool_sort_field = str(args.pool_sort_field).lower()
    sort_type = str(args.sort_type).lower()
    page_size = args.page_size
    page = args.page

    if pool_type not in ['all', 'concentrated', 'standard']:
        print(
            "\nPool Type {} is not supported. Supported modes are all, concentrated, standard.\n"
            .format(pool_type))
        sys.exit(1)

    if pool_sort_field not in [
            'default', 'liquidity', 'volume24h', 'fee24h', 'apr24h',
            'volume7d', 'fee7d', 'apr7d', 'volume30d', 'fee30d', 'apr30d'
    ]:
        print(
            "\nPool Sort Field {} is not supported. Supported modes are default, liquidity, volume24h, fee24h, apr24h, volume7d, fee7d, apr7d, volume30d, fee30d, apr30d.\n"
            .format(pool_sort_field))
        sys.exit(1)

    if sort_type not in ['desc', 'asc']:
        print(
            "\nSort Type {} is not supported. Supported modes are desc, asc.\n"
            .format(sort_type))
        sys.exit(1)

    url = "https://api-v3.raydium.io/pools/info/list?poolType={}&poolSortField={}&sortType={}&pageSize={}&page={}".format(
        pool_type, pool_sort_field, sort_type, page_size, page)

    response = requests.get(url, verify=False)

    if response.status_code == 200:
        print("\nRequest successful!")
        mint_addresses = set()

        try:
            pools_data = response.json().get('data', {}).get('data', [])

            if not isinstance(pools_data, list):
                pools_data = []
        except:
            pools_data = []

        for pool in pools_data:

            mintA = pool.get('mintA', {})
            mintB = pool.get('mintB', {})

            mintA_address = mintA.get('address', '')
            mintB_address = mintB.get('address', '')

            if mintA_address not in EXCLUDED_MINT_ADDRESSES:
                mint_addresses.add(mintA_address)

            if mintB_address not in EXCLUDED_MINT_ADDRESSES:
                mint_addresses.add(mintB_address)

    else:
        raise Exception('Query failed and return code is {}.'.format(
            response.status_code))

    saved_data_folder_file_path = './saved_data'
    if not os.path.exists(saved_data_folder_file_path):
        os.makedirs(saved_data_folder_file_path)

    current_datetime = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"{saved_data_folder_file_path}/raydium_pools_mint_addresses_{current_datetime}.json"

    save_json_file(file_name, list(mint_addresses))
