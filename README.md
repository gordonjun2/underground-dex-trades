# **Underground DEX Trades**

### **Overview**
Underground DEX Trades is a program designed to visualize blockchain transactions using a node and edge graph, similar to platforms like [Bubblemaps](https://bubblemaps.io/). Nodes represent token mint addresses, and edges show the net volume flow in USD between these token mint addresses. For instance, if a user buys dogwifhat (WIF) using Popcat (POPCAT) with $100 USD, the graph will display two nodes representing WIF and POPCAT, connected by a directional edge labeled with the transaction amount of $100 USD, pointing from POPCAT to WIF. This allows users to understand net transaction flows between different mint addresses, aiding in trend analysis and discovery of new token addresses. This can serve to provide short-term trading insights. However, the dominance of high-market-cap coins like Solana (SOL), Jupiter (JUP), and Jito (JTO) in blockchain volumes can obscure other types of trading, such as meme coins. Underground DEX Trades aims to filter out these major tokens, focusing instead on a clearer view of alternative transaction flows and reducing noise in analysis.
<br>

### Updates

- The program can only scan DEX trades data from Solana blockchain. I may consider to add support for EVM chains, such as Ethereum and Base.

### How It Works

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

### **Note**
- The program uses the [`@staratlas/factory`](https://www.npmjs.com/package/@staratlas/factory) package.
    - [Package documentations](https://staratlasmeta.github.io/factory/modules.html)
- The bot does not make use of the class `GmEventService` in the package `@staratlas/factory`. Thus, it does not react immediately to new events happening in the marketplace (eg. new sell orders). Rather, it uses the `GmClientService` based on a fixed interval set in `main.js`.
    - My intention was to use `GmEventService` as this can probably reduce the frequency of RPC calls, but I am unsure on how to use it. Please hit me up if you know how to do it.
- I am very new to JavaScript. Please let me know if there are any errors or ways the code may be improved.
- I am also new to DevOps / Cloud Engineering. Please let me know if there are any better way to go about the deployment of the program.
