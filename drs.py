import ssl
import certifi
import geopy.geocoders
from geopy.geocoders import Nominatim

# Force Geopy to use updated certificates
ctx = ssl.create_default_context(cafile=certifi.where())
geopy.geocoders.options.default_ssl_context = ctx

geolocator = Nominatim(user_agent="weather_app")
import streamlit as st
import requests
from geopy.geocoders import Nominatim
from datetime import datetime
import pytz
import matplotlib.pyplot as plt
import pandas as pd

# ---------------- PAGE SETUP ----------------
st.set_page_config(page_title="🌍 ClimaSphere", page_icon="🌦", layout="wide")

# ---------------- CUSTOM STYLING WITH WEATHER-THEMED BACKGROUND ----------------
st.markdown(
    """
    <style>
    /* 🌤 Page Background - cloudy, blue-sky theme */
    [data-testid="stAppViewContainer"] {
        background: linear-gradient(rgba(0, 0, 0, 0.35), rgba(0, 0, 0, 0.45)),
                    url('https://images.unsplash.com/photo-1501973801540-537f08ccae7b?auto=format&fit=crop&w=1920&q=80');
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background: rgba(30, 41, 59, 0.85);
        backdrop-filter: blur(8px);
    }

    /* City card */
    .city-card {
        background: rgba(30, 41, 59, 0.8);
        border-radius: 20px;
        padding: 20px;
        color: white;
        box-shadow: 0 6px 15px rgba(0,0,0,0.4);
        transition: 0.3s ease-in-out;
        margin-bottom: 20px;
    }
    .city-card:hover {
        transform: scale(1.03);
        box-shadow: 0 8px 20px rgba(0,0,0,0.6);
    }

    /* Headings and text */
    h1, h3, p, label {
        color: white !important;
        text-shadow: 1px 1px 3px rgba(0,0,0,0.7);
    }

    /* Input field */
    .stTextInput>div>div>input {
        background-color: rgba(255,255,255,0.9);
        color: black;
        border-radius: 10px;
    }

    </style>
    """,
    unsafe_allow_html=True
)

# ---------------- TITLE ----------------
st.title("❄️🍂Clima Sphere🌞☔")
st.caption("Get live weather updates & 7-day trends — powered by Open-Meteo API")

# ---------------- LANGUAGE SELECTION ----------------
language = st.selectbox(
    "🌐 Choose language:",
    ["English", "Spanish", "French", "German", "Hindi", "Chinese", "Arabic"]
)

# ---------------- TRANSLATION DICTIONARY ----------------
translations = {
    "English": {"Temperature": "Temperature","Wind Speed": "Wind Speed","Direction": "Direction","Local Time": "Local Time","Weekly Weather Summary": "Weekly Weather Summary","City not found. Please check spelling.": "City not found. Please check spelling.","No weekly data available.": "No weekly data available."},
    "Spanish": {"Temperature": "Temperatura","Wind Speed": "Velocidad del viento","Direction": "Dirección","Local Time": "Hora local","Weekly Weather Summary": "Resumen semanal del clima","City not found. Please check spelling.": "Ciudad no encontrada. Verifique la ortografía.","No weekly data available.": "No hay datos semanales disponibles."},
    "French": {"Temperature": "Température","Wind Speed": "Vitesse du vent","Direction": "Direction","Local Time": "Heure locale","Weekly Weather Summary": "Résumé météorologique hebdomadaire","City not found. Please check spelling.": "Ville non trouvée. Vérifiez l’orthographe.","No weekly data available.": "Aucune donnée hebdomadaire disponible."},
    "German": {"Temperature": "Temperatur","Wind Speed": "Windgeschwindigkeit","Direction": "Richtung","Local Time": "Ortszeit","Weekly Weather Summary": "Wöchentliche Wetterübersicht","City not found. Please check spelling.": "Stadt nicht gefunden. Bitte überprüfe die Schreibweise.","No weekly data available.": "Keine wöchentlichen Daten verfügbar."},
    "Hindi": {"Temperature": "तापमान","Wind Speed": "हवा की गति","Direction": "दिशा","Local Time": "स्थानीय समय","Weekly Weather Summary": "साप्ताहिक मौसम सारांश","City not found. Please check spelling.": "शहर नहीं मिला। कृपया वर्तनी जांचें।","No weekly data available.": "साप्ताहिक डेटा उपलब्ध नहीं है।"},
    "Chinese": {"Temperature": "温度","Wind Speed": "风速","Direction": "方向","Local Time": "当地时间","Weekly Weather Summary": "每周天气总结","City not found. Please check spelling.": "未找到城市。请检查拼写。","No weekly data available.": "没有可用的每周数据。"},
    "Arabic": {"Temperature": "درجة الحرارة","Wind Speed": "سرعة الرياح","Direction": "الاتجاه","Local Time": "الوقت المحلي","Weekly Weather Summary": "ملخص الطقس الأسبوعي","City not found. Please check spelling.": "لم يتم العثور على المدينة. يرجى التحقق من التهجئة.","No weekly data available.": "لا توجد بيانات أسبوعية متاحة."},
}

