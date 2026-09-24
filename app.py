import time
import threading
import requests
from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient

app = Flask(__name__)
CORS(app)

# നിങ്ങളുടെ യഥാർത്ഥ യൂസർനെയിമും പാസ്‌വേഡും ഉൾപ്പെടുത്തിയ പൂർണ്ണമായ ലിങ്ക്
MONGO_URI = "mongodb+srv://kking25307_db_user:g5XMQBtl41GlsI4c@cluster0.mwdpp9i.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

try:
    client = MongoClient(MONGO_URI)
    db = client['jonwick_db']
    logs_collection = db['prediction_logs']
    print("MongoDB Connected Successfully!")
except Exception as e:
    print("MongoDB Connection Error:", e)

# സിസ്റ്റം സ്റ്റാറ്റസ്
system_state = {
    "status": "24/7 ENGINE RUNNING",
    "last_sync": "",
    "current_period": "",
    "next_prediction": "WAIT",
    "strategy_used": ""
}

# --- 4 CORE STRATEGIES (Python Version) ---
def logic_trend(history):
    if len(history) < 5: return "big"
    big_count = sum(1 for x in history[:5] if int(x.get('number', 0)) >= 5)
    return "big" if big_count >= 3 else "small"

def logic_reverse(history):
    return "small" if logic_trend(history) == "big" else "big"

def get_best_prediction(history):
    # സിമ്പിൾ AI ഇവാല്യൂഷൻ
    trend_pred = logic_trend(history)
    reverse_pred = logic_reverse(history)
    
    # തൽക്കാലം ലളിതമായ സ്വിച്ചിംഗ് ലോജിക്
    best_type = trend_pred
    strategy = "TREND FOLLOWER"
    return best_type, strategy

# --- BACKGROUND BOT ---
def run_autobot():
    previous_period = ""
    while True:
        try:
            # WinGo 30S ഡാറ്റ എടുക്കുന്നു
            url = "https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?page=1&size=20"
            res = requests.get(url, timeout=5)
            data = res.json()
            history = data.get('data', {}).get('list', [])
            
            if history:
                latest = history[0]
                current_period = str(latest.get('issueNumber', ''))
                
                # പുതിയ പിരീഡ് വന്നാൽ മാത്രം പ്രവർത്തിക്കും
                if previous_period != current_period and current_period != "":
                    actual_num = int(latest.get('number', 0))
                    actual_type = "big" if actual_num >= 5 else "small"
                    
                    # ഡാറ്റാബേസിലേക്ക് സേവ് ചെയ്യുന്നു
                    log_entry = {
                        "period": current_period,
                        "actual_result": actual_type,
                        "actual_number": actual_num,
                        "timestamp": time.time()
                    }
                    logs_collection.insert_one(log_entry)
                    
                    # അടുത്ത പിരീഡിലേക്കുള്ള പ്രെഡിക്ഷൻ കണ്ടെത്തുന്നു
                    next_pred, strat = get_best_prediction(history)
                    
                    system_state['current_period'] = current_period
                    system_state['next_prediction'] = next_pred.upper()
                    system_state['strategy_used'] = strat
                    system_state['last_sync'] = time.strftime('%Y-%m-%d %H:%M:%S')
                    
                    print(f"SUCCESS: Period {current_period} Saved! Next Pred: {next_pred.upper()}")
                    previous_period = current_period
                    
        except Exception as e:
            print("Auto-bot API Error:", e)
            
        time.sleep(5) # ഓരോ 5 സെക്കൻഡിലും ചെക്ക് ചെയ്യും

# സെർവർ ഓൺ ആകുമ്പോൾ തന്നെ ബോട്ട് ബാക്ക്ഗ്രൗണ്ടിൽ വർക്ക് ചെയ്യാൻ തുടങ്ങും
bot_thread = threading.Thread(target=run_autobot)
bot_thread.daemon = True
bot_thread.start()

# വെബ്സൈറ്റ് വഴിയോ ആപ്പ് വഴിയോ ഡാറ്റ ചോദിച്ചാൽ നൽകാനുള്ള റൂട്ട്
@app.route('/')
def home():
    return jsonify({
        "engine": "JONWICK2 PRO",
        "message": "24/7 AI BOT IS ACTIVE",
        "live_data": system_state
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
