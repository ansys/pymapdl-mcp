import base64
import sys
from io import BytesIO, TextIOWrapper

import matplotlib
import matplotlib.pyplot as plt
import pyvista as pv
from PIL import Image

# Set UTF-8 encoding for stdout and stderr to handle Unicode characters
if sys.stdout.encoding != "utf-8":
    sys.stdout = TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
if sys.stderr.encoding != "utf-8":
    sys.stderr = TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

# Use non-interactive backend to prevent blocking on plot displays
matplotlib.use("Agg")

# Enable off-screen rendering globally
pv.OFF_SCREEN = True

# Set a clean default theme
pv.set_plot_theme("document")


def save_plot(plotter: pv.Plotter) -> str:
    """
    Save PyVista plot to file and optionally return as base64.

    Parameters
    ----------
    plotter : pv.Plotter
        The PyVista plotter to save

    Returns
    -------
    str
        File path or base64 data URI
    """
    try:
        # Capture screenshot
        img_array = plotter.screenshot(return_img=True, transparent_background=False)

        # Convert to PIL Image
        img = Image.fromarray(img_array)

        # Save to buffer
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        # Seek to beginning before reading
        buffer.seek(0)

        # Encode to base64
        img_base64 = base64.b64encode(buffer.read()).decode("utf-8")

        # Create data URI
        result = f"data:image/png;base64,{img_base64}"

        # Clean up and return
        plotter.close()
        return result
    except Exception as e:
        plotter.close()
        return f"Error in save_plot: {str(e)}"


def save_matplotlib_plot(dpi=150):
    """
    Return the current Matplotlib plot as a base64-encoded PNG image.

    Parameters
    ----------
    dpi : int
        Resolution in dots per inch

    Returns
    -------
    str
        File path or base64 data URI
    """
    buffer = BytesIO()
    plt.savefig(buffer, format="png", dpi=dpi, bbox_inches="tight")
    buffer.seek(0)

    img_base64 = base64.b64encode(buffer.read()).decode("utf-8")
    result = f"data:image/png;base64,{img_base64}"
    plt.close()
    return result
