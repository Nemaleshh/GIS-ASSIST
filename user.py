import ollama
import json
from datetime import datetime

import yaml
import os

# ✅ Load config
with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

DATA_DIR = config["data_dir"]
DOWNLOADS_DIR = config["downloads_dir"]



from filehandle import (
    extract_today_zip_files,
    rename_folders_to_date_format,
    process_all_scenes
)
from webscrap import login_and_enter_location

# 🔍 Extract structured task info using LLaMA
def extract_task_info(user_input):
    prompt = f"""
You are a GIS assistant for flood risk mapping.

Your task is to extract structured information from the user request.

If a location is mentioned, include its approximate latitude and longitude using your world knowledge.

Return the start_date and end_date in this format:
"01 June 2025", "30 June 2025"

User request: "{user_input}"

Return a JSON object with the following fields:
- task
- location
- latitude
- longitude
- start_date
- end_date

Strictly return only JSON. Do not explain anything.
"""
    try:
        response = ollama.chat(model='llama3:8b', messages=[{"role": "user", "content": prompt}])
        content = response['message']['content']
        json_start = content.find("{")
        json_end = content.rfind("}") + 1
        return json.loads(content[json_start:json_end])
    except Exception as e:
        print("❌ LLaMA failed to respond correctly.")
        print(e)
        return {}

# 📖 Log the extracted task
def log_task_info(info):
    with open("task_log.jsonl", "a") as f:
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "info": info
        }
        f.write(json.dumps(log_entry) + "\n")

# 🌊 Simulated flood risk analysis
def run_flood_risk_analysis(coords, start_date, end_date):
    print(f"\n🌧️ Running flood risk mapping...")
    print(f"📍 Coordinates: {coords}")
    print(f"🗓️ Period: {start_date} to {end_date}")
    print("🛠️ (Simulation) Performing spatial analysis using DEM + rainfall data...")
    print("✅ Flood risk analysis complete. (placeholder output)")

# 🧠 Full pipeline handler
def process_user_prompt(user_input):
    print("🧠 Thinking with LLaMA 3...")

    try:
        info = extract_task_info(user_input)

        print(f"\n📍 Location: {info['location']} ({info['latitude']}, {info['longitude']})")
        print(f"📆 Start: {info['start_date']}, End: {info['end_date']}")

        log_task_info(info)
        run_flood_risk_analysis(
            (info['latitude'], info['longitude']),
            info['start_date'],
            info['end_date']
        )

        print("\n🌐 Launching web automation using Selenium...")
        driver = login_and_enter_location(
            username="nemu",
            password="Nemu@2005",
            latitude=str(info['latitude']),
            longitude=str(info['longitude']),
            start_date=info['start_date'],
            end_date=info['end_date']
        )

        print("\n📁 Starting satellite file handling workflow...")
        downloads_dir = DOWNLOADS_DIR
        target_dir = DATA_DIR

        extract_today_zip_files(downloads_dir, target_dir)
        rename_folders_to_date_format(target_dir)
        process_all_scenes(target_dir)

    except Exception as e:
        print(f"❌ Failed to process user prompt: {e}")
