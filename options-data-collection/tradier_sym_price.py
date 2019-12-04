import pandas as pd
import requests,json
import time

def getSymPrice(symbols, KEY):
    source = 'https://sandbox.tradier.com/v1/markets/quotes'
    headers = {
        'Accept': "application/json",
        'Authorization': "Bearer "+KEY}
    

    ## request data
    try:
        init_res = requests.get(source, params={'symbols':symbols}, headers=headers, timeout=15)
    except:
        print('Error when requesting Tradier Symbols Data ('+symbols+')')
        time.sleep(5)
        getSymPrice(symbols, KEY)

    ## process data
    try:
        orig = json.loads(init_res.text)
        orig = orig['quotes']['quote']
        prices = [sym['last'] for sym in orig]
        return prices
    except:
        print('Processing error ('+symbols+')')
        return getSymPrice(symbols, KEY)

def chunks(l, n): ## break list l into groups of n
    all_parts = []
    for i in range(0, len(l), n):
        all_parts.append(l[i:i + n])
    return all_parts

## ---- MAIN ----
def access_prices(df, KEY):
    global SYMBOL_PRICES, SYMBOL_ERRORS
    global prices,symlist,final_sym
    
    ## get all symbols
    symlist = df['UnderlyingSymbol'].tolist()
    symlist = list(dict.fromkeys(symlist))
    
    ## formatting
    sym_strgroups = []
    sym_listgroups = chunks(symlist, 15)
    for sym_group in sym_listgroups:
        sym_group = str(sym_group)[1:-1]
        sym_group = sym_group.replace("'","")
        sym_group = sym_group.replace(' ','')
        sym_strgroups.append(sym_group)
    
    ## get symbol prices
    print('\ngetting prices')
    SYMBOL_PRICES = {}
    for i in range(len(sym_strgroups)):
        SYMBOL_PRICES.update(dict(zip(sym_listgroups[i],getSymPrice(sym_strgroups[i], KEY))))

    ## input price into df
    SYMBOL_ERRORS = []
    def getprice(sym):
        if sym not in SYMBOL_PRICES:
            SYMBOL_PRICES[sym] = None
            
        price = SYMBOL_PRICES[sym]
        if price == None:
            if sym not in SYMBOL_ERRORS:
                SYMBOL_ERRORS.append(sym)            
                
        return SYMBOL_PRICES[sym]

    df['UnderlyingPrice'] = df['UnderlyingSymbol'].apply(getprice)
    print('Unavailable symbol prices '+str(SYMBOL_ERRORS))

    return df

## MANUAL ACCESS

##global df
##filename = '662019_four.csv'
##
##df = pd.read_csv(filename)
##df = access_prices(df, 'OOQP9hchGXHPvR7JT10d9T0TETp8')
##df.to_csv(filename, index=False)

