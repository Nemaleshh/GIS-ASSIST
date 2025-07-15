import subprocess
import os
import glob
from generation import analyze  # ✅ Replace with your actual pipeline module

def run_llm_pipeline(base_data_path):


    import os

    # --- Step 0: Automatically get first and last folder ---
    all_folders = [
        name for name in os.listdir(base_data_path)
        if os.path.isdir(os.path.join(base_data_path, name))
    ]

    # Sort folders (assuming folder names like "YYYY-MM-DD")
    all_folders.sort()

    if not all_folders:
        raise ValueError(f"No folders found in {base_data_path}")

    folder_start = os.path.join(base_data_path, all_folders[0])
    folder_end = os.path.join(base_data_path, all_folders[-3])

    print(f"📁 Auto-selected start folder: {folder_start}")
    print(f"📁 Auto-selected end folder:   {folder_end}")


    # --- Step 1: Run the analysis and extract flood & NDVI stats ---
    analysis_result = analyze(base_data_path)

    flood_stats = {
        'flooded_pixels': 0,
        'flooded_percent': 0.0,
        'non_flooded_pixels': 0,
        'non_flooded_percent': 0.0,
    }
    ndvi_stats = {
        'gain_pixels': 0,
        'gain_percent': 0.0,
        'loss_pixels': 0,
        'loss_percent': 0.0,
        'neutral_pixels': 0,
        'neutral_percent': 0.0
    }

    if analysis_result:
        if analysis_result.get("flood"):
            flood_stats.update(analysis_result["flood"])
        if analysis_result.get("ndvi_change"):
            ndvi_stats.update(analysis_result["ndvi_change"])

    # --- Step 2: Helpers ---
    def find_meta_file(folder):
        meta_files = glob.glob(os.path.join(folder, '**', '*.meta*'), recursive=True)
        if not meta_files:
            raise FileNotFoundError(f"No .meta files found in {folder}")
        return meta_files[0]

    def extract_times(filepath):
        start, end = None, None
        with open(filepath, 'r') as f:
            for line in f:
                if "ProductSceneStartTime" in line or "SceneStartTime" in line:
                    if not start:
                        start = line.split("=")[-1].strip()
                elif "ProductSceneEndTime" in line or "SceneEndTime" in line:
                    if not end:
                        end = line.split("=")[-1].strip()
        return start, end

    start_meta_file = find_meta_file(folder_start)
    end_meta_file = find_meta_file(folder_end)

    print(f"✅ Found start metadata file: {start_meta_file}")
    print(f"✅ Found end metadata file: {end_meta_file}")

    scene1_start, scene1_end = extract_times(start_meta_file)
    scene2_start, scene2_end = extract_times(end_meta_file)

    # --- Step 3: Build LLM prompt ---
    prompt = f"""
You are a geospatial reasoning expert.

Here is the metadata and analysis information for two satellite scenes:

scene1_start_time: "{scene1_start}"
scene1_end_time:   "{scene1_end}"
scene2_start_time: "{scene2_start}"
scene2_end_time:   "{scene2_end}"

Flood classification stats:
  flooded_pixels: {flood_stats['flooded_pixels']}
  flooded_percent: {flood_stats['flooded_percent']}
  non_flooded_pixels: {flood_stats['non_flooded_pixels']}
  non_flooded_percent: {flood_stats['non_flooded_percent']}

NDVI change stats:
  gain_pixels: {ndvi_stats['gain_pixels']}
  loss_pixels: {ndvi_stats['loss_pixels']}
  gain_percent: {ndvi_stats['gain_percent']}
  loss_percent: {ndvi_stats['loss_percent']}
  neutral_pixels: {ndvi_stats['neutral_pixels']}
  neutral_percent: {ndvi_stats['neutral_percent']}

Tasks:
1. Calculate the duration of each scene and compare.
2. Explain if flood and NDVI loss are correlated.
3. Create a Chain-of-Thought analysis log.
4. Generate a complete, downloadable YAML or JSON workflow containing:
   - workflow_name
   - inputs
   - analysis_log
   - steps (with id, operation, reasoning)
   - outputs
   - recommendations

All keys must use snake_case and your output must be valid YAML or JSON.
Do not include extra explanation. Output ONLY valid YAML or JSON ready for saving.
"""

    # --- Step 4: Run Ollama ---
    print("\n🚀 Running llama3:8b with Ollama...")
    process = subprocess.run(
        ["ollama", "run", "llama3:8b"],
        input=prompt.encode("utf-8"),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    output = process.stdout.decode("utf-8").strip()

    # --- Step 5: Save output ---
    if output.startswith("{"):
        output_file = "flood_workflow.json"
    elif output.startswith("workflow_name") or output.startswith("---"):
        output_file = "flood_workflow.yaml"
    else:
        output_file = "flood_workflow.txt"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"\n📥 LLaMA 3 output saved to: {output_file}")
