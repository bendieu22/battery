import pandas as pd
import numpy as np
from pathlib import Path
import argparse

# Get the SoC before each spike of current, assuming it is at 100% before the first one. 

# Allows us to find the overall capacity of the cell.
def overall_capacity(csv_path) :
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    
    # Step 27 is where we consider a full discharge, the current is constant.
    step_data = df[df["Step"] == 27]
    time_values = step_data["Total Time"].values
    current_values = step_data["Current"].values

    start_time = time_values[0]
    end_time = time_values[-1]
    current = current_values[0] 
    overall_capacity = abs(current * (end_time - start_time) / 3600) # Divide by 3600 to get the value in Ah.
    
    return overall_capacity

# Determine the SoC at each spike.
def soc_by_spike(csv_path) :
    df = pd.read_csv(csv_path)
    #csv_path = Path(csv_path)
    df.columns = [c.strip() for c in df.columns]
    
    # Step 15 is the step where we have a constant current right after each spike.
    # We update the SoC once per continuous Step 15 block.
    is_step15 = df["Step"] == 15
    block_id = (is_step15 != is_step15.shift()).cumsum()
    step15_df = df[is_step15]
    
    # Assume that before the first spike, the SoC is 100%.
    soc_list = [(0, 100.0)]
    tot_SOC = 100.0
    
    # Used only to label the output (csv_path as a key).
    cells_dictionary = {'Cell_data/CELL_E_TEST_00.csv': 'file 0', 'Cell_data/CELL_E_TEST_01.csv': 'file 1', 'Cell_data/CELL_E_TEST_02.csv': 'file 2', 'Cell_data/CELL_E_TEST_03.csv': 'file 3', 'Cell_data/CELL_E_TEST_04.csv': 'file 4'}
    
    # For each Step 15 block, compute the difference in charge and the drop in SoC.
    for i, (_, block) in enumerate(step15_df.groupby(block_id[is_step15]), 1):
        t_start = block["Total Time"].iloc[0]
        t_end = block["Total Time"].iloc[-1]
        duration = t_end - t_start
        current = block["Current"].iloc[0]
        
        # Calculate the capacity at the spike (in Ah).
        current_capacity = abs(duration * current / 3600)
        # Determine the SoC drop between each spike (in %).
        SOC_drop = current_capacity / overall_capacity(csv_path) * 100
        
        # Get a list of : (spike, SoC at that spike)
        tot_SOC = float(tot_SOC - SOC_drop)
        soc_list.append((i, tot_SOC))
        
    return {cells_dictionary[str(csv_path)]: soc_list}

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
        
        print(soc_by_spike(file_path))