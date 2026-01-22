import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

import zero_order_energy_consumed
import power_from_WLTP  
import plot_tests
import SoC_computation
import SoC_0thorder_parameters_link
import socpolarization
import energyconsumptionfirstorder

files = plot_tests.get_cell_files()

st.title("Renault Zoe Battery Simulation")

def reset_defaults():
    st.session_state.theta_input = "0.0"
    st.session_state.wind_input = "0.0"
    st.session_state.mass_input = "0.0"

    if files:
        st.session_state.cell_selector = files[0].stem

    st.session_state.r0_mult = 1.0
    st.session_state.ocv_mult = 1.0
    st.session_state.r1_mult = 1.0
    st.session_state.soc_slider = 100
    st.session_state.n_cells_slider = 220 
    st.session_state.n_parallel_slider = 2


# --- SIDEBAR INPUTS ---
st.sidebar.title("Car model Parameters")

st.sidebar.button("Reset to Defaults", on_click=reset_defaults)

def get_float_input(label, default_value, key_name):
    val = st.sidebar.text_input(label, value=str(default_value), key=key_name)
    try:
        return float(val)
    except ValueError:
        st.sidebar.error(f"Please enter a valid number for {label}")
        return float(default_value)

theta_deg = get_float_input('Angle theta (degrees)', 0.0, "theta_input")
wind_kmh = get_float_input('Wind speed (km/h)', 0.0, "wind_input")
additional_mass = get_float_input('Additional mass (kg)', 0.0, "mass_input")

selected_file = st.sidebar.selectbox(
    "Choose a cell:", 
    [f.stem for f in files],
    index=0,
    key="cell_selector"
)
filepath = files[[f.stem for f in files].index(selected_file)]
capacity = round(SoC_computation.overall_capacity(filepath), 3)

theta_rad = np.radians(theta_deg)
wind_ms = wind_kmh / 3.6
total_mass = 1502 + additional_mass

st.sidebar.markdown("---")
st.sidebar.title("Cell Parameters")

R0_multiplier = st.sidebar.slider(' R0 multiplier ', 0.5, 10.0, 1.0, 0.5, key="r0_mult")
OCV_multipler = st.sidebar.slider('OCV multiplier', 0.5, 10.0, 1.0, 0.5, key="ocv_mult")
R1_multiplier = st.sidebar.slider(' R1 multiplier ', 0.5, 10.0, 1.0, 0.5, key="r1_mult")
SOC = st.sidebar.slider('SOC percentage', 5, 100, 100, 1, key="soc_slider")

st.sidebar.markdown("---")
st.sidebar.title("Pack Design")
# Slider for Series/Parallel configuration
N_cells = st.sidebar.slider(
    "Number of cells in total (Default 220):", 
    200, 240, 220, 
    step=4,
    key="n_cells_slider"
)
N_parallel = st.sidebar.slider(
    "Cells in Parallel (Default 2): ", 
    1, 4, 2, 
    help="Determines Pack Capacity",
    key="n_parallel_slider"
)
N_series = N_cells/N_parallel
current_cell_ocv = SoC_0thorder_parameters_link.interpolate_ocv(filepath, SOC) 
pack_voltage_real = N_series * current_cell_ocv
# Real-time Pack Stats Calculation

results_cell = zero_order_energy_consumed.energy_consumption_cell(filepath, N_series, N_parallel, R0_multiplier, OCV_multipler, SOC, total_mass, wind_ms, theta_rad)
capacity_cell = capacity # from your existing variable
pack_voltage = N_series * pack_voltage_real
pack_capacity_kwh = results_cell["energyconsumed"]
pack_mass_est = (N_series * N_parallel * 0.5) * 1.3 # Assuming 0.5kg/cell * 1.3 packaging factor


# --- BODY ---

results = power_from_WLTP.run_simulation(
    mass=total_mass, 
    theta=theta_rad, 
    wind_speed=wind_ms, 
)

st.write("### Simulation Results")
col_plots, col_info = st.columns([2, 1], gap="medium")

with col_plots:
    st.write("#### 1. WLTP Speed Profile")
    fig_speed = power_from_WLTP.plot_speed(results) 
    st.pyplot(fig_speed)

    st.write("#### 2. Power at Wheels")
    fig_total = power_from_WLTP.plot_total_power(results)
    st.pyplot(fig_total)

    st.write("#### 3. Battery Power (incl. Losses & Aux)")
    fig_batt = power_from_WLTP.plot_battery_power(results)
    st.pyplot(fig_batt)

    if st.checkbox("Show Power Components Breakdown"):
        st.write("#### 3.bis. Power Components")
        fig_comp = power_from_WLTP.plot_power_components(results)
        st.pyplot(fig_comp)

with col_info:
    st.write("### Simulation Stats")
    
    st.write("**Cycle Type:** WLTP Class 3")
    st.write("**Total Duration:** 1800 s")
    st.write("**Energy needed for one WLTP cycle:** ", str(round(results["energy"],2)), "Wh")
    st.write("")
    st.write("")

    st.divider()
    
    st.markdown("####  Values")
    st.write("- **Highest power needed at the wheels:**", str(round(max(results["power_total"])/1000,2)), "kW")
    st.write("- **Highest power needed at the battery:**", str(round(max(results["p_batt"])/1000,2)), "kW")
    if theta_deg != 0: 
        st.write(f"- **Theta:** {theta_deg}°")
    if wind_kmh != 0:
        st.write(f"- **Wind Speed:** {wind_kmh} km/h")
    if additional_mass!= 0:
        st.write(f"- **Total Mass:** {total_mass} kg")
    


st.write("#### 4. Cell plots and parameters")
fig_cell = plot_tests.plot_file(filepath)
st.pyplot(fig_cell)


st.write("The capacity of this cell is ", str(capacity), "Ah.")

st.write("#### 5. Energy Consumption (0th Order)")

col1, col2, col3 = st.columns(3)
col1.metric("Pack Config", f"{N_series}S {N_parallel}P")
col2.metric("Energy Consumable", f"{pack_capacity_kwh:.1f} kWh")
col3.metric("System Voltage", f"{pack_voltage_real:.0f} V", f"at {SOC}% SOC")


fig_distance_SOC = zero_order_energy_consumed.plot_distance_SOC(results_cell)
fig_voltage_time = zero_order_energy_consumed.plot_voltage_time(results_cell)
fig_current_time = zero_order_energy_consumed.plot_current_time(results_cell)

st.pyplot(fig_distance_SOC)
st.pyplot(fig_voltage_time)
#st.pyplot(fig_current_time)

st.write("#### 6. 0th Order vs 1st Order model")

col_1, col_2 = st.columns(2)

with col_1:
    
    fig_R0_SOC = SoC_0thorder_parameters_link.plot_R0_SOC(filepath, R0_multiplier)
    st.pyplot(fig_R0_SOC)
    fig_OCV_SOC = SoC_0thorder_parameters_link.plot_ocv_soc_full_link(filepath, OCV_multipler)
    
    st.pyplot(fig_OCV_SOC)

with col_2:
    fig_R1_SOC= socpolarization.plot_SOC_R1(filepath, R1_multiplier)
    st.pyplot(fig_R1_SOC)
    energy = energyconsumptionfirstorder.energy_consumption_cell(filepath, N_series, N_parallel, R0_multiplier, R1_multiplier, OCV_multipler, SOC, total_mass, wind_ms, theta_rad)[1]
    st.write(" The energy that is consumable in the 1st order model is: ", str(round(energy, 1)), "kW")    
