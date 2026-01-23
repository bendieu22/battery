# Data and Modelling Weeks Git Repository README

## Overview

The Git Repository that you have been given access to includes our source code for the 2026 Data and Modelling Weeks EDF project. This code was used in order to respond to the problem given to us initially, which was to design a battery pack for an EV model of our choice (with a corresponding range), using the cell data given to us. The following README will detail how you can use the code that we wrote in order to design our battery pack.

---

## Git Repository Content

- **`README.md`
    This is the file that details how to use the Git repository.

- **`Cell_data/`**
    The folder containing the experimental data that we were given.

- **`plot_tests.py`**
    Our code to plot the cell data.

- **`WLTC_data.csv`**
    The WLTP speed profile data.

- **`power_from_WLTP.py`**
Our code to study this data with our car model.

- **`R0_OCV_computation.py`**
    Our code to compute the internal resistance (R0) and open circuit voltage (OCV) at specific current jumps.

- **`SoC_computation.py`**
Our code to calculate the state of charge (SoC) of a specific cell data file, and extract the SoC before certain current jumps in the test files.

- **`SoC_0thorder_parameters_link.py`**
Our code to link the Zeroth-order model parameters (OCV and R0 for charge and discharge) to the Soc.

- **`zero_order_energy_consumed.py`**
Our code to calculate the range and energy consumption of our car for the Zeroth-order circuit model.

- **`socpolarization.py`**
Our code to calculate the First-order model parameters (R1, C1 and Tau) and link them to the SoC.

- **`energyconsumptionfirstorder.py`**
Our code to calculate the range and energy consumption of our car for the First-order model.

- **`SoH_degradation.py`**
Our code to study how the range of the car evolves with a degrading SoH.

- **`GUI.py`**
Our code that implements the Graphical User Interface.


---

## How to use the repository

This following section will describe how to use the python files in the Repository.
All commands below should be run from the terminal in the **root directory** of the project, using the instructions given.

For every instruction, we will write python and python3.
On macOS/Linux use python3, on Windows use python.

If at any point it is unclear what functions and/or arguments can be run in a file, writing the following in your terminal will allow you to see the options available:
```bash
python script_name.py -help
```
```bash
python3 script_name.py -help
```
Whenever a specific cell data file name must be called as an argument for a python script, it must be passed using the `--file` argument. The file must be located in the `Cell_data/` folder. For the first file it should therefore look like this: `--file CELL_E_TEST_00.csv`

---

## Python scripts

### `plot_tests.py` 
This script is used to plot the cell data in a specific file located in the `Cell_data/` folder.

To run, for example for the first file:
```bash
python plot_tests.py --file CELL_E_TEST_00.csv
```
```bash
python3 plot_tests.py --file CELL_E_TEST_00.csv
```

### `power_from_WLTP.py`
This script calculates all the parameters that we can extract from the WLTP, taking into account the forces in our car model. It then uses this data to plot multiple graphs.

The script requires **one positional argument** called `plot_type`, which selects the plot to display.

Valid options are:
- `speed` — WLTP speed profile
- `total` — WLTP Power demand taking all possible forces into account
- `mechanical` — Mechanical power of driveshaft
- `battery` — Battery power demand
- `components` — Plots two Power curves on the same graph. "WLTP forces" includes only the car's acceleration and rolling resistance, while "Total Forces" includes all possible forces that can be added to the code (aerodymic drag and a slope).

To run:
``` bash
python power_from_WLTP.py speed
```
```bash
python3 power_from_WLTP.py speed
```

Should you wish the change the mass of the car, wind speed or angle of slope that the car is on, this can be done in line 151 of the file or in the GUI.

### `R0_OCV_computation.py`

This script computes the **open circuit voltage (OCV)** and **internal resistance (R0)** from experimental cell data files by analyzing current jumps, both for discharging current jumps and charging current jumps. It then outputs a dictionary with as key the file number ('file 0' for `CELL_E_TEST_00.csv`), and as corresponding value a list full of tuples. Each tuple represents a certain current jump, followed by its corresponding R0 and then OCV computed during the jump and just before it respectively. 

To run:
```bash
python R0_OCV_computation.py --file CELL_E_TEST_00.csv
```
```bash
python3 R0_OCV_computation.py --file CELL_E_TEST_00.csv
```

### `SoC_computation.py`

This script computes the overall capacity of each cell, as well as state of charge identified just before each of the current jumps where R0 and OCV are calculated in the previous script. It does this by evaluating the decrease in capacity from constant discharging currents between current jumps, and relating that to the overall capacity of the cell. Again it outputs a dictionary with as key the file number ('file 0' for `CELL_E_TEST_00.csv`), and as corresponding value a list full of tuples. Each tuple represents a certain current jump, followed by the corresponding SoC just before that jump.

To run:
```bash
python SoC_computation.py --file CELL_E_TEST_00.csv
```
```bash
python3 SoC_computation.py --file CELL_E_TEST_00.csv
```

### `SoC_0thorder_parameters_link.py`

