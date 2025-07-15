import os
import re
import zipfile
from datetime import datetime, date
import rasterio
import numpy as np
import matplotlib.pyplot as plt

# === UTILS ===
month_map = {
    "JAN": 1, "FEB": 2, "MAR": 3, "APR": 4,
    "MAY": 5, "JUN": 6, "JUL": 7, "AUG": 8,
    "SEP": 9, "OCT": 10, "NOV": 11, "DEC": 12
}

def normalize(array):
    return (array - np.min(array)) / (np.max(array) - np.min(array) + 1e-5)

def save_tif(output_path, array, profile):
    profile.update(dtype='float32', count=1)
    with rasterio.open(output_path, 'w', **profile) as dst:
        dst.write(array, 1)

def load_band(path):
    with rasterio.open(path) as src:
        data = src.read(1).astype('float32')
        profile = src.profile
    return data, profile

def compute_ndvi(nir, red):
    return (nir - red) / (nir + red + 1e-5)

def compute_ndwi(green, nir):
    return (green - nir) / (green + nir + 1e-5)

def compute_mndwi(green, swir):
    return (green - swir) / (green + swir + 1e-5)

def generate_composite(r, g, b):
    rgb = np.stack([normalize(r), normalize(g), normalize(b)], axis=-1)
    return np.clip(rgb, 0, 1)

# === STAGE 1: Extract ZIP Files ===
def extract_today_zip_files(downloads_dir, target_dir):
    os.makedirs(target_dir, exist_ok=True)
    zip_files = []
    for fname in os.listdir(downloads_dir):
        if fname.endswith(".zip") and fname.startswith("R23"):
            fpath = os.path.join(downloads_dir, fname)
            created = datetime.fromtimestamp(os.path.getctime(fpath))
            if created.date() == date.today():
                zip_files.append((fpath, created))

    zip_files.sort(key=lambda x: x[1])

    if not zip_files:
        print("❌ No zip files downloaded today.")
        return

    print(f"📦 Found {len(zip_files)} zip files downloaded today.\n")
    for zip_file, created_time in zip_files:
        filename = os.path.basename(zip_file)
        print(f"🧩 Extracting: {filename}")
        try:
            with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                extract_to = os.path.join(target_dir, os.path.splitext(filename)[0])
                os.makedirs(extract_to, exist_ok=True)
                zip_ref.extractall(extract_to)
                print(f"✅ Extracted to: {extract_to}\n")
        except Exception as e:
            print(f"❌ Failed to extract {filename}: {e}")

# === STAGE 2: Rename Folders Based on Date ===
def rename_folders_to_date_format(target_dir):
    folders = [f for f in os.listdir(target_dir) if os.path.isdir(os.path.join(target_dir, f))]
    for folder in folders:
        match = re.search(r"([A-Z]{3})(\d{4})(\d{6})", folder)
        if match:
            month_str = match.group(1)
            year = int(match.group(2))
            month = month_map.get(month_str.upper(), 1)
            new_name = f"{year:04d}-{month:02d}-01"
            src_path = os.path.join(target_dir, folder)
            dst_path = os.path.join(target_dir, new_name)

            counter = 1
            while os.path.exists(dst_path):
                dst_path = os.path.join(target_dir, f"{new_name}_{counter}")
                counter += 1

            os.rename(src_path, dst_path)
            print(f"✅ Renamed: {folder} → {os.path.basename(dst_path)}")
        else:
            print(f"⚠️ Skipped (no timestamp pattern found): {folder}")

# === STAGE 3: Process Scene ===
def process_scene(scene_path):
    try:
        print(f"🔍 Processing: {scene_path}")
        b2_path = os.path.join(scene_path, "BAND2.tif")
        b3_path = os.path.join(scene_path, "BAND3.tif")
        b4_path = os.path.join(scene_path, "BAND4.tif")
        b5_path = os.path.join(scene_path, "BAND5.tif")

        if not all(os.path.exists(p) for p in [b2_path, b3_path, b4_path, b5_path]):
            print(f"❌ Skipping {scene_path} (Missing one or more band files)")
            return

        b2, profile = load_band(b2_path)
        b3, _ = load_band(b3_path)
        b4, _ = load_band(b4_path)
        b5, _ = load_band(b5_path)

        output_dir = os.path.join(scene_path, "outputs")
        os.makedirs(output_dir, exist_ok=True)

        rgb_image = generate_composite(b3, b2, b2)
        plt.imsave(os.path.join(output_dir, "RGB_composite.png"), rgb_image)

        false_color = generate_composite(b4, b3, b2)
        plt.imsave(os.path.join(output_dir, "False_color_composite.png"), false_color)

        ndvi = compute_ndvi(b4, b3)
        save_tif(os.path.join(output_dir, "NDVI.tif"), ndvi, profile)
        plt.imsave(os.path.join(output_dir, "NDVI.png"), ndvi, cmap='RdYlGn')

        ndwi = compute_ndwi(b2, b4)
        save_tif(os.path.join(output_dir, "NDWI.tif"), ndwi, profile)
        plt.imsave(os.path.join(output_dir, "NDWI.png"), ndwi, cmap='Blues')

        mndwi = compute_mndwi(b2, b5)
        save_tif(os.path.join(output_dir, "MNDWI.tif"), mndwi, profile)
        plt.imsave(os.path.join(output_dir, "MNDWI.png"), mndwi, cmap='Blues')

        print(f"✅ Done: {scene_path}\n")

    except Exception as e:
        print(f"⚠️ Error in {scene_path}: {e}")

def process_all_scenes(base_dir):
    for root, dirs, files in os.walk(base_dir):
        if any(f.startswith("BAND2") for f in files):
            process_scene(root)
