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
BATCH_SIZE = 200

# ==========================================
# FILTERING & REJECTION SETTINGS
# ==========================================
# The maximum Full Width at Half Maximum (FWHM) value allowed for a frame.
# Frames with an FWHM higher than this value (indicating bloated or blurry
# stars often due to bad seeing or tracking errors) will be rejected
# and excluded from the final stack.
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
