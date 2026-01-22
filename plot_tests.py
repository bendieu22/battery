import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
import argparse

#the 5 csv_paths for the five test files are as follows: 
# 'Cell_data/CELL_E_TEST_00.csv' 
# 'Cell_data/CELL_E_TEST_01.csv' 
# 'Cell_data/CELL_E_TEST_02.csv'
# 'Cell_data/CELL_E_TEST_03.csv'
# 'Cell_data/CELL_E_TEST_04.csv'

def plot_file(csv_path):
    csv_path = Path(csv_path)
    #structures our csv file in memory with panda so it is easily accessible
    df = pd.read_csv(csv_path)

    fig, axs = plt.subplots(3, 1, figsize=(9, 6))

    # Voltage vs Time
    axs[0].plot(df["Total Time"],df["Voltage"],linestyle='None',marker='.',markersize=2) #so that plot is only data points, not lines in between
    axs[0].set_xlabel("Total Time (s)")
    axs[0].set_ylabel("Voltage (V)")
    axs[0].set_title("Voltage vs Time")
    axs[0].grid(True)

    # Current vs Time
    axs[1].plot(df["Total Time"],df["Current"],linestyle='None',marker='.', markersize=2)
    axs[1].set_xlabel("Total Time (s)")
    axs[1].set_ylabel("Current (A)")

    #axs[1].set_xlim(3595,3800)
    #axs[1].set_ylim(0,30)
    axs[1].set_title("Current vs Time")
    axs[1].grid(True)

    # --- Steps vs Time (discrete)
    axs[2].plot(df["Total Time"], df["Step"],linestyle='None',marker='.', markersize=2)
    axs[2].set_xlabel("Total Time (s)")
    axs[2].set_ylabel("Step")
    #axs[2].set_xlim(3000,6000)
    axs[2].set_title("Step vs Time")
    axs[2].grid(True)

    fig.suptitle(csv_path.stem)
    fig.tight_layout()
    return fig


#def plot_all_files():
    data_folder = Path("Cell_data")
    files = sorted(data_folder.glob("*.csv"))
    for file in files:
        plot_file(file)

def get_cell_files():
    data_folder = Path("Cell_data")
    files = sorted(data_folder.glob("*.csv"))
    return files


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Plot Cell Data Files")
    
    parser.add_argument(
        "--file", 
        help="Filename to plot (e.g., CELL_E_TEST_00.csv). If omitted, plots all files in Cell_data folder.",
        default=None
    )
    
    args = parser.parse_args()

    if args.file:

        file_path = Path("Cell_data") / args.file
        
        print(f"Plotting {file_path}...")
        plot_file(file_path)

    plt.show()