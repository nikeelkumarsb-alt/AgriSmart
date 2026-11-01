from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3, os, requests
from datetime import datetime

app=Flask(__name__)
CORS(app)
DB=os.environ.get("DATABASE_PATH", "/tmp/agrismart.db")
CROPS=[
{"id":"rice","name":"Rice","scientific":"Oryza sativa","names":["Paddy","ಅಕ್ಕಿ","ಭತ್ತ","धान"],"soil":["clay","loamy","alluvial"],"ph":[5.5,7.0],"rain":[1000,2500],"water":"high","seasons":["kharif"]},
{"id":"ragi","name":"Finger millet","scientific":"Eleusine coracana","names":["Ragi","ರಾಗಿ","मंडुआ","ರಾಗಿ ಬೆಳೆ"],"soil":["red","loamy","sandy"],"ph":[5,7.5],"rain":[500,1000],"water":"low","seasons":["kharif","rabi"]},
{"id":"maize","name":"Maize","scientific":"Zea mays","names":["Corn","ಮೆಕ್ಕೆಜೋಳ","मक्का"],"soil":["loamy","alluvial","black"],"ph":[5.5,7.5],"rain":[500,1200],"water":"medium","seasons":["kharif","rabi"]},
{"id":"groundnut","name":"Groundnut","scientific":"Arachis hypogaea","names":["Peanut","ಶೇಂಗಾ","ಮೂಂಗಫಲಿ","मूंगफली"],"soil":["sandy","red","loamy"],"ph":[6,7.5],"rain":[500,1000],"water":"low","seasons":["kharif","rabi"]},
{"id":"sorghum","name":"Sorghum","scientific":"Sorghum bicolor","names":["Jowar","ಜೋಳ","ज्वार"],"soil":["black","red","loamy"],"ph":[5.5,8],"rain":[400,900],"water":"low","seasons":["kharif","rabi"]},
{"id":"cotton","name":"Cotton","scientific":"Gossypium hirsutum","names":["ಹತ್ತಿ","कपास"],"soil":["black","loamy"],"ph":[5.8,8],"rain":[500,1200],"water":"medium","seasons":["kharif"]},
{"id":"tomato","name":"Tomato","scientific":"Solanum lycopersicum","names":["ಟೊಮೇಟೊ","टमाटर"],"soil":["loamy","sandy","red"],"ph":[5.5,7],"rain":[400,800],"water":"medium","seasons":["kharif","rabi","summer"]},
{"id":"chickpea","name":"Chickpea","scientific":"Cicer arietinum","names":["Bengal gram","ಕಡಲೆ","चना"],"soil":["black","loamy","alluvial"],"ph":[6,8],"rain":[300,700],"water":"low","seasons":["rabi"]}]

def conn():
 c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def init():
 with conn() as c:
  c.execute("CREATE TABLE IF NOT EXISTS farms(id INTEGER PRIMARY KEY, farmer TEXT NOT NULL, location TEXT, soil_type TEXT, area REAL, crop TEXT, created_at TEXT)")
def num(x):
 try:return float(x)
 except:return None
init()

@app.get("/api/health")
def health(): return jsonify(status="ok",service="AgriSmart API")
@app.get("/api/crops")
def crops():
 q=request.args.get("q","").lower().strip()
 return jsonify([c for c in CROPS if not q or q in c["name"].lower() or q in c["scientific"].lower() or any(q in n.lower() for n in c["names"])])
@app.post("/api/recommend")
def recommend():
 d=request.get_json(silent=True) or {}; soil=d.get("soil_type","").lower(); season=d.get("season","").lower(); water=d.get("water","").lower(); ph=num(d.get("ph")); rain=num(d.get("rainfall"))
 if not soil or not season or not water or ph is None or rain is None:return jsonify(error="Enter soil type, pH, rainfall, season and water availability."),400
 out=[]
 for c in CROPS:
  score=25 if soil in c["soil"] else 0
  score+=20 if c["ph"][0]<=ph<=c["ph"][1] else 0
  score+=20 if c["rain"][0]<=rain<=c["rain"][1] else (8 if abs(rain-sum(c["rain"])/2)<350 else 0)
  score+=20 if season in c["seasons"] else 0
  score+=15 if water==c["water"] else (7 if water=="medium" or c["water"]=="medium" else 0)
  out.append({**c,"score":score,"reasons":["Soil and climate matching is indicative","Check local variety and irrigation guidance"]})
 out.sort(key=lambda x:x["score"],reverse=True)
 return jsonify(results=out[:5],disclaimer="Indicative rule-based shortlist only. Confirm with local KVK/State Agricultural University before planting.")
@app.post("/api/soil-analysis")
def soil():
 d=request.get_json(silent=True) or {}; crop=next((c for c in CROPS if c["id"]==d.get("crop_id")),None)
 if not crop:return jsonify(error="Select a crop."),400
 v={k:num(d.get(k)) for k in ("n","p","k","ph")}
 if any(x is None for x in v.values()):return jsonify(error="Enter N, P, K and pH readings from a soil test."),400
 obs=[]
 for k,label in (("n","Nitrogen"),("p","Phosphorus"),("k","Potassium")):
  level="low" if v[k]<20 else "moderate" if v[k]<50 else "higher"
  obs.append(dict(name=label,level=level,message="Basic screening only; check lab units and interpretation."))
 return jsonify(crop=crop["name"],observations=obs,ph=dict(value=v["ph"],message="Within indicative crop pH range." if crop["ph"][0]<=v["ph"]<=crop["ph"][1] else "Outside indicative crop pH range."),guidance="Do not apply fertilizer from this screening. Follow the soil laboratory report and current local SAU/ICAR package of practices.")
@app.get("/api/weather")
def weather():
 lat=num(request.args.get("lat")); lon=num(request.args.get("lon"))
 if lat is None or lon is None:return jsonify(error="Enter latitude and longitude."),400
 try:
  r=requests.get("https://api.open-meteo.com/v1/forecast",params={"latitude":lat,"longitude":lon,"current":"temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m","daily":"precipitation_sum,temperature_2m_max,temperature_2m_min","timezone":"auto"},timeout=10); r.raise_for_status(); return jsonify(r.json())
 except requests.RequestException:return jsonify(error="Weather service temporarily unavailable."),503
@app.get("/api/farms")
def farms():
 with conn() as c: rows=c.execute("SELECT * FROM farms ORDER BY id DESC").fetchall()
 return jsonify([dict(x) for x in rows])
@app.post("/api/farms")
def add_farm():
 d=request.get_json(silent=True) or {}; name=str(d.get("farmer","")).strip()
 if not name:return jsonify(error="Farmer name is required."),400
 with conn() as c: cur=c.execute("INSERT INTO farms(farmer,location,soil_type,area,crop,created_at) VALUES(?,?,?,?,?,?)",(name,d.get("location",""),d.get("soil_type",""),num(d.get("area")),d.get("crop",""),datetime.now().isoformat(timespec="minutes")))
 return jsonify(id=cur.lastrowid,message="Farm profile saved."),201
@app.delete("/api/farms/<int:fid>")
def delete_farm(fid):
 with conn() as c: cur=c.execute("DELETE FROM farms WHERE id=?",(fid,))
 return (jsonify(message="Deleted"),200) if cur.rowcount else (jsonify(error="Not found"),404)
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)))
