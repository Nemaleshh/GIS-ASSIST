import streamlit as st
import os
import re
from PIL import Image
import pandas as pd

from user import process_user_prompt
from generation import analyze
from outputllm import run_llm_pipeline
import yaml

with open("config.yaml", "r") as f:
    config = yaml.safe_load(f)

DATA_DIR = config["data_dir"]
WORKFLOW_FILE = config["workflow_file"]


# 👉 Initialize session state for LLM
if 'conversation_history' not in st.session_state:
    st.session_state['conversation_history'] = []


if 'submitted' not in st.session_state:
    st.session_state['submitted'] = False

if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ""


# 👉 Function to clean dates
def clean_date_folder(date_folder):
    return re.sub(r'_\d+$', '', date_folder)

import yaml

def convert_workflow_txt_to_yaml(txt_path):
    steps = []
    with open(txt_path, "r") as f:
        for line in f:
            line = line.strip()
            if line:
                steps.append(line)
    workflow = {"flood_workflow": steps}
    yaml_content = yaml.dump(workflow, sort_keys=False)
    return yaml_content

# 👉 Function to get images
def get_composite_images(base_dir="DATA_DIR"):
    images = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.lower() == "false_color_composite.png":
                parts = root.split(os.sep)
                date_folder = next((p for p in parts if p.startswith("2024") or p.startswith("2025")), "Unknown")
                date_folder_clean = clean_date_folder(date_folder)
                images.append((date_folder_clean, os.path.join(root, file)))
    # Deduplicate
    unique_images = {}
    for date, path in images:
        if date not in unique_images:
            unique_images[date] = path
    return sorted(unique_images.items())

def run_workflow():
    st.session_state['submitted'] = True
    st.info("⏳ Processing your request...")
    process_user_prompt(st.session_state['user_input'])
    analyze(DATA_DIR)
    results = run_llm_pipeline(DATA_DIR)
    st.session_state['results'] = results
    st.success("✅ Task processed. Scroll down to see outputs.")




# 🌊 Streamlit UI
st.set_page_config(layout="wide")
st.title("🚀GIS Assistant")
st.session_state['user_input'] = st.text_area(
    "Enter your analysis query:",
    value=st.session_state['user_input']
)

import subprocess

# 📌 LLM system prompt
SYSTEM_PROMPT = """
You are a geospatial reasoning expert.
You work with satellite metadata, flood classification, NDVI change detection, and produce Chain-of-Thought analysis for research.
Always use snake_case, stay concise, do not add extra explanation.
"""