def T(text):
    return translations.get(language, translations["English"]).get(text, text)

# ---------------- MULTI-CITY INPUT ----------------
cities_input = st.text_input("🏙 Enter city names (comma-separated):", "New York,Japan")
cities = [c.strip() for c in cities_input.split(",") if c.strip()]

geolocator = Nominatim(user_agent="weather_app")

# ---------------- HELPER FUNCTION ----------------
def deg_to_compass(deg):
    dirs = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
    ix = round(deg / 45) % 8
    return dirs[ix]

# ---------------- MAIN LOOP (MULTI-CITY DISPLAY) ----------------
cards_per_row = 3

for i in range(0, len(cities), cards_per_row):
    row_cities = cities[i:i + cards_per_row]
    cols = st.columns(len(row_cities))

    for j, city in enumerate(row_cities):
        with cols[j]:
            st.markdown("<div class='city-card'>", unsafe_allow_html=True)
            st.markdown(f"<h3 style='text-align:center;'>📍 {city}</h3>", unsafe_allow_html=True)

            location = geolocator.geocode(city)
            if not location:
                st.error(f"❌ {T('City not found. Please check spelling.')}") 
                continue

            lat, lon = location.latitude, location.longitude

            # 🌤 SINGLE API CALL
            try:
                url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
                data = requests.get(url).json()
            except Exception:
                st.error("⚠ Failed to fetch weather data.")
                continue

            weather = data.get("current_weather", {})
            weekly_data = data.get("daily", {})

            if weather:
                timezone = data.get("timezone", "UTC")
                local_time = datetime.now(pytz.timezone(timezone)).strftime("%I:%M %p")

                direction_text = deg_to_compass(weather['winddirection'])

                st.metric(f"🌡 {T('Temperature')}", f"{weather['temperature']} °C")
                st.metric(f"💨 {T('Wind Speed')}", f"{weather['windspeed']} m/s")
                st.metric(f"🧭 {T('Direction')}", f"{direction_text} ({weather['winddirection']}°)")
                st.metric(f"🕒 {T('Local Time')}", local_time)

                # 📊 WEEKLY BAR GRAPH
                if "time" in weekly_data:
                    days = []
                    for d in weekly_data["time"]:
                        try:
                            days.append(datetime.strptime(d, "%Y-%m-%d").strftime("%-d %b"))
                        except:
                            days.append(datetime.strptime(d, "%Y-%m-%d").strftime("%#d %b"))

                    temp_max = weekly_data["temperature_2m_max"]
                    temp_min = weekly_data["temperature_2m_min"]

                    plt.style.use("dark_background")
                    fig, ax = plt.subplots(figsize=(4, 2))
                    x = range(len(days))
                    ax.bar(x, temp_max, color="#ef4444", width=0.4, label="Max Temp")
                    ax.bar([k + 0.4 for k in x], temp_min, color="#3b82f6", width=0.4, label="Min Temp")
                    ax.set_xticks([k + 0.2 for k in x])
                    ax.set_xticklabels(days, rotation=45, fontsize=8)
                    ax.set_title(f"📈 {T('Weekly Weather Summary')}", fontsize=9, color="white")
                    ax.legend(fontsize=7)
                    ax.tick_params(colors="white")
                    ax.set_facecolor("#1e293b")
                    fig.patch.set_facecolor((0, 0, 0, 0))

                    st.pyplot(fig)

            st.markdown("</div>", unsafe_allow_html=True)
