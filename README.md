# AgriSmart — Smart Crop Recommendation & Soil Nutrient Management

React + Vite frontend and Flask API prototype.

## Features
- Rule-based crop shortlist using soil type, pH, rainfall, season and water availability.
- Crop-name search with selected regional names.
- Basic NPK/pH screening with guidance to use verified soil-test interpretations.
- Open-Meteo weather lookup.
- Farm profile storage in SQLite (prototype storage; data may reset on ephemeral hosting).

## Local development
Backend: `cd backend && pip install -r requirements.txt && python app.py`
Frontend: `cd frontend && npm install && npm run dev`

## Deployment notes
This is an educational prototype, not a validated agronomy advisory. Confirm crop choices and fertilizer decisions with local agricultural experts and current SAU/ICAR recommendations.