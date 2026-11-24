from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3, os, requests
from datetime import datetime
from market_fertilizers import market_matches

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
 if lat is None or lon is None or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
  return jsonify(error="Valid GPS latitude and longitude are required."),400
 try:
  params={
   "latitude":lat,"longitude":lon,
   # Open-Meteo's current endpoint supports a smaller set than hourly.
   "current":"temperature_2m,relative_humidity_2m,apparent_temperature,is_day,precipitation,rain,showers,weather_code,cloud_cover,pressure_msl,surface_pressure,wind_speed_10m,wind_direction_10m,wind_gusts_10m",
   "hourly":"temperature_2m,precipitation_probability,precipitation,rain,weather_code,visibility,uv_index",
   "daily":"weather_code,temperature_2m_max,temperature_2m_min,apparent_temperature_max,apparent_temperature_min,precipitation_sum,rain_sum,precipitation_probability_max,sunrise,sunset,uv_index_max,et0_fao_evapotranspiration",
   "timezone":"auto","forecast_days":7
  }
  r=requests.get("https://api.open-meteo.com/v1/forecast",params=params,timeout=20)
  r.raise_for_status()
  data=r.json()
  if "current" not in data or "daily" not in data or "hourly" not in data:
   return jsonify(error="Weather provider returned incomplete data. Please retry."),502
  # These are hourly variables, not supported current request variables.
  # Copy the observation for the current timestamp into the current object
  # so the existing UI can render rain chance, UV and visibility consistently.
  hourly=data.get("hourly",{})
  hour_times=hourly.get("time",[])
  current_time=data["current"].get("time")
  hour_index=max((i for i,t in enumerate(hour_times) if current_time and t <= current_time), default=None)
  if hour_index is not None:
   for key in ("precipitation_probability","visibility","uv_index"):
    values=hourly.get(key,[])
    if hour_index < len(values):
     data["current"][key]=values[hour_index]
  code=data["current"].get("weather_code",0)
  labels={0:"Clear sky",1:"Mainly clear",2:"Partly cloudy",3:"Overcast",45:"Fog",48:"Depositing rime fog",51:"Light drizzle",53:"Drizzle",55:"Dense drizzle",61:"Slight rain",63:"Moderate rain",65:"Heavy rain",71:"Slight snowfall",73:"Snowfall",75:"Heavy snowfall",80:"Rain showers",81:"Moderate rain showers",82:"Violent rain showers",95:"Thunderstorm",96:"Thunderstorm with hail",99:"Severe thunderstorm"}
  icons={0:"☀️",1:"🌤️",2:"⛅",3:"☁️",45:"🌫️",48:"🌫️",51:"🌦️",53:"🌦️",55:"🌧️",61:"🌧️",63:"🌧️",65:"🌧️",71:"🌨️",73:"❄️",75:"❄️",80:"🌦️",81:"🌧️",82:"⛈️",95:"⛈️",96:"⛈️",99:"⛈️"}
  data["condition"]={"label":labels.get(code,"Variable conditions"),"icon":icons.get(code,"🌤️")}
  data["location"]={"latitude":lat,"longitude":lon}
  try:
   geo=requests.get("https://nominatim.openstreetmap.org/reverse",params={"lat":lat,"lon":lon,"format":"jsonv2","zoom":10},headers={"User-Agent":"AgriSmart-College-Prototype/1.0 (weather location lookup)"},timeout=5)
   if geo.ok:
    address=geo.json().get("address",{})
    data["location_name"]=", ".join(x for x in [address.get("village") or address.get("town") or address.get("city") or address.get("county"),address.get("state_district") or address.get("state")] if x)
  except requests.RequestException:
   pass
  return jsonify(data)
 except requests.Timeout:
  return jsonify(error="Weather request timed out. Please try again."),504
 except requests.HTTPError:
  return jsonify(error="Weather provider rejected the request. Please retry in a moment."),502
 except (requests.RequestException, ValueError):
  return jsonify(error="Weather service is temporarily unavailable. Check your connection and retry."),503

