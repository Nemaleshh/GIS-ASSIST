import rasterio
from rasterio.enums import Resampling
import numpy as np
import matplotlib.pyplot as plt
import os

def generate_site_suitability(ndvi_path, ndwi_path, flood_mask_path, output_dir):
    """
    Generate site suitability map based on NDVI, NDWI, and flood mask.

    Parameters:
        ndvi_path (str): Path to NDVI GeoTIFF.
        ndwi_path (str): Path to NDWI GeoTIFF.
        flood_mask_path (str): Path to binary flood mask GeoTIFF.
        output_dir (str): Directory to save output files.
    """
    os.makedirs(output_dir, exist_ok=True)

    # Read NDVI
    with rasterio.open(ndvi_path) as src:
        ndvi = src.read(1)
        profile = src.profile
        shape = ndvi.shape

    # Read NDWI
    with rasterio.open(ndwi_path) as src:
        ndwi = src.read(1, out_shape=shape, resampling=Resampling.bilinear)

    # Read flood mask
    with rasterio.open(flood_mask_path) as src:
        flood_mask = src.read(1, out_shape=shape, resampling=Resampling.nearest).astype(bool)

    # Apply suitability conditions
    suitability = (
        (ndvi > 0.4) &
        (ndwi < 0.2) &
        (~flood_mask)
    )

    # Save GeoTIFF
    profile.update(dtype='uint8', count=1)
    tif_path = os.path.join(output_dir, "site_suitability.tif")
    with rasterio.open(tif_path, 'w', **profile) as dst:
        dst.write(suitability.astype(np.uint8), 1)

    # Save PNG
    plt.imshow(suitability, cmap="gray")
    plt.title("Site Suitability Map")
    plt.axis("off")
    png_path = os.path.join(output_dir, "site_suitability.png")
    plt.savefig(png_path, bbox_inches='tight', dpi=300)
    plt.close()

    print("✅ Site suitability map saved to:", tif_path, "and", png_path)