def run_llm_chat(user_message, conversation_history):
    prompt = SYSTEM_PROMPT + "\n"
    for turn in conversation_history:
        prompt += f"User: {turn['user']}\nAssistant: {turn['assistant']}\n"
    prompt += f"User: {user_message}\nAssistant:"

    process = subprocess.run(
        ["ollama", "run", "llama3:8b"],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    output = process.stdout.decode("utf-8").strip()
    conversation_history.append({"user": user_message, "assistant": output})
    return output, conversation_history

if not st.session_state['submitted']:
    st.button("Submit", on_click=run_workflow)
else:
    st.info("✅ Task already submitted. If you want to rerun, restart the app.")

if st.session_state.get("submitted", False):
    results = st.session_state.get("results")
    if results:
        st.markdown("### 📊 Flood Statistics Summary:")
        flood = results.get('flood', {})
        st.write(f"  Flooded Pixels     : {flood.get('flooded_pixels')} ({flood.get('flooded_percent')}%)")
        st.write(f"  Non-Flooded Pixels : {flood.get('non_flooded_pixels')} ({flood.get('non_flooded_percent')}%)")

        st.markdown("### 📊 NDVI Statistics:")
        ndvi = results.get('ndvi_change', {})
        st.write(f"  Gain     : {ndvi.get('gain_pixels')} ({ndvi.get('gain_percent')}%)")
        st.write(f"  Loss     : {ndvi.get('loss_pixels')} ({ndvi.get('loss_percent')}%)")
        st.write(f"  Neutral  : {ndvi.get('neutral_pixels')} ({ndvi.get('neutral_percent')}%)")

        site = results.get('site_suitability', {})
        st.markdown("### 📌 Site Suitability:")
        st.write(f"  Status : {site.get('status')}")
        st.write(f"  Path   : {site.get('path')}")


# ✅ Interactive LLM Research Chat
if st.session_state.get("submitted", False):
    st.markdown("---")
    st.markdown("## 🧑‍💻 Interactive LLM Research Chat")
    st.info("Ask any follow-up questions about your analysis results.")

    # 👇 Add a text input for user question
    user_chat_input = st.text_input(
        "Type your LLM research question:",
        key="chat_input",
        placeholder="e.g., Explain the correlation between flood and NDVI loss..."
    )

    # 👇 Add a button to submit the chat question
    if st.button("Send LLM Query"):
        if user_chat_input.strip():
            with st.spinner("🧠 LLM thinking..."):
                response, st.session_state['conversation_history'] = run_llm_chat(
                    user_chat_input.strip(),
                    st.session_state['conversation_history']
                )
                st.markdown(f"**LLM:** {response}")
        else:
            st.warning("⚠️ Please type a question!")

    # 👇 Show full conversation history
    if st.session_state['conversation_history']:
        st.markdown("### 📜 Conversation History")
        for turn in st.session_state['conversation_history']:
            st.markdown(f"**You:** {turn['user']}")
            st.markdown(f"**LLM:** {turn['assistant']}")


# ✅ 3️⃣ Continue with image grid below
st.markdown("### 🛰️ Satellite Composite Outputs")

image_list = get_composite_images()

if image_list:
    cols = st.columns(4)
    for idx, (date, path) in enumerate(image_list):
        with cols[idx % 4]:
            try:
                st.image(Image.open(path), caption="", use_container_width=True)
                st.write(f"📅 {date}")

                # Dummy per-image data: add real logic if needed
                with open(path, "rb") as img_file:
                    img_bytes = img_file.read()

                st.download_button(
                    label="⬇️ Download Image",
                    data=img_bytes,
                    file_name=f"composite_{date}.png",
                    mime="image/png",
                    key=f"download_img_{idx}"
                )


            except Exception as e:
                st.error(f"Could not load image: {path}\nError: {e}")
else:
    st.warning("⚠️ No flood composite outputs found yet.")
# ✅ 4️⃣ Detailed Benchmark Outputs (ALWAYS visible)
st.markdown("---")
st.markdown("## 🗺️ Detailed Benchmark Outputs")

# 📍 1) Flood Extent
st.markdown("### 🌊 Flood Extent Risk Map")
try:
    BASE_DIR =DATA_DIR
    flood_png = os.path.join(BASE_DIR, "flood_extent", "flood_mask.png")
    flood_tif = os.path.join(BASE_DIR, "flood_extent", "flood_mask.tif")

    # ✅ Use st.image to handle local paths safely
    col_center = st.columns(3)
    with col_center[1]:  # center column
        st.image(Image.open(flood_png), caption="Flood Extent Risk", width=500)

    with open(flood_tif, "rb") as tif_file:
        tif_bytes = tif_file.read()

    # ✅ Center the download button too
    with col_center[1]:
        st.download_button(
            label="⬇️ Download Flood Extent GeoTIFF",
            data=tif_bytes,
            file_name="flood_mask.tif",
            mime="image/tiff",
            key="download_flood_tif"
        )

except Exception as e:
    st.warning(f"Flood extent data not found. {e}")

# 📍 2) NDVI Change Detection
st.markdown("### 🌿 NDVI Change Detection")
try:
    ndvi_change_png = os.path.join(DATA_DIR, "flood_extent", "NDVI_change.png")
    ndvi_stats_png = os.path.join(DATA_DIR, "flood_extent", "ndvi_stats.png")

    # 🟢 Use two columns side-by-side
    ndvi_cols = st.columns(2)

    with ndvi_cols[0]:
        st.image(Image.open(ndvi_change_png), caption="NDVI Change Map", width=500)

    with ndvi_cols[1]:
        st.image(Image.open(ndvi_stats_png), caption="NDVI Statistics Chart", width=500)
    # ✅ Safe, portable path
    ndvi_tif_path = os.path.join(DATA_DIR, "flood_extent", "delta_ndvi.tif")

    # ✅ Open and serve file
    with open(ndvi_tif_path, "rb") as tif_file:
        tif_bytes = tif_file.read()

    st.download_button(
        label="⬇️ Download NDVI Change GeoTIFF",
        data=tif_bytes,
        file_name="delta_ndvi.tif",
        mime="image/tiff",
        key="download_ndvi_tif"
    )

except Exception as e:
    st.warning(f"NDVI change detection data not found. {e}")


# ✅ 5️⃣ Flood Workflow YAML
st.markdown("---")
st.markdown("## 🗂️ Flood Risk Workflow (YAML)")
# Example if your workflow file is in the root
workflow_txt_path = WORKFLOW_FILE

try:
    yaml_doc = convert_workflow_txt_to_yaml(workflow_txt_path)

    # ✅ Display the YAML in a code block
    st.code(yaml_doc, language="yaml")

    # ✅ Download button for the YAML file
    st.download_button(
        label="⬇️ Download Flood Workflow YAML",
        data=yaml_doc,
        file_name="flood_workflow.yaml",
        mime="text/yaml",
        key="download_workflow_yaml"
    )

except Exception as e:
    st.warning(f"Could not generate workflow YAML: {e}")
import os
from PIL import Image
