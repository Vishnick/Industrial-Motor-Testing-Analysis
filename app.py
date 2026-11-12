"""Industrial Motor Testing & Performance Analysis
Educational portfolio project. Demo data is simulated, not measured equipment data.
"""
from __future__ import annotations
import io, math, random, sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "motor_tests.db"
REQUIRED = ["timestamp", "motor_id", "voltage_v", "current_a", "power_factor", "rpm", "torque_nm", "temperature_c"]

st.set_page_config(page_title="MotorTest | Industrial Analytics", page_icon="⚙️", layout="wide")

# --------------------------- Core calculations ---------------------------
def calculate_performance(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["input_power_w"] = (math.sqrt(3) * out["voltage_v"] * out["current_a"] * out["power_factor"])
    out["output_power_w"] = (2 * math.pi * out["rpm"] * out["torque_nm"] / 60)
    out["efficiency_pct"] = (out["output_power_w"] / out["input_power_w"].replace(0, float("nan"))) * 100
    out["test_result"] = out.apply(classify_row, axis=1)
    return out


def classify_row(row) -> str:
    # Illustrative demo thresholds only. Configure them for a real test standard.
    checks = [
        380 <= row["voltage_v"] <= 440,
        0 < row["current_a"] <= 15,
        0.70 <= row["power_factor"] <= 1.0,
        1200 <= row["rpm"] <= 1800,
        0 < row["torque_nm"] <= 60,
        row["temperature_c"] <= 90,
        0 < row["efficiency_pct"] <= 100,
    ]
    return "PASS" if all(checks) else "REVIEW"


def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS motor_tests (
            id INTEGER PRIMARY KEY AUTOINCREMENT, timestamp TEXT, motor_id TEXT,
            voltage_v REAL, current_a REAL, power_factor REAL, rpm REAL, torque_nm REAL,
            temperature_c REAL, input_power_w REAL, output_power_w REAL,
            efficiency_pct REAL, test_result TEXT, source TEXT)""")


def save_records(df: pd.DataFrame, source: str):
    cols = REQUIRED + ["input_power_w", "output_power_w", "efficiency_pct", "test_result"]
    saved = df[cols].copy()
    saved["source"] = source
    with sqlite3.connect(DB_PATH) as conn:
        saved.to_sql("motor_tests", conn, if_exists="append", index=False)


def load_history() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query("SELECT * FROM motor_tests ORDER BY id DESC", conn)


def make_demo_reading() -> dict:
    # Plausible illustrative values for a small three-phase induction-motor demo.
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "motor_id": "DEMO-3PH-001",
        "voltage_v": round(random.gauss(415, 2.0), 1),
        "current_a": round(random.gauss(5.2, 0.12), 2),
        "power_factor": round(min(0.98, max(0.72, random.gauss(0.86, 0.015))), 2),
        "rpm": int(random.gauss(1440, 5)),
        "torque_nm": round(random.gauss(19.5, 0.35), 2),
        "temperature_c": round(random.gauss(54, 1.0), 1),
    }


init_db()
if "live_data" not in st.session_state:
    st.session_state.live_data = pd.DataFrame(columns=REQUIRED)
if "streaming" not in st.session_state:
    st.session_state.streaming = False

# ------------------------------- Sidebar ---------------------------------
st.sidebar.title("⚙️ MotorTest")
st.sidebar.caption("Industrial motor test & performance analytics")
page = st.sidebar.radio("Workspace", ["Live Monitor", "Test & Analyse", "Test History", "About Project"])
st.sidebar.divider()
st.sidebar.caption("Demo mode: readings are simulated unless you upload or enter measured data.")

st.title("Industrial Motor Testing & Performance Analysis")
st.caption("A portfolio demonstration for motor testing, quality inspection and engineering data analysis.")

if page == "Live Monitor":
    st.subheader("Live motor monitor")
    c1, c2 = st.columns([2, 1])
    with c1:
        st.info("Live demo generates a new illustrative reading every 2 seconds. It is not connected to a physical motor or test bench.")
    with c2:
        if st.session_state.streaming:
            if st.button("⏹ Stop live demo", use_container_width=True):
                st.session_state.streaming = False
                st.rerun()
        else:
            if st.button("▶ Start live demo", use_container_width=True):
                st.session_state.streaming = True
                st.rerun()

    run_every = "2s" if st.session_state.streaming else None
    @st.fragment(run_every=run_every)
    def live_panel():
        if st.session_state.streaming:
            reading = make_demo_reading()
            st.session_state.live_data = pd.concat([st.session_state.live_data, pd.DataFrame([reading])], ignore_index=True).tail(60)
        if st.session_state.live_data.empty:
            st.session_state.live_data = pd.DataFrame([make_demo_reading()])
        calculated = calculate_performance(st.session_state.live_data.copy())
        latest = calculated.iloc[-1]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Line voltage", f"{latest.voltage_v:.1f} V")
        m2.metric("Line current", f"{latest.current_a:.2f} A")
        m3.metric("Speed", f"{latest.rpm:.0f} RPM")
        m4.metric("Efficiency (calculated)", f"{latest.efficiency_pct:.1f}%")
        m5, m6, m7 = st.columns(3)
        m5.metric("Power factor", f"{latest.power_factor:.2f}")
        m6.metric("Temperature", f"{latest.temperature_c:.1f} °C")
        m7.metric("Inspection flag", str(latest.test_result))
        chart = calculated.set_index("timestamp")[["voltage_v", "current_a", "rpm", "temperature_c"]]
        st.line_chart(chart, height=300)
        st.caption(f"Latest update: {latest.timestamp} | Displaying last {len(calculated)} readings")
        if st.session_state.streaming:
            st.caption("Auto-refresh: every 2 seconds")
    live_panel()

elif page == "Test & Analyse":
    st.subheader("Record a motor test")
    tab1, tab2 = st.tabs(["Manual test entry", "Upload CSV readings"])
    with tab1:
        with st.form("manual_test"):
            a, b, c = st.columns(3)
            motor_id = a.text_input("Motor ID", "MOTOR-001")
            voltage = b.number_input("Line voltage (V)", 1.0, 1000.0, 415.0, 1.0)
            current = c.number_input("Line current (A)", 0.01, 1000.0, 5.2, 0.1)
            d, e, f = st.columns(3)
            pf = d.number_input("Power factor", 0.01, 1.0, 0.86, 0.01)
            rpm = e.number_input("Speed (RPM)", 1, 100000, 1440, 10)
            torque = f.number_input("Torque (N·m)", 0.01, 100000.0, 19.5, 0.1)
            temp = st.number_input("Temperature (°C)", -50.0, 300.0, 54.0, 0.5)
            submitted = st.form_submit_button("Calculate and save test", type="primary")
        if submitted:
            raw = pd.DataFrame([{
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "motor_id": motor_id,
                "voltage_v": voltage, "current_a": current, "power_factor": pf,
                "rpm": rpm, "torque_nm": torque, "temperature_c": temp
            }])
            result = calculate_performance(raw)
            save_records(result, "Manual entry")
            st.success("Test calculated and saved to local history.")
            st.dataframe(result[["motor_id", "input_power_w", "output_power_w", "efficiency_pct", "test_result"]], use_container_width=True)
    with tab2:
        st.markdown("Upload a CSV containing: `timestamp, motor_id, voltage_v, current_a, power_factor, rpm, torque_nm, temperature_c`.")
        uploaded = st.file_uploader("Choose motor test CSV", type=["csv"])
        if uploaded is not None:
            try:
                raw = pd.read_csv(uploaded)
                missing = [col for col in REQUIRED if col not in raw.columns]
                if missing:
                    st.error("Missing required columns: " + ", ".join(missing))
                else:
                    for col in REQUIRED[2:]:
                        raw[col] = pd.to_numeric(raw[col], errors="coerce")
                    raw = raw.dropna(subset=REQUIRED[2:])
                    if raw.empty:
                        st.error("No valid numeric readings found.")
                    else:
                        result = calculate_performance(raw)
                        st.dataframe(result, use_container_width=True)
                        if st.button("Save uploaded tests to history"):
                            save_records(result, "CSV upload")
                            st.success(f"Saved {len(result)} records.")
            except Exception as exc:
                st.error(f"Could not read CSV: {exc}")
    st.divider()
    st.subheader("Download sample CSV template")
    sample = pd.read_csv(APP_DIR / "data" / "sample_motor_data.csv")
    st.download_button("Download CSV template", sample.to_csv(index=False).encode("utf-8"), "sample_motor_data.csv", "text/csv")

elif page == "Test History":
    st.subheader("Saved test history")
    history = load_history()
    if history.empty:
        st.info("No saved tests yet. Add a manual test or upload a CSV in Test & Analyse.")
    else:
        total = len(history)
        passed = int((history["test_result"] == "PASS").sum())
        x, y, z = st.columns(3)
        x.metric("Total records", total)
        y.metric("PASS", passed)
        z.metric("REVIEW", total - passed)
        st.dataframe(history, use_container_width=True)
        st.download_button("Export history as CSV", history.to_csv(index=False).encode("utf-8"), "motor_test_history.csv", "text/csv")
        if st.button("Clear local history", type="secondary"):
            with sqlite3.connect(DB_PATH) as conn:
                conn.execute("DELETE FROM motor_tests")
            st.success("Local history cleared.")
            st.rerun()

else:
    st.subheader("Project overview")
    st.markdown("""
**Objective**  
Create a small engineering tool to calculate motor performance, review test readings and retain inspection records.

**Features**
- Automatically refreshed simulated motor readings for a live demonstration.
- Three-phase input power, mechanical output power and efficiency calculations.
- Manual test entry and CSV upload.
- Configurable-in-code illustrative review checks (not a certified acceptance standard).
- SQLite test history and CSV export.

**Technology:** Python, Streamlit, Pandas, SQLite.

**Engineering formulas**
- Three-phase input power: `P_in = √3 × V_line × I_line × power_factor`
- Mechanical output power: `P_out = 2π × RPM × torque / 60`
- Efficiency: `η = (P_out / P_in) × 100`

**Important limitations**
- Live Monitor uses simulated values. Real sensor/controller integration is not included in this starter release.
- Assumes balanced three-phase supply for the input-power formula.
- Efficiency calculation assumes measured shaft torque and speed.
- PASS/REVIEW thresholds are illustrative demo settings. Replace them with approved limits from the relevant motor specification and test procedure before any real inspection use.
- This is an independent student portfolio project and is not based on any manufacturer proprietary data.
""")

st.sidebar.divider()
st.sidebar.caption("Independent educational project")
