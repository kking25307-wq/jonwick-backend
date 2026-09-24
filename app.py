import time
import threading
import urllib.parse
import requests as req
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
except Exception as e:
    pass

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

def run_autobot():
    print("Auto-bot background thread started with Proxy Bypass!")
    previous_period = ""
    
    while True:
        try:
            t = int(time.time())
            raw_url = f"https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?page=1&size=20&t={t}"
            
            data = None
            try:
                # Proxy 1: CodeTabs API
                res = req.get(f"https://api.codetabs.com/v1/proxy?quest={raw_url}", timeout=10)
                data = res.json()
            except:
                try:
                    # Proxy 2: AllOrigins Fallback
                    encoded_url = urllib.parse.quote(raw_url, safe='')
                    res = req.get(f"https://api.allorigins.win/raw?url={encoded_url}", timeout=10)
                    data = res.json()
                except:
                    pass
            
            if data:
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
                        try:
                            logs_collection.insert_one(log_entry)
                        except:
                            pass
                        
                        next_pred = logic_trend(history)
                        
                        system_state['current_period'] = current_period
                        system_state['next_prediction'] = next_pred
                        system_state['strategy_used'] = "TREND FOLLOWER"
                        system_state['last_sync'] = time.strftime('%Y-%m-%d %H:%M:%S')
                        
                        print(f"SUCCESS: Period {current_period} Saved! Next Pred: {next_pred}")
                        previous_period = current_period
        except Exception as e:
            pass
            
        time.sleep(3)

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