@app.post("/api/field-recommend")
def field_recommend():
 d=request.get_json(silent=True) or {}
 soil=str(d.get("soil_type","")).lower(); season=str(d.get("season","")).lower(); water=str(d.get("water","")).lower()
 ph=num(d.get("ph")); rain=num(d.get("rainfall")); forecast_rain=num(d.get("forecast_rain_7d")); temp=num(d.get("temperature")); location=str(d.get("location","")).strip()
 if not all([soil,season,water]) or ph is None or rain is None:
  return jsonify(error="Soil type, pH, annual rainfall, season and water availability are required."),400
 out=[]
 for crop in CROPS:
  parts={}
  parts["soil"]=25 if soil in crop["soil"] else 0
  parts["pH"]=20 if crop["ph"][0]<=ph<=crop["ph"][1] else max(0,10-abs(ph-sum(crop["ph"])/2)*5)
  parts["annual_rainfall"]=15 if crop["rain"][0]<=rain<=crop["rain"][1] else max(0,8-abs(rain-sum(crop["rain"])/2)/100)
  parts["season"]=15 if season in crop["seasons"] else 0
  parts["water"]=10 if water==crop["water"] else (5 if water=="medium" or crop["water"]=="medium" else 0)
  raw_score=sum(parts.values())
  score=round(raw_score/85*100)
  notes=[]
  if parts["soil"]==0: notes.append("Soil type is outside this crop's starter dataset preference.")
  if parts["pH"]<20: notes.append("Soil pH needs local verification or amendment planning.")
  if parts["annual_rainfall"]<15: notes.append("Annual rainfall is outside the starter range.")
  if parts["season"]==0: notes.append("Season is not listed in the starter crop calendar.")
  if forecast_rain is not None:
   if forecast_rain>=100: notes.append("Heavy 7-day rain outlook: check drainage and avoid field operations on saturated soil.")
   elif forecast_rain<=5: notes.append("Very low 7-day rain outlook: confirm irrigation availability.")
   else: notes.append("Review the 7-day rainfall outlook before sowing and irrigation.")
  if temp is not None: notes.append("Use local crop-stage temperature thresholds from the regional agricultural package.")
  out.append({**crop,"score":round(score),"score_breakdown":parts,"reasons":notes or ["Core soil, season and water inputs match the starter crop profile."]})
 out.sort(key=lambda x:x["score"],reverse=True)
 context={"location":location or None,"coordinates":{"latitude":num(d.get("latitude")),"longitude":num(d.get("longitude"))} if num(d.get("latitude")) is not None and num(d.get("longitude")) is not None else None,"forecast_rain_7d_mm":forecast_rain,"current_temperature_c":temp,"crop_history":d.get("crop_history") or None}
 return jsonify(results=out[:5],context=context,disclaimer="Location and weather are contextual signals, not a validated district-level crop model. This starter dataset does not replace local crop calendars, soil testing or KVK/SAU advice.")
