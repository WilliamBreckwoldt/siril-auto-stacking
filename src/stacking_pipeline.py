"""
stacking_pipeline.py

This script processes and stacks astrophotography frames in batches using pySiril.
It ensures that disk space is not overwhelmed by limiting the number of registered/calibrated
frames stored at any given time.
"""

import shutil
import importlib
from pathlib import Path
from datetime import datetime
from pysiril.siril import Siril

from . import constants as c

importlib.reload(c)


def run_pipeline(master_flat, master_dark, lights_dir, partial_dir, final_dir):
    """
    Main function to process batches of light frames, create partial stacks,
    and then combine them into a final master stack.
    """
    # Convert string paths to absolute Path objects and use forward slashes for Siril CLI safety
    master_flat_path = Path(master_flat).absolute().as_posix()
    master_dark_path = Path(master_dark).absolute().as_posix()
    lights_path = Path(lights_dir).absolute()
    partial_path = Path(partial_dir).absolute()
    final_path = Path(final_dir).absolute()

    # Clear out any existing partial stacks to ensure a clean workspace
    if partial_path.exists():
        # You could shutil.rmtree(partial_path), but it may not work if that folder is open in
        # file explorer. Instead we will delete all the partials individually
        for item in partial_path.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

    # Ensure output directories exist
    partial_path.mkdir(parents=True, exist_ok=True)
    final_path.mkdir(parents=True, exist_ok=True)

    # Initialize pySiril application interface
    app = Siril()

    # Mute the background log stream if VERBOSE is False
    if not c.VERBOSE:
        app.tr.MuteSiril(True)

    try:
        # Open connection to the Siril backend
        app.Open()

        # Grab a list of all raw/FITS light frames from the lights directory
        valid_extensions = (".fit", ".fits", ".orf", ".cr2", ".nef", ".arw")
        light_files = [
            f
            for f in lights_path.iterdir()
            if f.suffix.lower() in valid_extensions
        ]
        light_files.sort()

        if not light_files:
            print(
                "No light frames found in the specified directory. Please check your paths."
            )
            return

        total_files = len(light_files)
        print(
            f"Found {total_files} light frames. Processing in batches of {c.BATCH_SIZE}..."
        )

        # We will create a temporary working directory to store the intermediate
        # converted, calibrated, and registered files for each batch to save disk space.
        work_dir = partial_path / "temp_work"
        if work_dir.exists():
            shutil.rmtree(work_dir)
        work_dir.mkdir()

        # ==========================================
        # STEP 1: PROCESS LIGHTS IN BATCHES
        # ==========================================
        batch_count = 0
        for i in range(0, total_files, c.BATCH_SIZE):
            batch_count += 1
            batch_files = light_files[i : i + c.BATCH_SIZE]
            print(
                f"\n--- Processing Batch {batch_count} ({len(batch_files)} frames) ---"
            )

            # Clear the work directory for the new batch to save disk space
            for f in work_dir.iterdir():
                if f.is_file():
                    f.unlink()
                elif f.is_dir():
                    shutil.rmtree(f)

            # Copy batch files to the working directory so Siril can find them locally
            for f in batch_files:
                shutil.copy2(f, work_dir / f.name)

            # Instruct Siril to move into the working directory
            app.Execute(f'cd "{work_dir.as_posix()}"')

            # 1a. Convert RAW to FITS.
            print("Converting frames...")
            app.Execute("convert lights -out=.")

            # 1b. Calibrate
            print("Calibrating frames...")
            # CRITICAL: If using Drizzle, the sequence must NOT be debayered here.
            # Drizzle requires the raw CFA data and handles debayering on the fly.
            debayer_flag = "" if c.USE_DRIZZLE else "-debayer"
            cal_cmd = (
                f'calibrate lights "-dark={master_dark_path}" "-flat={master_flat_path}" '
                f"-cfa -equalize_cfa -cc=dark {c.COLD_SIGMA} {c.HOT_SIGMA} {debayer_flag}"
            )
            app.Execute(cal_cmd)

            # 1c. Register
            print("Registering frames...")
            app.Execute("register pp_lights -2pass")

            # Move the filter HERE. This prevents bad frames from ever being exported.
            filter_str = f"-filter-fwhm={c.MAX_FWHM}"

            if c.USE_DRIZZLE:
                print(
                    f"Applying Drizzle Filtered (Scale: {c.DRIZZLE_SCALE}, Pixfrac: {c.PIXFRAC})..."
                )
                # We add the filter_str here
                drizzle_cmd = (
                    f"seqapplyreg pp_lights -framing=max {filter_str} "
                    f"-drizzle -scale={c.DRIZZLE_SCALE} -pixfrac={c.PIXFRAC} -kernel={c.DRIZZLE_KERNEL}"
                )
                app.Execute(drizzle_cmd)
            else:
                print(f"Applying Filtered Registration (FWHM {c.MAX_FWHM})...")
                app.Execute(f"seqapplyreg pp_lights -framing=max {filter_str}")

            # 1d. Stack Partial Batch
            print("Stacking batch...")
            partial_stack_name = f"partial_stack_{batch_count}"
            partial_stack_file = partial_path / partial_stack_name

            # Fixed the stack command syntax based on documentation
            stack_cmd = (
                f"stack r_pp_lights rej winsorized {c.SIGMA_LOW} {c.SIGMA_HIGH} "
                f"-norm=addscale -weight=wfwhm "
                f'"-out={partial_stack_file.as_posix()}" '
                f"-output_norm -rgb_equal -32b"
            )
            app.Execute(stack_cmd)
            print(
                f"Batch {batch_count} completed. Saved partial stack: {partial_stack_name}.fit"
            )

        # ==========================================
        # STEP 2: STACK ALL PARTIALS INTO FINAL
        # ==========================================
        print("\n--- Processing Final Master Stack ---")
        app.Execute(f'cd "{partial_path.as_posix()}"')

        # Convert partial stacks into a new "partials.seq" sequence
        app.Execute("convert partials -out=.")

        # Because each partial stack was registered locally to its own batch,
        # we now need to register the partial stacks to each other.
        print("Registering partial stacks...")
        app.Execute("register partials -2pass")
        app.Execute("seqapplyreg partials -framing=max")

        # Final Stack
        # Generate a timestamp (e.g., 20260428-085730) to prevent overwrites
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        final_stack_file = final_path / f"final_master_stack_{timestamp}"

        print("Stacking final image...")
        final_stack_cmd = (
            f"stack r_partials rej winsorized {c.SIGMA_LOW} {c.SIGMA_HIGH} "
            f"-norm=addscale "
            f'-weight=nbstack "-out={final_stack_file.as_posix()}" '
            f"-output_norm -rgb_equal -32b"
        )
        app.Execute(final_stack_cmd)

        print(
            f"\nPipeline complete! Final stack safely written to: {final_stack_file.name}.fit"
        )

    except Exception as e:
        print(f"An error occurred during Siril execution: {e}")
    finally:
        # Cleanly shut down the background Siril daemon
        app.Close()
        # Automatically clean up the last batch of intermediate files to recover disk space
        if "work_dir" in locals() and work_dir.exists():
            shutil.rmtree(work_dir)
