from SoC_computation import *
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.interpolate import PchipInterpolator
import numpy as np
from R0_OCV_computation import *



def OCV_SoC(csv_path, charge=False) : #Set this as false as default because we are typically interested in this link for discharging
    df = pd.read_csv(csv_path)
    df.columns = [c.strip() for c in df.columns]
    all_list = []
    
    # Get OCV and R0 during a charging spike.
    if charge==True:
        soc_dic = soc_by_spike(csv_path)
        ocv_dic = identify_R0_OCV(csv_path, True)
        cells_dictionary = {'Cell_data/CELL_E_TEST_00.csv': 'file 0', 'Cell_data/CELL_E_TEST_01.csv': 'file 1', 'Cell_data/CELL_E_TEST_02.csv': 'file 2', 'Cell_data/CELL_E_TEST_03.csv': 'file 3', 'Cell_data/CELL_E_TEST_04.csv': 'file 4'}    
        
        for key in ocv_dic.keys() :
            for index_of_tuple in range(len(ocv_dic[key])) :
                all_list.append((soc_dic[key][index_of_tuple][0], float(soc_dic[key][index_of_tuple][1]), ocv_dic[key][index_of_tuple][1], ocv_dic[key][index_of_tuple][2]))
        return {cells_dictionary[str(csv_path)]: all_list}
    
    # Get OCV and R0 during a discharging spike.
    if charge==False:
        soc_dic = soc_by_spike(csv_path)
        ocv_dic = identify_R0_OCV(csv_path)
        cells_dictionary = {'Cell_data/CELL_E_TEST_00.csv': 'file 0', 'Cell_data/CELL_E_TEST_01.csv': 'file 1', 'Cell_data/CELL_E_TEST_02.csv': 'file 2', 'Cell_data/CELL_E_TEST_03.csv': 'file 3', 'Cell_data/CELL_E_TEST_04.csv': 'file 4'}    
        
        for key in ocv_dic.keys() :
            for index_of_tuple in range(len(ocv_dic[key])) :
                all_list.append((soc_dic[key][index_of_tuple][0], float(soc_dic[key][index_of_tuple][1]), ocv_dic[key][index_of_tuple][1], ocv_dic[key][index_of_tuple][2]))
        return {cells_dictionary[str(csv_path)]: all_list}


# Plot OCV vs SoC for charge points and discharge points on the same axes.
def plot_OCV_SOC(csv_path, OCV_multiplier):
    ocv_soc_link_charge = OCV_SoC(csv_path, True)
    ocv_soc_link_discharge = OCV_SoC(csv_path)

    csv_path = Path(csv_path)

    fig, ax = plt.subplots(figsize=(9, 6))

    # Charge data
    for key in ocv_soc_link_charge.keys():
        for tuple_index in range(len(ocv_soc_link_charge[key])):
            ax.plot(
                ocv_soc_link_charge[key][tuple_index][1],
                ocv_soc_link_charge[key][tuple_index][3]*OCV_multiplier,
                linestyle='None',
                marker='o',
                markersize=5,
                color='tab:blue',
                label='Charge'  
            )

    # Discharge data
    for key in ocv_soc_link_discharge.keys():
        for tuple_index in range(len(ocv_soc_link_discharge[key])):
            ax.plot(
                ocv_soc_link_discharge[key][tuple_index][1],
                ocv_soc_link_discharge[key][tuple_index][3]*OCV_multiplier,
                linestyle='None',
                marker='o',
                markersize=5,
                color='tab:red',
                label='Discharge' 
            )

    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys())

    ax.set_xlabel("SoC (%)")
    ax.set_ylabel("Open Circuit Voltage (V)")
    ax.set_title("OCV vs SoC (Charge vs Discharge)")
    ax.grid(True)

    plt.show()

