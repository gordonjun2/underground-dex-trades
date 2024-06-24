# **Underground DEX Trades**

### **Overview**
Underground DEX Trades is a program designed to visualize blockchain transactions using a node and edge graph, similar to platforms like [Bubblemaps](https://bubblemaps.io/). Nodes represent token mint addresses, and edges show the net volume flow in USD between these token mint addresses. For instance, if a user buys dogwifhat (WIF) using Popcat (POPCAT) with $100 USD, the graph will display two nodes representing WIF and POPCAT, connected by a directional edge labeled with the transaction amount of $100 USD, pointing from POPCAT to WIF. This allows users to understand net transaction flows between different mint addresses, aiding in trend analysis and discovery of new token addresses. This can serve to provide short-term trading insights. However, the dominance of high-market-cap coins like Solana (SOL), Jupiter (JUP), and Jito (JTO) in blockchain volumes can obscure other types of trading, such as meme coins. Underground DEX Trades aims to filter out these major tokens, focusing instead on a clearer view of alternative transaction flows and reducing noise in analysis.
<br>

### Notes

- This is a personal project of mine and was not created under any entity.
- Please be aware that the results provided by this project might not be 100% accurate due to potential bugs.
- Please do not rely on this software to make financial decisions. NFA.
- The program can only scan DEX trades data from Solana blockchain. I may consider to add support for EVM chains, such as Ethereum and Base.
- [Bitquery Early Access Program (EAP)](https://docs.bitquery.io/docs/graphql/dataset/EAP/) is used to query Solana DEX trades data in this project. As this API version is considered new, future updates on this API may break the program. 
    - EAP is currently limited to real-time information and does not include historical data. Hence, the amount of DEX trades data retrieved from the API is limited. Due to this, any insight produced from this program is only short-term.
- Please let me know if there are any errors or ways the code may be improved.
<br>

### How It Works

<img src="images/underground_dex_trades_flowchart.png" width="1431" height="971">

- The image above shows the flow of the program.
- The program starts by generating the Bitquery's access token required for the queries.
- There are various checkpoints created as the program runs, and the user can choose which checkpoint to start from based on the mode selection shown below.

#### Checkpoint 1 
- Mode: **Breadth-First Search (BFS)**
    - If BFS mode is selected, the user must provide a starting token mint address first.
    - The BFS algorithm starts with the root node, which is the first token mint address, and queries any DEX trade containing this address. 
    - It records new token mint addresses that trade against the root and their corresponding transaction signatures, making these new addresses the children nodes. 
    - The algorithm then queries each of these children nodes to retrieve more new token mint addresses and accumulate more transaction signatures. 
    - As the algorithm runs, all token mint addresses and the transaction signatures will be saved.
    - This process continues until the specified tree depth is reached, such as stopping at the grandchildren nodes if the depth is set to 2.
    - The program will reach Checkpoint 1 once the BFS algorithm has completed.

<img src="images/depth_and_breadth_first_search.jpeg" width="600" height="400">

- Mode: **Input (INPUT)**
    - If the INPUT mode is selected, the user must provide a list of token mint addresses.
    - While it is up to the user to gather the token list, the repository provides two ways the user can get them.
        - Vybe Network API:
            - The user can run the ```query_token_vybe_network.py``` script to retrieve a list of tokens sorted by their market cap in descending order.
        - Raydium API:
            - The user can run the ```query_raydium_pools.py``` script to retrieve a list of tokens found in Raydium pools sorted by selected factor such as 24 hours volume, liquidity, and more.
    - The query will be done on this list of tokens. Unlike the BFS algorithm, this mode does not search more token mint addresses and transaction signatures beyond the first depth.
    - As the process runs, all token mint addresses and the transaction signatures will be saved.
    - The query process will end after all tokens in the list are queried.
    - The program will reach Checkpoint 1 once the process has completed.

#### Checkpoint 2

- If **LOAD_SIGNATURES** mode is selected, the program will skip to this point. The user must provide a list of unique transaction signatures. Else, the program will arrive at this checkpoint after finishing Checkpoint 1.
- The next step of the program involves querying the recorded transaction signatures and processing them.
- The transaction signatures will be queried in batches. A single transaction signature may contain multiple pool swaps, hence multiple data may be returned after querying a single transaction signature. After ordering the swaps, the actual intent of the transaction can be deduced using the sell side token of the first swap and the buy side token of the last swap.
- Two filters will take place here:
    - MEV
        - If the sell side token of the first swap equals to the buy side token of the last swap (eg. 1 SOL --> 1.0019 SOL), the trade will be ignored.
        - This is to prevent self-loop in the node-and-edge graph and any form of volume bias.
    - Excluded tokens
        - If the sell side token of the first swap or the buy side token of the last swap is found in the list of excluded tokens, the trade will be ignored.
        - This part helps to prevent high-market-cap coins from dominating the volume flow.
        - Users can configure it in ```config.py```.
- The filtered trade data and the filtered token mint addresses will be saved.
- The program will reach Checkpoint 2 once the DEX trades data are processed.

#### Checkpoint 3

- If **LOAD_TRADES** mode is selected, the program will skip to this point. The user must provide a list of DEX trades data and a list of token mint addresses. Else, the program will arrive at this checkpoint after finishing Checkpoint 2.
- At this point, the program will rely on Dexscreener API to retrieve token details, such as name, symbol, volume, FDV, socials, of the remaining tokens.
- The program will start to create the node-and-edge data.
    - Node Information:
        - Contains all token mint addresses and their respective token details
    - Edge Information:
        - Contains unique pair of token mint addresses representing swaps discovered between them and the net volume flow in a single direction
        - Eg. If the pair is named '25hAyBQfoDhfWx9ay6rarbgvWGwDdNqcHsXS3jQ3mTDJ-2Dyzu65QA9zdX1UeE7Gx71k7fiwyUK6sZdrvJ7auq5wm' and the net volume is 37 USD, this means that a net 37 USD flows from the token '25hAyBQfoDhfWx9ay6rarbgvWGwDdNqcHsXS3jQ3mTDJ' to the token '2Dyzu65QA9zdX1UeE7Gx71k7fiwyUK6sZdrvJ7auq5wm'. No '2Dyzu65QA9zdX1UeE7Gx71k7fiwyUK6sZdrvJ7auq5wm-25hAyBQfoDhfWx9ay6rarbgvWGwDdNqcHsXS3jQ3mTDJ' should be found as the pair already existed. Using the same example but in another perspective, '2Dyzu65QA9zdX1UeE7Gx71k7fiwyUK6sZdrvJ7auq5wm-25hAyBQfoDhfWx9ay6rarbgvWGwDdNqcHsXS3jQ3mTDJ' simply means a net 37 USD flow from the token '25hAyBQfoDhfWx9ay6rarbgvWGwDdNqcHsXS3jQ3mTDJ' to the token '2Dyzu65QA9zdX1UeE7Gx71k7fiwyUK6sZdrvJ7auq5wm', which refers to the same thing as before.
- The graph data will be saved.
- The program will reach Checkpoint 3 once the graph data is created.

#### Node-and-Edge Graph Plotting

- If **PLOT** mode is selected, the program will skip to this point. The user must provide the graph data. Else, the program will arrive at this checkpoint after finishing Checkpoint 3.
- The graph data will be processed and displayed in a node-and-edge graph.

<img src="images/unfiltered_node_and_edge_graph.png" width="783" height="400">

- However, the graph can be very messy if no further filtering is done.
- Filtering done in this phase includes:
    - Minimum Volume Threshold
        - User can set a minimum volume threshold to filter higher volume flow edges. This can help to remove noisy data on the graph.
    - Filter Token Names or Symbols
        - User can select specificially which tokens to display on the graph. All token pairs that contains the indicated tokens will be displayed.

<img src="images/filtered_node_and_edge_graph.png" width="783" height="400">

<br>

### **APIs**
1. [Bitquery](https://docs.bitquery.io/docs/intro/)
    - Used to query on-chain DEX trades data
    - **REQUIRED** and **API keys REQUIRED**
2. [Dexscreener](https://docs.dexscreener.com/api/reference)
    - Used to query token-related information such as name, symbol, and fully diluted valuation (FDV)
    - **REQUIRED** and **API keys NOT REQUIRED**
3. [Raydium](https://api-v3.raydium.io/docs/)
    - Used to query a list of tokens based on criteria such as 24hrs volume and liquidity, which can be used starting as mint addresses for the program
    - **OPTIONAL** and **API keys NOT REQUIRED**
4. [Vybe Network](https://docs.vybenetwork.com/docs/overview)
    - Used to query token-related information such as volume and holder count
    - **OPTIONAL** and **API keys REQUIRED**
5. [Birdeye](https://birdeye.so/find-gems?chain=solana)
    - Used to query a list of tokens based on criteria such as 24 hrs volume and 24 hrs trades, which can be used as starting mint addresses for the program
    - **OPTIONAL** and **API keys REQUIRED**
    - **NOT WORKING ALREADY**
<br>

### **Installation**
1. Clone the repository using
    ```
    git clone https://github.com/gordonjun2/underground-dex-trades.git
    ```
2. Navigate to the root directory of the repository.
    ```
    cd underground-dex-trades
    ```
3. Install required packages.
    ```
    pip install -r requirements.txt
    ```
4. Rename private keys file.
    ```
    mv private_template.ini private.ini
    ```
5. Sign up for *Bitquery API* [here](https://bitquery.io/) and get the respective keys in the link below.
    - BITQUERY_CLIENT_ID: https://account.bitquery.io/user/api_v2/applications
    - BITQUERY_CLIENT_SECRET: https://account.bitquery.io/user/api_v2/applications
    - BITQUERY_V1_API_KEY: https://account.bitquery.io/user/api_v1/api_keys
6. Sign up for *Vybe Network API* [here](https://www.vybenetwork.com/) and get the respective keys in the link below.
    - VYBE_NETWORK_X_API_KEY: https://alpha.vybenetwork.com/dashboard/api-management
7. Copy and save the keys into the private keys file.
8. Done!
<br>

### **Configuration**
<br>

### **Usage**
1. Run the command below to start the bot:
    ```
    node main.js -f private.json
    ```
2. Once the bot is ready, look for the Telegram Bot you created in Telegram by searching for its Telegram username (eg. `@<bot's username>`).
3. Click on `/start` to start the tracking.
    <br>
    <img src="images/telegram-bot_start.jpg" width="280" height="380">
    
4. Done! You can leave the bot running in your terminal.
    - To stop the bot, just do a `Ctrl+C`.
    - To keep the bot running without the need to have your computer switched on all the time, consider deploying the repository into a Cloud service (see **Deploy to Cloud** section below).
<br>

### **Usage Tips**
- In the Telegram chat with the bot, type `/help` to get all available commands to use.
    - Currently implemented:
        - `/start`: Re-initialise tracking and list assets being tracked (do not need to use again)
        - `/list`: List assets being tracked
        - `/modify`: Modify assets to be tracked
            - Some assets are already added. You can remove them and add new assets here.
        - `/help`: To list the available commands and their description
- You can set the data retrieving interval in `main.js` under 
    ```
    function begin_bot(){
    teleBot.telegram.sendMessage(chatID, "Tracking starts now...", { parse_mode: 'HTML' });
    console.log(getDateTime() + ' Timer starts');
    scanManager = setInterval(scan, 30 * 1000);                             // check every 30 sec
    checkAliveManager = setInterval(checkAlive, 6 * 60 * 60 * 1000);        // check every 6 hours
    scan();
    }
    ```
    - Change the interval value to your own preference.
    - Please see **Note** section below.
<br>
