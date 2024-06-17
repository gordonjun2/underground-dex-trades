import requests
import time


def get_token_details(mint_addresses,
                      no_of_tokens_per_batch=1,
                      max_retries=5,
                      retry_after=10):

    token_details_dict = {}
    total_mint_addresses = len(mint_addresses)
    count = 1

    for i in range(0, total_mint_addresses, no_of_tokens_per_batch):

        start_number = i + 1

        if i + no_of_tokens_per_batch > total_mint_addresses:
            end_number = total_mint_addresses
        else:
            end_number = i + no_of_tokens_per_batch

        print('\nQuerying token details {} - {} out of {}'.format(
            start_number, end_number, total_mint_addresses))

        mint_addresses_batch = mint_addresses[i:i + no_of_tokens_per_batch]
        mint_addresses_batch_comma_separated = ','.join(mint_addresses_batch)

        url = "https://api.dexscreener.com/latest/dex/tokens/{}".format(
            mint_addresses_batch_comma_separated)

        headers = {
            "accept": "application/json",
        }

        retry_count = 0

        while retry_count < max_retries:

            response = requests.get(url, headers=headers, verify=False)

            if response.status_code == 200:

                token_details = response.json().get('pairs', [])

                for token in token_details:
                    count += 1
                    mint_address = token.get('baseToken',
                                             {}).get('address', '')

                    if not mint_address:
                        continue

                    if mint_address not in token_details_dict:
                        token_details_dict[mint_address] = {
                            'chainId': token.get('chainId', ''),
                            'dexId': token.get('dexId', ''),
                            'volume': token.get('volume', {}),
                            'priceChange': token.get('priceChange', {}),
                            'liquidity': token.get('liquidity', {}),
                            'fdv': token.get('fdv', 0),
                            'info': token.get('info', {}),
                        }

                break

            else:
                retry_count += 1

                print(
                    'Query failed and return code is {}. Retrying ({}) after {} seconds...'
                    .format(response.status_code))

                time.sleep(retry_after)

        if retry_count >= max_retries:
            print('Maximum retries reached. Skipping the rest...')
            break

    return token_details_dict


# get_token_details([
#     'DxtssVdyYe4wWE5f5zEgx2NqtDFbVL3ABGY62WCycHWg',
#     '3J5QaP1zJN9yXE7jr5XJa3Lq2TyGHSHu2wssK7N1Aw4p'
# ])