This script plots **open-circuit voltage (OCV)** and **internal resistance (R0)** as functions of the **state of charge (SoC)**, either as raw data points or as interpolated curves. It does this by linking the results of the two previous scripts into a single dictionary.

#### Required arguments

- **`plot_type`** : selects the type of plot to display  
  Valid options:
  - `OCV_points` — OCV vs SoC (raw extracted points)
  - `R0_points` — R0 for charging and discharging current jumps vs SoC (raw extracted points)
  - `OCV_full` — OCV vs SoC (interpolated curve)
  - `R0_full` — R0 vs SoC (interpolated curve)

- **`--file`** : path to the cell CSV file  
  Example: `Cell_data/CELL_E_TEST_04.csv`

#### Optional arguments

- **`--mult`**: multiplier applied to OCV or R0 values  
  Default value: `1.0`

Examples to run:
```bash 
python SoC_0thorder_parameters_link.py OCV_points --file CELL_E_TEST_04.csv
```
```bash
python3 SoC_0thorder_parameters_link.py OCV_points --file CELL_E_TEST_04.csv
```

```bash
python SoC_0thorder_parameters_link.py OCV_full --file CELL_E_TEST_04.csv --mult 1.1
```
```bash
python3 SoC_0thorder_parameters_link.py OCV_full --file CELL_E_TEST_04.csv --mult 1.1
```

### `zero_order_energy_consumed.py`

This script runs a **battery energy consumption simulation** using the **zeroth-order equivalent circuit model** and generates a selected plot based on your choice. It does this by using an iterative model where at each second it extracts the power demand of the WLTP, computes the cell's ECM parameters from the SoC, and therefore finds a current and voltage that matches that power demand. It then also enables this to be scaled for a battery pack with any number of cells in series and parallel. These, and other parameters like an R0 coefficient, OCV coefficient, initial SoC, and car parameters, can be changed on line 133 of the code, or in the GUI. This enabled us to find the battery pack necessary for our car to last for our desired 300 km range.

#### Required arguments

- **`plot_type`**: selects the type of plot to generate  
  Valid options:
  - `current` — battery current as a function of time
  - `voltage` — battery terminal voltage as a function of time
  - `soc` — state of charge (SoC) as a function of distance

The name of the test CSV file to use must also be added as usual.

To run:
```bash
python zero_order_energy_consumed.py current --file CELL_E_TEST_00.csv
```
```bash
python3 zero_order_energy_consumed.py current --file CELL_E_TEST_00.csv
```

### `socpolarization.py`

This script plots the **polarization resistance R1** as a function of the **state of charge (SoC)** for a given cell test file. It does this by identifying the current plateau just after a current jump, and looking at the corresponding voltage change. An exponential fit is then computed for that voltage change, corresponding to the polarization effect, which is due to the RC branch of the First-order model. From that exponential fit we can extract the Resistance (R1) of the branch, as well as the time constant tau. Tau can be found by finding how much time it takes for the Voltage to reach 63% of its maximum value relative to the initial Voltage when the current plateau starts. We can then find the Capacitance (C1) of the RC branch by diving tau by R1. In the GUI, a coefficient that is multiplied by R1 can be manipulated to observe how the plot changes.

The name of the test CSV file to use must also be added as usual.

To run:
```bash
python socpolarization.py --file CELL_E_TEST_00.csv
```
```bash
python3 socpolarization.py --file CELL_E_TEST_00.csv
```

### `energyconsumptionfirstorder.py`

This script runs a **battery energy consumption simulation** for a given cell test file using the First-order ECM, and its parameters obtained in the previous script. It does this with the same core code as `zero_order_energy_consumed.py`, however it also adds to this an iterative model of the polarization voltage. The polarization voltage is calculated using the equation V = IR(1-exp(-t/tau)), where the time represents a time step between two calculations (1 second), and this voltage is added to the value of the polarization voltage calculated at the previous time value. This code outputs the energy consumed by the battery pack, and the distance that the car can travel under the chosen configuration (110 cells in series with two parallel branches).

The name of the test CSV file to use must also be added as usual.

To run:
```bash
python energyconsumptionfirstorder.py --file CELL_E_TEST_00.csv
```
```bash
python3 energyconsumptionfirstorder.py --file CELL_E_TEST_00.csv
```

### `SoH_degradation.py`

This script estimates the **State of Health (SoH)** of each experimental cell data file (based on capacity) and evaluates how the **vehicle range** evolves as SoH decreases. It then plots **Range vs SoH**.

To run:
```bash
python SoH_degration.py
```
```bash
python3 SoH_degration.py
```

### `GUI.py`

This script codes the Graphical User Interface, which uses data from previous python scripts to plot significant results, as well as to allow sensitivity analysis to be displayed.
To run this Graphical User Interface, streamlit must be installed, which can be done with the following code:

```bash
pip install streamlit
```
```bash
pip3 install streamlit
```

To run:
```bash
python -m streamlit run GUI.py
```
```bash
python3 -m streamlit run GUI.py
```

----


You have now reached the end of this README detailing our project Git Repository.