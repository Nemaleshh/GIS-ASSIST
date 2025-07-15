import os
import glob
from pathlib import Path
from datetime import datetime
import importlib

def parse_date(folder_name):
    try:
        return datetime.strptime(folder_name.split("_")[0], "%Y-%m-%d")
    except:
        return None

def find_file_recursive(folder, filename_substring):
    matches = glob.glob(os.path.join(folder, '**', f'*{filename_substring}*'), recursive=True)
    return matches[0] if matches else None

def analyze(data_root_path: str):
    data_root = Path(data_root_path)
    output_dir = data_root / "flood_extent"
    site_suitability_output = data_root / "site_suitability_outputs"

    results = {
        "flood": None,
        "ndvi_change": None,
        "site_suitability": None
    }

    # Step 1: Scan and collect valid folders
    valid_folders = []
    for date_folder in data_root.iterdir():
        if not date_folder.is_dir():
            continue
        date = parse_date(date_folder.name)
        if not date:
            continue

        ndwi_path = find_file_recursive(str(date_folder), "NDWI.tif")
        ndvi_path = find_file_recursive(str(date_folder), "NDVI.tif")

        valid_folders.append({
            "date": date,
            "ndwi": Path(ndwi_path) if ndwi_path else None,
            "ndvi": Path(ndvi_path) if ndvi_path else None
        })

    if len(valid_folders) < 2:
        print("❌ Not enough valid folders for analysis.")
        return results

    # Step 2: Sort by date
    valid_folders.sort(key=lambda x: x["date"])
    start = valid_folders[0]
    end = valid_folders[-1]

    print(f"📆 Start Date: {start['date'].strftime('%Y-%m-%d')}")
    print(f"📆 End Date  : {end['date'].strftime('%Y-%m-%d')}")
    print(f"🔍 Start NDWI path: {start['ndwi']}")
    print(f"🔍 End NDWI path  : {end['ndwi']}")

    if not start["ndwi"] or not end["ndwi"]:
        print("❌ NDWI file(s) missing in start or end folder.")
        return results

    # Step 3: Flood detection
    import flood
    importlib.reload(flood)
    from flood import generate_flood_extent

    flood_stats = generate_flood_extent(start["ndwi"], end["ndwi"], output_dir)

    print("\n📊 Flood Statistics Summary:")
    print(f"  Flooded Pixels     : {flood_stats['flooded_pixels']} ({flood_stats['flooded_percent']}%)")
    print(f"  Non-Flooded Pixels : {flood_stats['non_flooded_pixels']} ({flood_stats['non_flooded_percent']}%)")
    print(f"  TIFF File          : {flood_stats['flood_mask_tif']}")
    print(f"  PNG Map            : {flood_stats['flood_map_png']}")
    print(f"  Stats Chart        : {flood_stats['flood_stats_png']}")

    results["flood"] = flood_stats

    # Step 4: NDVI change detection
    import ndvi_change
    importlib.reload(ndvi_change)
    from ndvi_change import generate_ndvi_change

    if not start["ndvi"] or not end["ndvi"]:
        print("⚠️ NDVI file(s) missing. Skipping NDVI analysis.")
    else:
        ndvi_stats = generate_ndvi_change(start["ndvi"], end["ndvi"], output_dir)

        print("\n📊 NDVI Statistics:")
        print(f"  Gain     : {ndvi_stats['gain_pixels']} ({ndvi_stats['gain_percent']}%)")
        print(f"  Loss     : {ndvi_stats['loss_pixels']} ({ndvi_stats['loss_percent']}%)")
        print(f"  Neutral  : {ndvi_stats['neutral_pixels']} ({ndvi_stats['neutral_percent']}%)")
        print(f"  Chart    : {ndvi_stats['ndvi_stats_chart']}")

        results["ndvi_change"] = ndvi_stats

    # Step 5: Site suitability
    import site_suitable
    importlib.reload(site_suitable)
    from site_suitable import generate_site_suitability

    site_suitability_result = generate_site_suitability(
        ndvi_path=end["ndvi"],
        ndwi_path=end["ndwi"],
        flood_mask_path=Path(flood_stats["flood_mask_tif"]),
        output_dir=site_suitability_output
    )

    print("\n✅ Site suitability generation complete.")
    results["site_suitability"] = site_suitability_result if site_suitability_result else {
        "status": "complete",
        "path": str(site_suitability_output)
    }

    return results
