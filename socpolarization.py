import numpy as np
import pandas as pd
from pathlib import Path
from scipy.optimize import curve_fit
import matplotlib.pyplot as plt
import argparse

# ---------------- Parameters ----------------
DATA_FOLDER = "Cell_data"
STEP_VALUE = 9
WINDOW = 1              # samples for ohmic resistance
MIN_CURRENT = 0.01      # avoid division by zero
T_MIN = 16000           # optional start of analysis
T_MAX = 25000           # optional end of analysis

# ---------------- Capacity & SoC functions ----------------
def overall_capacity(csv_path):
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    step_data = df[df["Step"] == 27]
    time_values = step_data["Total Time"].values
    current_values = step_data["Current"].values
    start_time = time_values[0]
    end_time = time_values[-1]
    current = current_values[0]
    return abs(current * (end_time - start_time) / 3600)

def soc_by_spike_single(csv_path):
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    is_step15 = df["Step"] == 15
    block_id = (is_step15 != is_step15.shift()).cumsum()
    step15_df = df[is_step15]
    soc_dict = {0: 100.0}  # start at 100%
    tot_SOC = 100
    for i, (_, block) in enumerate(step15_df.groupby(block_id[is_step15]), 1):
        t_start = block["Total Time"].iloc[0]
        t_end = block["Total Time"].iloc[-1]
        duration = t_end - t_start
        current = block["Current"].iloc[0]
        current_capacity = abs(duration * current / 3600)
        SOC_drop = current_capacity / overall_capacity(csv_path) * 100
        tot_SOC = tot_SOC - SOC_drop
        soc_dict[i] = tot_SOC
    return soc_dict

def soc_df_single(csv_path):
    soc_dict = soc_by_spike_single(csv_path)
    return pd.DataFrame({
        "pulse_id": list(soc_dict.keys()),
        "SoC": list(soc_dict.values())
    })

def soc_df_all(folder_path):
    folder = Path(folder_path)
    rows = []
    for csv_file in sorted(folder.glob("*.csv")):
        df_soc = soc_df_single(csv_file)
        df_soc["file"] = csv_file.stem
        rows.append(df_soc)
    return pd.concat(rows, ignore_index=True)

