from flask import Flask, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import requests
import threading
import time
import os

app = Flask(__name__)
CORS(app)

# നിങ്ങളുടെ MongoDB കണക്ഷൻ ലിങ്ക്
MONGO_URI = "mongodb+srv://kking25307_db_user:g8NzQbliK1GIvl4e@cluster0.mwdpp9i.mongodb.net/?appName=Cluster0"
client = MongoClient(MONGO_URI)
db = client["jonwick_db"]
collection = db["history_30s"]

# 24 മണിക്കൂറും പ്രവർത്തിക്കുന്ന ലൂപ്പ്
def fetch_data_forever():
    while True:
        try:
            url = f"https://draw.ar-lottery01.com/WinGo/WinGo_30S/GetHistoryIssuePage.json?ts={int(time.time()*1000)}&page=1&size=50"
            res = requests.get(url, timeout=10).json()
            data_list = res.get('data', {}).get('list', [])
            
            for item in data_list:
                period = str(item.get('issueNumber', item.get('issue', '')))
                number = int(item.get('number', 0))
                
                # ഡാറ്റാബേസിൽ ഈ പിരീഡ് മുൻപ് സേവ് ചെയ്തിട്ടില്ലെങ്കിൽ മാത്രം സേവ് ചെയ്യുന്നു
                if not collection.find_one({"period": period}):
                    collection.insert_one({
                        "period": period,
                        "number": number,
                        "timestamp": int(time.time())
                    })
                    print(f"Saved to DB: {period} - {number}")
        except Exception as e:
            print("Fetch Error:", e)
        
        time.sleep(10) # ഓരോ 10 സെൻഡിലും പുതിയ റിസൾട്ട് നോക്കും

# ബാക്ക്ഗ്രൗണ്ടിൽ ഡാറ്റ എടുക്കാൻ തുടങ്ങും
threading.Thread(target=fetch_data_forever, daemon=True).start()

@app.route('/api/history', methods=['GET'])
def get_history():
    data = list(collection.find({}, {"_id": 0}).sort("period", -1).limit(100))
    return jsonify({"status": "success", "list": data})

@app.route('/', methods=['GET'])
def home():
    return "JONWICK AI BACKEND SERVER IS RUNNING 24/7!"

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)