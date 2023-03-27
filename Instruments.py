from flask import Flask, jsonify, request
import requests
import yfinance as yf;
import pandas as pd;
from pymongo import MongoClient;
from datetime import datetime, date

app = Flask(__name__)
  
@app.route('/spotPrice/<string:symbol>', methods=['GET'])
def getSpotPrice(symbol):
    sym =  yf.Ticker(symbol);
    price = sym.fast_info.last_price;
    print(sym,price);
    return jsonify({'marketPrice': price})
  
@app.route("/load" , methods=['POST'])
def loadOptions():
    url = "mongodb://21af924e8e2c.mylabserver.com:8080/?connect=false";
    client = MongoClient(url);
    db = client["TradeData"];
    collection = db["Options"];
    db.Options.delete_many({});
        
    symlist = ['AAPL','AMZN','TSLA','MSFT','CSCO','META','V','PG','BAC','GOOGL'];
    options = pd.DataFrame();

    for symbol in symlist:
        tk = yf.Ticker(symbol);
        exps = tk.options[2:6];
                       
        for e in exps:
            print(symbol,e)
            opt = tk.option_chain(e)
            p = tk.fast_info.last_price;
            opt = pd.DataFrame().append(opt.calls)
            opt['expirationDate'] = e
            opt['spotPrice'] = p
            opt.drop(columns=['change','volume','openInterest','lastTradeDate','bid','ask','inTheMoney','percentChange','currency','contractSize'],axis=1,inplace=True);
            opt.rename(columns = {'impliedVolatility':'volatility'}, inplace = True)
            opt.rename(columns = {'strike':'strikePrice'}, inplace = True)
            opt['ticker'] = symbol
            options = options.append(opt, ignore_index=True);
        
    options.fillna(value = 0,inplace = True)
    options.reset_index(inplace=True)
    data_dict = options.to_dict("records")
    collection.insert_many(data_dict);
    count = collection.estimated_document_count();
    return jsonify({'Options Loaded': count})
        

@app.route('/getOption', methods=['GET'])
def getInstrumentDetails():
    symbol = request.args.get('ticker', None)
    optSymbol = request.args.get('contractSymbol', None)
    inst = yf.Ticker(symbol)
    price = inst.fast_info.last_price;
    
    expiry = optSymbol[-15:-9];
    expiry = date(2000+int(expiry[0:2]),int(expiry[2:4]),int(expiry[4:6])).strftime(('%Y-%m-%d'))
    opt = inst.option_chain(expiry).calls
    opt['expirationDate'] = expiry
    opt['spotPrice'] = price
    opt.drop(columns=['change','volume','openInterest','lastTradeDate','bid','ask','inTheMoney','percentChange','currency','contractSize'],axis=1,inplace=True);
    opt.rename(columns = {'impliedVolatility':'volatility'}, inplace = True)
    opt.rename(columns = {'strike':'strikePrice'}, inplace = True)
    opt['ticker'] = symbol
    query = "contractSymbol == '{}'".format(optSymbol)
    x = opt.query(query).to_dict("records")
  
    return jsonify(x)
  
# driver function
if __name__ == '__main__':  
    app.run(debug = True,host='0.0.0.0',port=5000)
