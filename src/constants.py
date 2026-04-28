"""
constants.py

This file contains the configurable limits and settings for the astrophotography
stacking pipeline. Keeping these values here allows novice users to easily
tweak them without needing to modify the complex pipeline logic.
"""

# ==========================================
# BATCH PROCESSING SETTINGS
# ==========================================
# The maximum number of light frames to process in a single batch.
# Processing in batches saves disk space, because intermediate files
# (converted, calibrated, registered) require massive storage.
# The pipeline will delete these intermediate files after each batch completes.
BATCH_SIZE = 305

# ==========================================
# FILTERING & REJECTION SETTINGS
# ==========================================
# If you provide a number (e.g., 4.0), Siril filters by absolute star size in pixels.
# If you provide a percentage string (e.g., "80%"), Siril keeps the best 80%
# of frames in each batch and throws away the worst 20%.
MAX_FWHM = 4.0

# ==========================================
# CALIBRATION SETTINGS
# ==========================================
# Hot and cold pixel sigma values for cosmetic correction during calibration.
# This helps remove defective pixels (hot/cold) using the master dark.
HOT_SIGMA = 3.0
COLD_SIGMA = 3.0

# ==========================================
# STACKING SETTINGS
# ==========================================
# Sigma clipping values for stacking.
# Winsorized sigma clipping rejects extreme pixel values (like satellite trails)
# that are this many standard deviations (sigma) away from the average.
SIGMA_LOW = 3.0
SIGMA_HIGH = 3.0

# ==========================================
# DRIZZLE SETTINGS
# ==========================================
# Enable or disable HST Drizzle during registration.
# Best used for undersampled images with plenty of dithering.
USE_DRIZZLE = True

# Drizzle scale (e.g., 2.0 doubles the image dimensions).
# If you only want to reduce CFA artifacts without upscaling, use 1.0.
DRIZZLE_SCALE = 2.0

# PIXFRAC (Pixel Fraction): Controls the size of the 'droplet' (0.1 to 1.0).
# - 1.0: Default. Safest for low frame counts.
# - 0.7 to 0.8: Recommended sweet spot for sharpening stars without adding noise.
# - < 0.6: Sharper stars, but requires many frames/dithers to avoid background artifacts.
PIXFRAC = 0.7

# DRIZZLE KERNEL: The shape of the droplet mapped to the high-res grid.
# Options: 'point', 'turbo', 'square', 'gaussian', 'lanczos2', 'lanczos3'
# - 'square': Standard HST algorithm; best balance of sharpness and smoothness.
# - 'gaussian': Slightly smoother background if 'square' looks too gritty.
DRIZZLE_KERNEL = "square"

# ==========================================
# LOGGING SETTINGS
# ==========================================
# Set to True to see the full Siril log stream, or False for a quiet console.
VERBOSE = True

# ==========================================
# ESTIMATING SIZE
# ==========================================
# All in MB
RAW_SIZE = 20.7
CONVERTED_SIZE = 40.6
CALIBRATED_SIZE = 81.2
REGISTERED_SIZE = 977
STACK_SIZE = 1024
