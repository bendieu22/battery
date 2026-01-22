from SoC_computation import *
from pathlib import Path
from zero_order_energy_consumed import *
import numpy as np
from scipy.interpolate import PchipInterpolator

cell_data_dir = Path("Cell_data")
cell_files = list(cell_data_dir.glob("*.csv"))
cell_files.sort()


def SoH_by_cell():
    capacity_brandnew_cell = overall_capacity("Cell_data/CELL_E_TEST_00.csv")
    SoH_dictionary = {}
    for file in cell_files: 
        capacity_required_cell = overall_capacity(file)
        SoH_dictionary[str(file)] = float((capacity_required_cell/capacity_brandnew_cell)*100)
    return SoH_dictionary

def range_of_car_with_SoH():
    range_for_SoH = {}
    SoH_dictionary = SoH_by_cell()
    for file in cell_files:
        energy_consumption_dict = energy_consumption_cell(file, 110, 2, 1, 1, 100, 1502, 0, 0)
        range_for_SoH[SoH_dictionary[str(file)]] = float(energy_consumption_dict['distance'][-1])
    return range_for_SoH

def plot_range_against_soh():
    range_for_SoH = range_of_car_with_SoH()
    SoH_points = []
    range_points = []
    for key in range_for_SoH.keys():
        SoH_points.append(key)
        range_points.append(range_for_SoH[key])
    SoH_points.reverse()
    range_points.reverse()

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.plot(SoH_points, range_points, linestyle="None", marker="o")
    ax.set_xlabel("State of Health (%)")
    ax.set_ylabel("Range of Pack(m)")
    ax.set_title("Range vs SoH")
    ax.grid(True)
    fig.tight_layout()
    return fig



if __name__ == "__main__":
    fig = plot_range_against_soh()
    plt.show()
    