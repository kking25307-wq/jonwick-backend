import time
import threading
from curl_cffi import requests
from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

MONGO_URI = "mongodb+srv://kking25307_db_user:g5XMQBtl41GlsI4c@cluster0.mwdpp9i.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    client = MongoClient(MONGO_URI)
    db = client['jonwick_db']
    logs_collection = db['prediction_logs']
    print("MongoDB Connected Successfully!")
except Exception as e:
    print("MongoDB Connection Error:", e)

system_state = {
    "status": "24/7 ENGINE RUNNING",
    "last_sync": "",
    "current_period": "",
    "next_prediction": "WAIT",
    "strategy_used": ""
}

def logic_trend(history):
    if len(history) < 5: return "BIG"
    big_count = sum(1 for x in history[:5] if int(x.get('number', 0)) >= 5)
    return "BIG" if big_count >= 3 else "SMALL"

def logic_reverse(history):
    return "SMALL" if logic_trend(history) == "BIG" else "BIG"

def get_best_prediction(history):
    trend_pred = logic_trend(history)
    strategy = "TREND FOLLOWER"
    return trend_pred, strategy

def run_autobot():
    previous_period = ""
    
    headers = {
        "Accept": "application/json, text/plain, */*",
        "Origin": "https://draw.ar-lottery01.com",
        "Referer": "https://draw.ar-lottery01.com/"
    }
    
    while True:
        try:
            url = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?page=1&size=20"
            
            # ഇവിടെ impersonate="chrome120" എന്ന് നൽകിയാൽ വിൻഗോ വിചാരിക്കുന്നത് ഇതൊരു യഥാർത്ഥ കമ്പ്യൂട്ടറിലെ ക്രോം ബ്രൗസർ ആണെന്നാണ്!
            res = requests.get(url, headers=headers, impersonate="chrome120", timeout=15)
            data = res.json()
            history = data.get('data', {}).get('list', [])
            
            if history:
                latest = history[0]
                current_period = str(latest.get('issueNumber', ''))
                
                if previous_period != current_period and current_period != "":
                    actual_num = int(latest.get('number', 0))
                    actual_type = "BIG" if actual_num >= 5 else "SMALL"
                    
                    log_entry = {
                        "period": current_period,
                        "actual_result": actual_type,
                        "actual_number": actual_num,
                        "timestamp": time.time()
                    }
                    logs_collection.insert_one(log_entry)
                    
                    next_pred, strat = get_best_prediction(history)
                    
                    system_state['current_period'] = current_period
                    system_state['next_prediction'] = next_pred
                    system_state['strategy_used'] = strat
                    system_state['last_sync'] = time.strftime('%Y-%m-%d %H:%M:%S')
                    
                    print(f"SUCCESS: Period {current_period} Saved! Next Pred: {next_pred}")
                    previous_period = current_period
                    
        except Exception as e:
            print("Auto-bot API Error:", e)
            
        time.sleep(5)

bot_thread = threading.Thread(target=run_autobot)
bot_thread.daemon = True
bot_thread.start()

@app.route('/')
def home():
    return jsonify({
        "engine": "JONWICK2 PRO",
        "message": "24/7 AI BOT IS ACTIVE",
        "live_data": system_state
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
