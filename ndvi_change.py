import rasterio
from rasterio.enums import Resampling
import numpy as np
import matplotlib.pyplot as plt
import os

def generate_ndvi_change(ndvi_2024_path, ndvi_2025_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    # Open 2024 NDVI
    with rasterio.open(ndvi_2024_path) as src1:
        ndvi_1 = src1.read(1)
        profile = src1.profile
        shape = ndvi_1.shape

    # Open 2025 NDVI
    with rasterio.open(ndvi_2025_path) as src2:
        ndvi_2 = src2.read(
            1,
            out_shape=shape,
            resampling=Resampling.bilinear
        )

    # NDVI difference
    delta_ndvi = ndvi_2 - ndvi_1

    # Save delta NDVI GeoTIFF
    profile.update(dtype='float32', count=1)
    output_tif = os.path.join(output_dir, "delta_ndvi.tif")
    with rasterio.open(output_tif, 'w', **profile) as dst:
        dst.write(delta_ndvi.astype(np.float32), 1)

    # Save PNG visualization
    output_png = os.path.join(output_dir, "NDVI_change.png")
    plt.imshow(delta_ndvi, cmap="RdYlGn", vmin=-1, vmax=1)
    plt.title("NDVI Change Detection")
    plt.colorbar(label="ΔNDVI")
    plt.axis("off")
    plt.savefig(output_png, bbox_inches='tight', dpi=300)
    plt.close()

    # Categorize NDVI change
    gain = np.sum(delta_ndvi > 0.1)
    loss = np.sum(delta_ndvi < -0.1)
    neutral = np.sum((delta_ndvi >= -0.1) & (delta_ndvi <= 0.1))
    total = gain + loss + neutral

    gain_pct = round((gain / total) * 100, 2)
    loss_pct = round((loss / total) * 100, 2)
    neutral_pct = round((neutral / total) * 100, 2)

    # Save bar chart
    stats_png = os.path.join(output_dir, "ndvi_stats.png")
    plt.bar(['Gain', 'Loss', 'Neutral'], [gain, loss, neutral], color=['green', 'red', 'gray'])
    plt.ylabel("Pixel Count")
    plt.title("NDVI Change Summary")
    plt.savefig(stats_png, bbox_inches='tight', dpi=300)
    plt.close()

    print(f"✅ NDVI change detection saved to: {output_tif} and {output_png}")
    print(f"📊 Summary: Gain={gain} ({gain_pct}%), Loss={loss} ({loss_pct}%), Neutral={neutral} ({neutral_pct}%)")

    return {
        "gain_pixels": int(gain),
        "loss_pixels": int(loss),
        "neutral_pixels": int(neutral),
        "gain_percent": gain_pct,
        "loss_percent": loss_pct,
        "neutral_percent": neutral_pct,
        "delta_ndvi_tif": output_tif,
        "delta_ndvi_png": output_png,
        "ndvi_stats_chart": stats_png
    }
