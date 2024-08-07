import os
from configparser import ConfigParser

root_dir = os.path.abspath(os.path.dirname(__file__))
config_file = os.path.join(root_dir, "private.ini")
cfg = ConfigParser()
cfg.read(config_file)

bitquery = dict(cfg.items('bitquery'))
BITQUERY_CLIENT_ID = bitquery.get('bitquery_client_id', '')
BITQUERY_CLIENT_SECRET = bitquery.get('bitquery_client_secret', '')
BITQUERY_V1_API_KEY = bitquery.get('bitquery_v1_api_key', '')

vybe_network = dict(cfg.items('vybe_network'))
VYBE_NETWORK_X_API_KEY = vybe_network.get('vybe_network_x_api_key', '')

birdeye = dict(cfg.items('birdeye'))
BIRDEYE_AGENT_ID = birdeye.get('birdeye_agent_id', '')
BIRDEYE_USER_AGENT = birdeye.get('birdeye_user_agent', '')

BITQUERY_API_VERSION = 'EAP'
BITQUERY_API_VERSION_URL_MAP = {
    'v1': 'https://graphql.bitquery.io/',
    'v2': 'https://streaming.bitquery.io/graphql',
    'EAP': 'https://streaming.bitquery.io/eap',
}

EXCLUDED_MINT_ADDRESSES = [
    # 'So11111111111111111111111111111111111111112',  # SOL
    # 'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
    # 'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # USDT
    '27G8MtK7VtTcCHkpASjSDdkWWYfoqT6ggEuKidVJidD4',  # JLP
    'jupSoLaHXQiZZTSfEWMTRRgpnyFm8f6sZdosWBjx93v',  # JupSOL
    'vSoLxydx6akxyMD9XEcPvGYNGq6Nn66oqVb3UkGkei7',  # vSOL
    'J1toso1uCk3RLmjorhTtrVwY9HJ7X8V9yYac6Y7kGCPn',  # JitoSOL
    'bSo13r4TkiE4KumL71LsHTPpL2euBYLFx6h9HP3piy1',  # bSOL
    'mSoLzYCxHdYgdzU16g5QSh3i5K3z3KZK7ytfqcJm7So',  # mSOL
    '3NZ9JMVBmGAqocybic2c7LQCJScmgsAZ6vQqTDzcqmJh',  # WBTC
    '7vfCXTUXx5WJV5JADk17DUJ4ksgau7utNKj4b963voxs',  # WETH
]

MARKED_MINT_ADDRESSES = [
    'So11111111111111111111111111111111111111112',  # SOL
    'EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v',  # USDC
    'Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB',  # USDT
]

variables = {}

VYBE_NETWORK_QUERY_LIMIT = 100
MAX_RETRIES = 10
RETRY_AFTER = 10
MAX_NO_OF_SIGNATURES_PER_BATCH = 10000
EDGE_POINTS_QUANTITY = 100
EDGE_POINTS_OPACITY = 0