# Plot R0 vs SoC for charge points and discharge points.
def plot_R0_SOC(csv_path, R0_multiplier):
    
    ocv_soc_link_charge = OCV_SoC(csv_path, True)
    ocv_soc_link_discharge = OCV_SoC(csv_path)

    csv_path = Path(csv_path)

    fig, ax = plt.subplots(figsize=(9, 6))

    # Charge data
    for key in ocv_soc_link_charge.keys():
        for tuple_index in range(len(ocv_soc_link_charge[key])):
            ax.plot(
                ocv_soc_link_charge[key][tuple_index][1],
                ocv_soc_link_charge[key][tuple_index][2]*R0_multiplier,
                linestyle='None',
                marker='o',
                markersize=5,
                color='tab:blue',
                label='Charge' 
            )

    # Discharge data
    for key in ocv_soc_link_discharge.keys():
        for tuple_index in range(len(ocv_soc_link_discharge[key])):
            ax.plot(
                ocv_soc_link_discharge[key][tuple_index][1],
                ocv_soc_link_discharge[key][tuple_index][2]*R0_multiplier,
                linestyle='None',
                marker='o',
                markersize=5,
                color='tab:red',
                label='Discharge' 
            )

    handles, labels = ax.get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    ax.legend(by_label.values(), by_label.keys())

    ax.set_xlabel("SoC (%)")
    ax.set_ylabel("Internal Resistance (Ohms)")
    ax.set_title("R0 vs SoC (Charge vs Discharge)")
    ax.grid(True)

    plt.show()
    

# Interpolate OCV as a function of SoC using a shape-preserving cubic interpolator (PCHIP).
def interpolate_ocv(csv_path, ocv_query, charge=False):
    ocv_soc_dict = OCV_SoC(csv_path, charge)
    SOC_points = []
    OCV_points = []
    for key in ocv_soc_dict.keys():
        for tuple_index in range(len(ocv_soc_dict[key])):
            SOC_points.append(ocv_soc_dict[key][tuple_index][1])
            OCV_points.append(ocv_soc_dict[key][tuple_index][3])
    SOC_points.sort()
    OCV_points.reverse()
    ocv_interp = PchipInterpolator(SOC_points, OCV_points)
    return ocv_interp(ocv_query)

# Interpolate R0 as a function of SoC using a shape-preserving cubic interpolator (PCHIP).
def interpolate_R0(csv_path, R0_query, charge = False):
    R0_soc_dict = OCV_SoC(csv_path, charge)
    SOC_points = []
    R0_points = []
    for key in R0_soc_dict.keys():
        for tuple_index in range(len(R0_soc_dict[key])):
            SOC_points.append(R0_soc_dict[key][tuple_index][1])
            R0_points.append(R0_soc_dict[key][tuple_index][2])
    SOC_points.sort()
    R0_points.reverse()
    r0_interp =  PchipInterpolator(SOC_points, R0_points)
    return r0_interp(R0_query)


# Evaluate the interpolated OCV vs SoC over many SoC values (0–100%) and plot the resulting curve.
def plot_ocv_soc_full_link(csv_path, OCV_multiplier,charge = False):
    soc_points = np.linspace(0,100,100)
    ocv_points = []
    for point in soc_points:
        ocv_points.append(interpolate_ocv(csv_path, point, charge)*OCV_multiplier)
    plt.plot(soc_points,ocv_points, linestyle = "None", marker = ".")
    plt.show()
    
# Evaluate the interpolated R0 for discharge vs SoC over many SoC values (0–100%) and plot the resulting curve.
def plot_R0_soc_full_link(csv_path, R0_multiplier, charge = False):
    soc_points = np.linspace(0,100,100)
    R0_points = []
    for point in soc_points:
        R0_points.append(interpolate_R0(csv_path, point, charge)*R0_multiplier)
    plt.plot(soc_points,R0_points, linestyle = "None", marker = ".")
    plt.show()

if __name__ == "__main__":
    plot_R0_soc_full_link('Cell_data/CELL_E_TEST_04.csv',1)
