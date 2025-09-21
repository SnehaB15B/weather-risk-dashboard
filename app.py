import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# ------------------- STREAMLIT CONFIG -------------------
st.set_page_config(page_title="🌤️ Outdoor Weather Risk Dashboard", layout="wide")
st.title("🌍 Outdoor Weather Risk & Comfort Dashboard")

# ------------------- ENV KEYS -------------------
load_dotenv()
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")
if not OPENWEATHER_API_KEY:
    st.error("⚠️ OPENWEATHER_API_KEY not found. Add it to your .env file.")
    st.stop()

# ------------------- POPULAR PLACES -------------------
popular_places = {
    "Mumbai": (19.0760, 72.8777),
    "Delhi": (28.6139, 77.2090),
    "Bangalore": (12.9716, 77.5946),
    "Chennai": (13.0827, 80.2707),
    "Kolkata": (22.5726, 88.3639)
}

selected_place = st.selectbox("📍 Select a city:", list(popular_places.keys()))
LAT, LON = popular_places[selected_place]

# ------------------- DATE INPUT -------------------
date_selected = st.date_input("📅 Select a date for your outdoor activity:",
                              min_value=datetime.today().date(),
                              max_value=(datetime.today() + timedelta(days=5)).date())

# ------------------- FETCH WEATHER FORECAST -------------------
url = f"https://api.openweathermap.org/data/2.5/forecast?lat={LAT}&lon={LON}&appid={OPENWEATHER_API_KEY}&units=metric"

try:
    response = requests.get(url)
    response.raise_for_status()
    forecast_json = response.json()
except Exception as e:
    st.error(f"❌ Error fetching weather data: {e}")
    st.stop()

# ------------------- PROCESS FORECAST -------------------
forecast_list = forecast_json["list"]

# Filter for selected date
selected_forecast = [f for f in forecast_list if f["dt_txt"].startswith(str(date_selected))]

if not selected_forecast:
    st.warning("⚠️ No forecast data available for this date. Try another date.")
    st.stop()

df = pd.DataFrame([{
    "time": f["dt_txt"],
    "temperature": f["main"]["temp"],
    "humidity": f["main"]["humidity"],
    "wind_speed": f["wind"]["speed"],
    "weather": f["weather"][0]["description"],
    "rain": f.get("rain", {}).get("3h", 0)
} for f in selected_forecast])

# ------------------- WEATHER RISK CATEGORIES -------------------
def weather_risk(temp, wind, rain, humidity):
    if temp >= 35:
        return "Very Hot"
    elif temp <= 10:
        return "Very Cold"
    elif wind >= 10:
        return "Very Windy"
    elif rain > 2:
        return "Very Wet"
    elif humidity >= 80 and 20 <= temp <= 32:
        return "Very Uncomfortable"
    else:
        return "Comfortable"

df["Condition"] = df.apply(lambda row: weather_risk(row["temperature"], row["wind_speed"], row["rain"], row["humidity"]), axis=1)

# ------------------- VISUALIZATION -------------------
st.subheader(f"🌤️ Weather Forecast for {selected_place} on {date_selected}")

fig, ax = plt.subplots(figsize=(7,4))
ax.plot(df["time"], df["temperature"], marker="o", label="Temperature (°C)")
ax.set_xticklabels(df["time"], rotation=45, fontsize=7)
ax.set_ylabel("Temperature (°C)")
ax.set_xlabel("Time")
ax.set_title(f"Temperature Trend - {selected_place}")
ax.legend()
st.pyplot(fig)

# ------------------- DATAFRAME -------------------
st.subheader("📊 Detailed Forecast")
st.dataframe(df)

# ------------------- RISK SUMMARY -------------------
st.subheader("⚠️ Risk Assessment")

risk_counts = df["Condition"].value_counts().to_dict()
total_slots = len(df)

st.write("### 📊 Condition Probabilities")
for condition, count in risk_counts.items():
    probability = (count / total_slots) * 100
    st.write(f"👉 {condition}: {count} time slots ({probability:.1f}%)")

# Optional: visualize probabilities
st.write("### 📈 Probability Chart")
fig2, ax2 = plt.subplots(figsize=(6,4))
ax2.bar(risk_counts.keys(), [(c/total_slots)*100 for c in risk_counts.values()])
ax2.set_ylabel("Probability (%)")
ax2.set_title("Likelihood of Weather Conditions")
st.pyplot(fig2)

# ------------------- AI-LIKE INSIGHT -------------------
st.subheader("🤖 Summary Insight")
unique_conditions = df["Condition"].unique()
summary = f"For {selected_place} on {date_selected}, conditions are mostly: {', '.join(unique_conditions)}."
if "Very Hot" in unique_conditions:
    summary += " 🥵 Stay hydrated and avoid peak afternoon heat."
if "Very Cold" in unique_conditions:
    summary += " 🥶 Wear layers and protect against the cold."
if "Very Windy" in unique_conditions:
    summary += " 💨 Be cautious with outdoor activities."
if "Very Wet" in unique_conditions:
    summary += " 🌧️ Carry rain gear or reconsider outdoor plans."
if "Very Uncomfortable" in unique_conditions:
    summary += " 😓 High humidity may cause discomfort."
if "Comfortable" in unique_conditions:
    summary += " ✅ Great conditions for outdoor activities!"
st.info(summary)
