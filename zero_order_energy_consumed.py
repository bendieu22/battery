from SoC_0thorder_parameters_link import *
from power_from_WLTP import *
import math
import argparse
import matplotlib.pyplot as plt

def energy_consumption_cell(csv_path, number_series_cells, number_parallel_cells, R0_coefficient, OCV_coefficient, SoC, mass, wind, angle):

    
    soc_dict = OCV_SoC(csv_path)
    SOC_points = []
    #R0 interpolation for discharging
    R0_points = []
    OCV_points = []
    #R0 interpolation for charging
    soc_dict_charging = OCV_SoC(csv_path, True)
    R0_points_charge = []
    for key in soc_dict.keys():
        for tuple_index in range(len(soc_dict[key])):
            SOC_points.append(soc_dict[key][tuple_index][1])
            R0_points.append(soc_dict[key][tuple_index][2])
            OCV_points.append(soc_dict[key][tuple_index][3])
            R0_points_charge.append(soc_dict_charging[key][tuple_index][2])
    SOC_points.sort()
    R0_points.reverse()
    r0_interp =  PchipInterpolator(SOC_points, R0_points)

    R0_points_charge.reverse()
    r0_charge_interp = PchipInterpolator(SOC_points, R0_points_charge)

    #OCV interpolation
    OCV_points.reverse()
    ocv_interp = PchipInterpolator(SOC_points, OCV_points)

    power_demand_dictionary = run_simulation(mass, wind, angle)
    p_batt = power_demand_dictionary["p_batt"]
    distance_demand = power_demand_dictionary["speed_ms"]
    SOC_now = [SoC]
    t_now = 0
    energy_consumed=0
    overall_capacity_cell = number_parallel_cells*overall_capacity(csv_path)
    U_list = []
    I_list = []
    distance_list = [0]
    while SOC_now[-1]>0.1:
        power_demand= p_batt[t_now%1801]
        distance_list.append(distance_demand[t_now%1801]+distance_list[-1])
        ocv_cell = ocv_interp(SOC_now[-1])
        ocv_now = ocv_cell*number_series_cells*OCV_coefficient
        if power_demand<0:
            R0_cell = r0_charge_interp(SOC_now[-1])
            R0_now = (R0_cell*number_series_cells*R0_coefficient)/number_parallel_cells
        else:
            R0_cell = r0_interp(SOC_now[-1])
            R0_now = (R0_cell*number_series_cells*R0_coefficient)/number_parallel_cells
        try:
            I2 = (ocv_now - math.sqrt((ocv_now)**2 - 4*power_demand*R0_now))/(2*R0_now)
        except ValueError:
            print("Math domain error at time ", t_now, " seconds")    
       
        # print("I2 is: " , I2)   

        U2 = power_demand/I2   
        U_list.append(U2) 
        I_list.append(I2)
        # print("U1 is: " , U1)
        # print("U2 is: " , U2)
        energy_consumed += power_demand/3600000
        #print("The energy consumed was ", energy_consumed, " kWh, and the power demanded was ", p_batt[t_now], " W")
        
        new_SOC_2 = SOC_now[-1] - ((I2/3600)/(overall_capacity_cell))*100
        
        
        SOC_now.append(float(new_SOC_2))
        t_now += 1

    t_list = list(range(1,t_now+1))  
    
    
    #print(t_now, energy_consumed,SOC_now[-1])
    return {
        'distance': distance_list,
        'SOC': SOC_now,
        'time': t_list,
        'energyconsumed': energy_consumed,
        'voltages': U_list,
        'Currents': I_list
    }

def plot_distance_SOC(results):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(results["distance"], results["SOC"], color='black', linestyle = 'None', marker=".",markersize=1)
    ax.set_title("SOC over a distance travelled")
    ax.set_xlabel('distance (m)')
    ax.set_ylabel("SOC (%)")
    ax.grid(True)
    return fig
def plot_voltage_time(results):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(results["time"], results["voltages"], color='black', linestyle = 'None', marker=".",markersize=1)
    ax.set_title("voltage over time")
    ax.set_ylabel('voltage (V)')
    ax.set_xlabel("time (s)")
    ax.grid(True)
    return fig
def plot_current_time(results):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(results["time"], results["Currents"], color='black', linestyle = 'None', marker=".", markersize=1)
    ax.set_title("current over time")
    ax.set_ylabel('current (A)')
    ax.set_xlabel("time (s)")
    ax.grid(True)
    return fig

# if __name__ == "__main__":
#     energy_consumption_cell('Cell_data/CELL_E_TEST_00.csv',110,2,1,1,100,1502,0,0)

if __name__ == "__main__":
    # 2. Set up the argument parser
    parser = argparse.ArgumentParser(description="Run Battery Simulation and Select Plot")
    
    # This creates a required argument where you must type one of the choices
    parser.add_argument(
        "plot_type", 
        choices=["current", "voltage", "soc"], 
        help="The type of plot to generate: 'current', 'voltage', or 'soc'"
    )
    parser.add_argument(
        "--file", 
        help="Filename to plot (e.g., CELL_E_TEST_00.csv). If omitted, plots all files in Cell_data folder.",
        default=None
    )
    args = parser.parse_args()
 
    n_series = 110
    n_parallel = 2
    r0_coeff = 1.0
    ocv_coeff = 1.0
    initial_soc = 100
    mass = 1502
    wind = 0
    angle = 0

    print(f"Running simulation to generate {args.plot_type} plot...")
    
    file_path = Path("Cell_data") / args.file

    # 5. Run the simulation (Required for any plot)
    try:
        results = energy_consumption_cell(
            file_path, n_series, n_parallel, r0_coeff, 
            ocv_coeff, initial_soc, mass, wind, angle
        )
    except Exception as e:
        print(f"Error running simulation: {e}")
        exit()

    # 6. Check which option the user chose and run only that plot
    if args.plot_type == "current":
        plot_current_time(results)
    elif args.plot_type == "voltage":
        plot_voltage_time(results)
    elif args.plot_type == "soc":
        plot_distance_SOC(results)

    # 7. Show the chosen plot
    plt.show()