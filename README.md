# Industrial Motor Testing & Performance Analysis

A Python + Streamlit portfolio project for motor test-data capture, performance calculations, basic inspection review, and history export.

## Run locally

1. Install Python 3.10 or newer.
2. Open a terminal in this project folder.
3. Create and activate a virtual environment (recommended).
4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Start the dashboard:

   ```bash
   streamlit run app.py
   ```

6. Streamlit opens the local app in your browser (usually `http://localhost:8501`).

## Features

- Live demo mode with simulated readings refreshing every 2 seconds.
- Manual test entry.
- CSV upload and calculation.
- Three-phase input power, shaft output power, and efficiency calculations.
- SQLite local history and CSV export.

## CSV format

Required columns:

`timestamp,motor_id,voltage_v,current_a,power_factor,rpm,torque_nm,temperature_c`

A sample file is available at `data/sample_motor_data.csv`.

## Calculations

- `P_in = sqrt(3) * V_line * I_line * PF` (balanced three-phase supply)
- `P_out = 2 * pi * RPM * torque / 60`
- `efficiency = (P_out / P_in) * 100`

## Important engineering notes

- The Live Monitor currently generates **simulated demo readings**. It is not connected to physical sensors, a motor test bench, or physical motor equipment.
- Sample readings are illustrative and are not actual manufacturer test data.
- The PASS/REVIEW checks in `app.py` are illustrative demonstration thresholds only. They are not manufacturer specifications, IEC acceptance limits, or a certified quality procedure. Replace them with approved test limits before use in a real test environment.
- The input-power formula assumes a balanced three-phase supply. Efficiency requires valid shaft torque and speed measurements.
- This is an independent educational portfolio project and is not affiliated with any motor manufacturer.

## Suggested next engineering extension

Integrate a properly isolated and calibrated data-acquisition device or PLC gateway, validate sensor scaling, timestamp incoming measurements, and add authentication and audit controls before using the application with real equipment.