@app.post("/api/fertilizer-advice")
def fertilizer_advice():
 d=request.get_json(silent=True) or {}
 crop=next((x for x in CROPS if x["id"]==d.get("crop_id")),None)
 stage=str(d.get("stage","")).strip(); symptom=str(d.get("symptom","none")).strip()
 vals={k:num(d.get(k)) for k in ("n","p","k","ph")}
 if not crop or not stage or any(v is None for v in vals.values()):
  return jsonify(error="Select a crop and growth stage, and enter soil-test NPK and pH values."),400
 if any(v<0 for v in vals.values()): return jsonify(error="Soil-test values cannot be negative."),400
 rain=num(d.get("forecast_rain_7d")); irrigation=str(d.get("irrigation","unknown"))
 signals=[]
 if vals["n"]<20: signals.append("N is below the prototype screening threshold; confirm lab units and the soil-test rating.")
 elif vals["n"]>80: signals.append("N is high in this simple screening; avoid adding nitrogen without a local recommendation.")
 if vals["p"]<15: signals.append("P is below the prototype screening threshold; confirm the lab method and units.")
 elif vals["p"]>60: signals.append("P is high in this simple screening; avoid additional phosphorus until reviewed.")
 if vals["k"]<20: signals.append("K is below the prototype screening threshold; confirm the lab method and units.")
 elif vals["k"]>80: signals.append("K is high in this simple screening; avoid adding potassium without a local recommendation.")
 if not crop["ph"][0]<=vals["ph"]<=crop["ph"][1]: signals.append("Measured pH is outside this crop's broad starter range; investigate pH before nutrient correction.")
 symptom_map={"yellow_old":"Yellowing on older leaves can have several causes, including N shortage, waterlogging or root stress; confirm before treatment.","yellow_young":"Yellowing on young leaves can have several causes, including micronutrient or root/pH issues; confirm before treatment.","leaf_edges":"Leaf-edge scorch can be related to K, salinity, heat or water stress; it is not a diagnosis.","purple":"Purple coloration can be linked to P availability, cold roots or varietal traits; confirm before treatment.","spots":"Leaf spots may be disease, pest or abiotic injury; fertilizer alone may not solve it.","wilting":"Wilting can indicate water stress, root damage or vascular disease; check soil moisture and roots first.","none":"No visible symptoms reported."}
 symptom_note=symptom_map.get(symptom,"Symptoms need field inspection; this questionnaire cannot diagnose disease.")
 weather_note="No forecast rainfall supplied; check local forecast before application."
 if rain is not None:
  weather_note=("Rain outlook is high: avoid applying soluble fertilizer immediately before heavy rain because of runoff/leaching risk." if rain>=25 else "Rain outlook is low: confirm soil moisture and irrigation before applying nutrients." if rain<5 else "Check the application label and local forecast; avoid application before heavy rain.")
 options=[
 {"type":"Lab-formulated / soil-test blend","examples":"A locally prepared NPK or micronutrient blend based on a certified soil test and crop-stage recommendation.","pros":["Can target the measured nutrient gap","Can be tailored to crop and soil test","Clear nutrient analysis when supplied by a licensed/verified source"],"cons":["Quality and formulation vary by supplier","Requires reliable lab results and correct units","May cost more than common bulk fertilizers"],"best_when":"A current soil test identifies a specific nutrient requirement and a qualified lab/agronomist specifies the blend."},
 {"type":"Organic","examples":"Mature compost, well-decomposed farmyard manure or vermicompost from a trusted source.","pros":["Adds organic matter and can improve soil structure","Supports biological activity","Can recycle farm residues"],"cons":["Nutrient content is variable and often slower to release","Bulky to transport and apply","Poorly matured material may introduce weed seeds or pathogens"],"best_when":"Building soil organic matter and supporting long-term soil health; nutrient contribution should be tested or conservatively estimated."},
 {"type":"Synthetic / mineral","examples":"Only the crop- and soil-test-appropriate mineral fertilizer grade recommended by local agriculture guidance.","pros":["Known nutrient concentration on a genuine label","Usually faster and more predictable nutrient availability","Lower bulk for transport"],"cons":["Over-application can burn crops or cause nutrient imbalance","Losses can occur through leaching or runoff","Does not replace organic-matter management"],"best_when":"A confirmed nutrient deficiency requires a timely, measured nutrient supply under local package-of-practice guidance."}
 ]
 products, market_note = market_matches(d.get("lab_ratings"))
 return jsonify(market_products=products,market_note=market_note,crop=crop["name"],stage=stage,soil_test=vals,health_observation=symptom_note,screening_signals=signals,weather_guidance=weather_note,irrigation=irrigation,options=options,action_plan=["Confirm the soil-test units, sampling depth and report date with the laboratory.","Inspect the whole plant, roots and field pattern; use a KVK/plant clinic for suspected disease or pest damage.","Choose a nutrient only when a soil test or validated crop-stage recommendation supports it.","Follow the product label and current district/state package of practices for dose, timing, PPE and waiting periods."],safety_note="This is a screening and comparison aid, not a fertilizer prescription or plant-disease diagnosis. No dose is calculated because crop variety, area, soil-test method, target yield and regional recommendations are not yet verified.")
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