# ---------------- Extraction function ----------------
def extract_step9_plateaus_fixed_tau(data_folder):
    data_folder = Path(data_folder)
    files = sorted(data_folder.glob("*.csv"))
    results = []

    for file in files: 
        df = pd.read_csv(file)
        df.columns = [c.strip() for c in df.columns]

        # Convert to numeric
        for col in ["Total Time", "Current", "Voltage", "Step"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        # Restrict time window
        df = df[(df["Total Time"] >= T_MIN) & (df["Total Time"] <= T_MAX)].reset_index(drop=True)

        time = df["Total Time"].values
        current = df["Current"].values
        voltage = df["Voltage"].values
        step = df["Step"].values

        # Detect Step=9 starts
        is_step = step == STEP_VALUE
        starts = is_step & (~np.roll(is_step, 1))
        starts[0] = False
        start_indices = np.where(starts)[0]

        # print(f"{file.name}: detected {len(start_indices)} Step={STEP_VALUE} events")

        for idx in start_indices:

            # ---------------- Plateau ----------------
            end_idx = idx
            while end_idx + 1 < len(step) and step[end_idx + 1] == STEP_VALUE:
                end_idx += 1

            if end_idx <= idx + 1:
                continue  # skip too short

            v_plateau = voltage[idx+1:end_idx+1]
            t_plateau = time[idx+1:end_idx+1]
            I_step = current[idx+1]

            if abs(I_step) < MIN_CURRENT or len(v_plateau) < 3:
                continue

            if abs(v_plateau[-1] - v_plateau[0]) < 1e-3:  # 1 mV threshold
                continue

            # ---------------- Tau from 63.2% method ----------------
            delta_V = v_plateau[-1] - v_plateau[0]
            V_tau = v_plateau[0] + 0.632 * delta_V
            V_tau = min(max(V_tau, min(v_plateau)), max(v_plateau))
            tau = np.interp(V_tau, v_plateau, t_plateau) - t_plateau[0]

            # ---------------- Exponential fit with fixed tau ----------------
            def V_exp_fixed_tau(t, V0, a):
                return V0 + a * (1 - np.exp(-t / tau))  # tau fixed

            t_fit = t_plateau - t_plateau[0]
            V_fit = v_plateau

            V0_guess = V_fit[0]
            a_guess = V_fit[-1] - V_fit[0]
            p0 = [V0_guess, a_guess]

            try:
                popt, _ = curve_fit(V_exp_fixed_tau, t_fit, V_fit, p0=p0, maxfev=5000)
                V0_fit, a_fit = popt
                R_pol = a_fit / I_step
            except Exception as e:
                print(f"Step {STEP_VALUE} fit failed: {e}")
                R_pol = np.nan

            C_pol = tau / R_pol if R_pol > 0 else np.nan

            # ---------------- Store ----------------
            results.append({
                "file": file.stem,
                "step_start_time": time[idx],
                "R_pol": R_pol,
                "tau": tau,
                "C_pol": C_pol
            })

    df_results = pd.DataFrame(results, columns=["file", "step_start_time",  "R_pol", "tau", "C_pol"])

    # ---------------- Add pulse index ----------------
    df_results["pulse_id"] = df_results.groupby("file").cumcount().add(1)

    return df_results


    # ---------------- Plot R_pol vs SoC ----------------
def plot_SOC_R1(csv_path, coefficient=1.0):
    """
    cell_name: e.g. 'CELL_E_TEST_01'
    coefficient: scaling factor for R_pol
    """

    csv_path = Path(csv_path) 
    cell_name = csv_path.stem
    if not csv_path.exists():
        raise FileNotFoundError(f"{csv_path} not found")

    # --- run analysis for ONE file ---
    df_results = extract_step9_plateaus_fixed_tau(DATA_FOLDER)
    df_results = df_results[df_results["file"] == cell_name]

    df_soc = soc_df_single(csv_path)

    # pulse index
    df_results = df_results.copy()
    df_results["pulse_id"] = df_results.index + 1

    # merge
    df = pd.merge(df_results, df_soc, on="pulse_id", how="inner")

    if df.empty:
        raise ValueError("No data after merge — check pulse indexing")

    fig, ax = plt.subplots(figsize=(9,6))
    ax.plot(
        df["SoC"],
        df["R_pol"] * coefficient,
        "o-",
        label=f"{cell_name}",
        linestyle = 'None'
    )

    ax.set_xlabel("State of Charge (%)")
    ax.set_ylabel("R_pol (Ω)")
    ax.set_title("Polarization resistance vs SoC")
    ax.invert_xaxis()
    ax.grid(True)
    ax.legend()
    fig.tight_layout()
    return fig

# ---------------- Main Execution ----------------
if __name__ == "__main__":
    
    # 1. Setup Argparse
    parser = argparse.ArgumentParser(description="Plot R1 vs SOC for a specific cell file")
    
    parser.add_argument(
        "--file", 
        required=True, # Force user to provide a file
        help="Path to the cell CSV file (e.g., Cell_data/CELL_E_TEST_00.csv)"
    )

    args = parser.parse_args()
    try:
        plot_SOC_R1(args.file)
        plt.show()
    except Exception as e:
        print(f"Error: {e}")




"""def plot_SOC_C1():
    plt.figure(figsize=(8,5))
    for file in df_merged["file"].unique():
        df_f = df_merged[df_merged["file"] == file]
        plt.plot(df_f["SoC"], df_f["C_pol"], 'o-', label=file)
    plt.xlabel("State of Charge (%)")
    plt.ylabel("C_pol (F)")
    plt.title("Polarization capacitance vs SoC")
    plt.gca().invert_xaxis()
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

# ---------------- Plot tau vs SoC ----------------
def plot_SOC_tau():
    plt.figure(figsize=(8,5))
    for file in df_merged["file"].unique():
        df_f = df_merged[df_merged["file"] == file]
        plt.plot(df_f["SoC"], df_f["tau"], 'o-', label=file)
    plt.xlabel("State of Charge (%)")
    plt.ylabel("Tau (s)")
    plt.title("Time constant vs SoC")
    plt.gca().invert_xaxis()
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.show()

# ---------------- Sample merged table ----------------
print(df_merged.head())"""


