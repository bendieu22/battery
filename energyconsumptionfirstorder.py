from SoC_0thorder_parameters_link import *
from power_from_WLTP import *
import math
from pathlib import Path
from scipy.interpolate import PchipInterpolator
from socpolarization import (
    overall_capacity,
    soc_df_single,
    extract_step9_plateaus_fixed_tau,
)

#R0_coeff, OCV_coeff, R1_coeff used in GUI to test sensitivity 
def energy_consumption_cell(csv_path, number_series_cells, number_parallel_cells, R0_coefficient, R1_coefficient, OCV_coefficient,SOC, mass, wind, angle_theta):

    #R0 interpolation 
    soc_dict = OCV_SoC(csv_path) # the function OCV_SOC builds a list of tuples like (time_or_step_index, SOC%, R0, OCV) 
    SOC_points = []
    R0_points = []
    OCV_points = []
    for key in soc_dict.keys(): #loop extracts three arrays:SOC values, R0 values, OCV values
        for tuple_index in range(len(soc_dict[key])): 
            SOC_points.append(soc_dict[key][tuple_index][1]) #element [1] of tuple = SO
            R0_points.append(soc_dict[key][tuple_index][2])
            OCV_points.append(soc_dict[key][tuple_index][3])
    SOC_points.sort() #interpolator expects x-values ordered
    R0_points.reverse() #make R0 line up with sorted SOC
    r0_interp =  PchipInterpolator(SOC_points, R0_points) #R0 is available for any SOC during simulation.

    #OCV interpolation 
    OCV_points.reverse()
    ocv_interp = PchipInterpolator(SOC_points, OCV_points)

    df_results = extract_step9_plateaus_fixed_tau("Cell_data") # Extract polarization params from Step 9 plateaus for each file
    this_file = Path(csv_path).stem #Cell_data/CELL_E_TEST_00.csv" to "CELL_E_TEST_00. match the file name used in df_results["file"].
    df_results = df_results[df_results["file"] == this_file].copy() #only use Step 9 pulses from the chosen cell file.

    # SOC pulses for THIS file
    df_soc = soc_df_single(csv_path) #returns a DataFrame with pulse_id and SoC.
    df_soc["file"] = this_file #add a column "file" with the filename in order to merge by ["file", "pulse_id"].

    df_merged = df_results.merge(df_soc, on=["file", "pulse_id"], how="inner") # each pulse has: SoC (from Step 15 coulomb counting) R_pol and tau (from Step 9 exponential behavior)

    if df_merged.empty:
        raise ValueError(
            f"Empty merge for file '{this_file}'. "
            f"Step=9 pulses and Step=15 pulses may not align by pulse_id."
        )

    df_merged = df_merged.dropna(subset=["SoC", "R_pol", "tau"]).sort_values("SoC") #removes any row where SoC, R_pol, or tau is NaN
    # PCHIP needs strictly increasing x; group duplicates
    df_merged = df_merged.groupby("SoC", as_index=False).median(numeric_only=True) #Combine duplicate SOC values (so x is strictly increasing)

    r1_interp = PchipInterpolator(df_merged["SoC"].values, df_merged["R_pol"].values, extrapolate=True)
    tau_interp = PchipInterpolator(df_merged["SoC"].values, df_merged["tau"].values, extrapolate=True)
    # ------------------------------------------------------------------------

    power_demand_dictionary = run_simulation(mass, angle_theta, wind ) #run_simulation outputs p_batt which we need to use to compute energy 
    p_batt = power_demand_dictionary["p_batt"]
    distance_demand = power_demand_dictionary["speed_ms"]
    SOC_now = [SOC]
    t_now = 0
    energy_consumed=0
    overall_capacity_cell = number_parallel_cells*overall_capacity(csv_path) # in parrallel you have to multiply, series doesnt change
    U_list = []
    I_list = []
    distance_list = [0]

    # --------- NEW: polarization state ----------
    V1 = 0.0
    dt = 1.0
    # ------------------------------------------

    while SOC_now[-1]>5: #SOC never reaches 0
        power_demand= p_batt[t_now%1801]
        distance_list.append(distance_demand[t_now%1801]+distance_list[-1]) #add speed to previous distance, dt=1, so distance += speed*1s

        ocv_cell = ocv_interp(SOC_now[-1])
        ocv_now = ocv_cell*number_series_cells*OCV_coefficient

        R0_cell = r0_interp(SOC_now[-1])
        R0_now = (R0_cell*number_series_cells*R0_coefficient)/number_parallel_cells

        R1_cell = float(r1_interp(SOC_now[-1]))
        tau_now = float(tau_interp(SOC_now[-1])) #tau is not impacted by series or parallel
        R1_now = (R1_cell*number_series_cells*R1_coefficient)/number_parallel_cells

        ocv_eff = ocv_now - V1  #simplify equation OCVeff = OCV - V1 since in quadratic equation there is R0​I^2−(OCV−V1​)I+P=0
        try:
            I2 = (ocv_eff - math.sqrt((ocv_eff)**2 - 4*power_demand*R0_now))/(2*R0_now)
        except ValueError: # discriminant became negative → demanded power is impossible at that SOC.
            print("Math domain error at time ", t_now, " seconds")
            break

        U2 = ocv_now - I2*R0_now - V1

        U_list.append(U2)
        I_list.append(I2)

        energy_consumed += power_demand/3600000

        new_SOC_2= SOC_now[-1] - ((I2/3600)/(overall_capacity_cell))*100 #update the SOC value 
        SOC_now.append(float(new_SOC_2))

        alpha = math.exp(-dt/tau_now) if tau_now > 0 else 0.0
        V1 = V1*alpha + I2*R1_now*(1-alpha) #Update polarization voltage (have to take the last polvoltage into account and assume constant for one second)

        t_now += 1
        
        

    t_list = list(range(1,t_now+1))
    # fig, ax = plt.subplots(figsize = (10,4))
    # ax.plot(t_list, U_list)
    # ax.grid(True)
    # plt.show()
    return t_now, energy_consumed, SOC_now[-1]

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
        
        print(energy_consumption_cell(file_path, 110, 2, 1, 1, 1, 100, 0, 0, 0))


