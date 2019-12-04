global TRADIER_KEY
TRADIER_KEY = '(INSERT API KEY HERE)'

import requests, json, itertools, collections
import urllib.request
import pandas as pd
import time, schedule
from datetime import datetime, timedelta

import tradier_sym_price as tp

## Saves the previous day's options data
def start(symbols,datadate):
    global getdata_errors,errors,sym_options,all_options

    sym_options,getdata_errors,errors = [],[],[]
    for sym in symbols:
        print(sym)
        exp_dates = getData('v1/markets/options/expirations?symbol='+sym)
        if exp_dates == None:
            print('Error: no expiration dates ('+sym+')')
            errors.append(sym)
            continue
        if exp_dates['expirations'] == None:
            print('Error: no expiration dates ('+sym+')')
            errors.append(sym)
            continue
        exp_df = []
        if type(exp_dates['expirations']['date']) == str:
            exp_dates = [exp_dates['expirations']['date']]
        else:
            exp_dates = exp_dates['expirations']['date']

        for exp in exp_dates:
            try:
                optionChains = getData('/v1/markets/options/chains?symbol='+sym+'&expiration='+exp)
                if optionChains['options'] == None:
                    print("Error: Options Chain unavailable")
                    continue
            except:
                print(sym+' ('+exp+'): getData error')
                getdata_errors.append(sym)
                continue
            call_options,put_options = {},{}
            for option in optionChains['options']['option']:
                if option['option_type'] == 'call':
                    call_options[option['strike']] = [
                                                        option['symbol'],'call',
                                                        option['expiration_date'],
                                                        option['strike'],
                                                        option['last'],option['bid'],option['ask'],
                                                        option['volume'],
                                                        option['open_interest']
                                                     ]
                else:
                    put_options[option['strike']] = [
                                                        option['symbol'],'put',
                                                        option['expiration_date'],
                                                        option['strike'],
                                                        option['last'],option['bid'],option['ask'],
                                                        option['volume'],
                                                        option['open_interest']
                                                     ]
            call_strikes = dict(collections.OrderedDict(sorted(call_options.items())))
            call_options = [call_options[strike] for strike in call_strikes]
            put_strikes = dict(collections.OrderedDict(sorted(put_options.items())))
            put_options = [put_options[strike] for strike in put_strikes]
            options =  [x for x in itertools.chain.from_iterable(itertools.zip_longest(call_options,put_options)) if x]

            columns = ['OptionRoot','Type','Expiration','Strike','Last','Bid','Ask','Volume','OpenInterest']
            exp_df.append(pd.DataFrame(options,columns = columns))

        try:
            df = pd.concat(exp_df)
            df['UnderlyingSymbol'],df['UnderlyingPrice'],df['DataDate'] = sym, None, datadate
            columns = ['UnderlyingSymbol','UnderlyingPrice','OptionRoot','Type','Expiration','DataDate','Strike','Last','Bid','Ask','Volume','OpenInterest']
            df = df[columns]
            sym_options.append(df)

        except:
            pass

    all_options = pd.concat(sym_options)
    all_options = tp.access_prices(all_options, TRADIER_KEY) ## get symbol prices from tradier
    all_options.to_csv(datadate.replace('/','')+'_first.csv',index=False)

def getPrice(symbol):
    ## Get symbol price
    try:
        original = urllib.request.urlopen('https://api.iextrading.com/1.0/stock/'+symbol+'/price')
    except:
        print(symbol+' getPrice error')
        return None
    data = json.load(original)
    return str(data)

def getData(request):
    source = 'https://sandbox.tradier.com/'
    headers = {
        'Accept': "application/json",
        'Authorization': "Bearer "+TRADIER_KEY}

    try:
        init_res = requests.get(source+request, headers=headers, timeout=5)
    except:
        print('Error when requesting Tradier Data ('+request+')')
        time.sleep(5)
        getData(request)
    try:
        return json.loads(init_res.text)
    except:
        print('Error when requesting Tradier Data ('+request+')')
        return getData(request)

global symbols
file = open('symbols.txt', 'r')
symbols = [line[:-1] for line in file.readlines()]

## Use timedelta(1) if setting up after 12:00am

schedule.every().day.at("05:01").do(start,symbols,(datetime.now() - timedelta(1)).strftime('%m/%d/%Y'))

while True:
    schedule.run_pending()
    time.sleep(10) # wait 10 seconds
