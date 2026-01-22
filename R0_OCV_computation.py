import pandas as pd
from pathlib import Path
import argparse

#This code identifies the internal resistance that is associated with the current spiking down (discharging R0)
#This happens during step 7 of the CSV files where current typically spikes from 0 to -70.4A
#Here we can also use the 0 current point just before that spike up to identify the OCV
#This code also identifies the internal resistance that is associated with the current spiking up (charging R0)
#This happens during step 9 of the CSV files


def identify_R0_OCV(csv_path, charge = False):
    if charge == True:
        list_of_steps = [9]  #This is the only step which we are interested in looking for, for the charging R0
    elif charge == False:
        list_of_steps = [7]
    results = {}  #This will store our final results that we will output, our keys being the file number that the results match to
    #The values stored with that key will be a list, full of tuples, where each tuple represents what we call a pulse, or spike.
    #In the tuple there will also be the corresponding internal resistance and OCV for that spike
    csv_path = Path(csv_path)
    df = pd.read_csv(csv_path)

    # Normalize column names
    df.columns = [c.strip() for c in df.columns]

    #Defining our column names
    time_col = "Total Time" 
    curr_col = "Current"
    volt_col = "Voltage"
    step_col = "Step"

    #Checks that all necessary columns are present
    if not all(c in df.columns for c in [time_col, curr_col, volt_col, step_col]):
        raise ValueError(
            f"{csv_path.name}: Missing one of required columns. Found columns: {df.columns.tolist()}")
    
    #Converts all values to numbers (basically just a safety check)
    df[time_col] = pd.to_numeric(df[time_col], errors="coerce")
    df[curr_col] = pd.to_numeric(df[curr_col], errors="coerce")
    df[volt_col] = pd.to_numeric(df[volt_col], errors="coerce")
    df[step_col] = pd.to_numeric(df[step_col], errors="coerce")
    #Indices in the csv file where spike we're interested in happens
    start_indices=[]
    key = ("file " + csv_path.stem[-1]) #creating key for the results dictionary
    results[key] = []
    for value in list_of_steps:
        is_value = df[step_col].eq(value) #finds where step 9 happens
        prev_is_value = is_value.shift(1, fill_value = False) #checks that at the previous index the step wasnt 9 (so identifies where step switches from not 9 to 9)
        starts = is_value & (~prev_is_value)
        start_indices_value = df.index[starts].tolist() #forms list of our indexes that interest us
        for element in start_indices_value:
            start_indices.append(element)
    start_indices.sort() #useful if list_of_steps has multiple elements, so in this case not strictly neccessary
    idx_dictionary ={}
    for idx in start_indices:
        prev_idx = idx - 1
        if prev_idx not in df.index:
            continue #just a safety net again

        t0 = df.at[idx, time_col] #finds the time at which the step was identified, useful for double checking
        v0 = df.at[idx, volt_col]
        i0 = df.at[idx, curr_col]

        v1 = df.at[prev_idx, volt_col]
        i1 = df.at[prev_idx, curr_col]

        pulse_number = start_indices.index(idx) #0 for first pulse etc..
        if pulse_number not in idx_dictionary.keys():
            idx_dictionary[pulse_number] = [] #creates new list where for each pulse it will add the index that it happens at
        idx_dictionary[pulse_number].append(idx)
        dV = v1 - v0
        dI = i1 - i0
        R = (dV / dI) #calculate internal resistance
        
        OCV_index = idx_dictionary[pulse_number][0] -1 #find the index just before the spike (ie current will be zero)
        
        I_for_OCV = df.at[OCV_index, curr_col] #typically zero but not always the case
        V_for_OCV = df.at[OCV_index, volt_col]
        OCV = V_for_OCV +I_for_OCV*R #current not exactly 0 in file 04, so need to take into account this -0.0.11 value of current
        if abs(dI) > 10: #just a check to verify the current spike is not too small (should never fail this test)
            results[key].append((pulse_number, float(R), float(OCV))) #add the results as a tuple to the list that corresponds to a file
    return results

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
        
        print(identify_R0_OCV(file_path))