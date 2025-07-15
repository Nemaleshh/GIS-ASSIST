import rasterio
from rasterio.enums import Resampling
import numpy as np
import matplotlib.pyplot as plt
import os

def generate_flood_extent(ndwi_2024_path, ndwi_2025_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # Load base raster (2024)
    with rasterio.open(ndwi_2024_path) as src1:
        ndwi_1 = src1.read(1)
        profile = src1.profile
        ref_shape = ndwi_1.shape

    # Load and resample the 2025 raster to match 2024
    with rasterio.open(ndwi_2025_path) as src2:
        ndwi_2 = src2.read(
            1,
            out_shape=ref_shape,
            resampling=Resampling.bilinear
        )

    # Compute NDWI difference
    delta_ndwi = ndwi_2 - ndwi_1

    # Threshold to create flood mask
    flood_mask = (delta_ndwi > 0.2).astype(np.uint8)

    # Save flood mask as GeoTIFF
    profile.update(dtype='uint8', count=1)
    output_tif = os.path.join(output_dir, "flood_mask.tif")
    with rasterio.open(output_tif, 'w', **profile) as dst:
        dst.write(flood_mask, 1)

    # Save PNG visual (spatial map)
    output_png = os.path.join(output_dir, "flood_mask.png")
    plt.imshow(flood_mask, cmap='Blues')
    plt.title("Flood Extent Map")
    plt.axis("off")
    plt.savefig(output_png, bbox_inches='tight', dpi=300)
    plt.close()

    # Compute summary statistics
    total_pixels = flood_mask.size
    flooded_pixels = int(np.sum(flood_mask))
    non_flooded_pixels = int(total_pixels - flooded_pixels)

    flooded_percent = round((flooded_pixels / total_pixels) * 100, 2)
    non_flooded_percent = round(100 - flooded_percent, 2)

    # Save bar chart of stats
    stats_png = os.path.join(output_dir, "flood_stats.png")
    plt.bar(['Flooded', 'Non-Flooded'], [flooded_pixels, non_flooded_pixels], color=['blue', 'gray'])
    plt.ylabel("Pixel Count")
    plt.title("Flood Extent Summary")
    plt.savefig(stats_png, bbox_inches='tight', dpi=300)
    plt.close()

    print(f"✅ Flood mask saved in: {output_tif} and {output_png}")
    print(f"📊 Summary:")
    print(f"  Flooded Pixels     : {flooded_pixels} ({flooded_percent}%)")
    print(f"  Non-Flooded Pixels : {non_flooded_pixels} ({non_flooded_percent}%)")

    return {
        "flooded_pixels": flooded_pixels,
        "non_flooded_pixels": non_flooded_pixels,
        "flooded_percent": flooded_percent,
        "non_flooded_percent": non_flooded_percent,
        "flood_mask_tif": output_tif,
        "flood_map_png": output_png,
        "flood_stats_png": stats_png
    }
