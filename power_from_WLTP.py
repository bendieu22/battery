import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import argparse

def load_data():
    data = pd.read_csv('WLTC_data.csv')
    return data

"""
This function uses the WLTC data to be able to plot the Power at the wheels, then the mechanical power,
 then the electrical power at every second of the course of the whole 30min WLTP cycle.
"""
def run_simulation(mass, theta, wind_speed):
    data = load_data()
    time_values = data['Total elapsed time'].values
    speed_values = data['WLTC class 3, version 5, vehicle speed'].values
    speed_values_ms = speed_values / 3.6
    
    air_density = 1.225 #at sea level in 15°C 
    drag_coef = 0.29 #specific to the car
    front_area = 2.70726 #specific to the car 
    g = 9.81 #gravity
    C_rr = 0.01 #coeficient rolling resistance
    drivetrain_coef = 0.95 #energy lost from the wheels to the road, friction, heat
    p_aux = 1000 #screens, lights, AC
    regen_coef = 0.6 #energy given back to the battery when the wheels spins by themselves
    elec_coef = 0.89 #energy lost to make the wheels spin, from mechanical to electrical  

    #initialising the lists and variables
    power_acc_only = []
    power_acc_roll = []
    power_acc_aero_roll = []
    power_total = []
    p_mech = []
    p_batt = []
    energy = 0

    for time in range(len(time_values)):
        if time == 0:
            power_acc_only.append(0)
            power_acc_roll.append(0)
            power_acc_aero_roll.append(0)
            power_total.append(0)
            p_mech.append(0)
            p_batt.append(p_aux)
            energy = energy
        else: #at every sencond add the value of the power considering the speed of the WLTP in their respective lists of powers
            v = speed_values_ms[time]
            acc = (speed_values_ms[time] - speed_values_ms[time - 1])
            
            # different forces that have an impact on the power needed
            force_acc = mass * acc 
            force_aero = 0.5 * air_density * drag_coef * front_area * (v - wind_speed/3.6)**2
            force_roll = C_rr * mass * g
            force_slope = mass * g * np.sin(theta)
            
            # Cumulative Power
            #p1 = force_acc * v
            p2 = (force_acc + force_roll) * v # additional forces that affect the Energy 
            p3 = (force_acc + force_aero + force_roll) * v #taken into account in the WLTP 
            p4 = (force_acc + force_aero + force_roll + force_slope) * v # additional forces that affect the Energy 
            
           # power_acc_only.append(p1)
            power_acc_roll.append(p2)
            power_acc_aero_roll.append(p3)
            power_total.append(p4)
            #convert power at the wheels to mechanical power
            p5 = p4 / drivetrain_coef
            p_mech.append(p5)
            #convert mechanical power to electrical power
            if p4 >= 0: #here it is the power taking into account the regenerative braking
                p6 = p4 / (drivetrain_coef * elec_coef) + p_aux
            else:
                p6 = p4 * regen_coef + p_aux
            p_batt.append(p6)
            energy = energy + p_batt[time]*(1/3600) #energy considering there is regenerative braking
    return {
        "time": time_values,
        "speed_ms": speed_values_ms,
        "power_total": power_total,
        "p_mech": p_mech,
        "p_batt": p_batt,
        "power_acc_only": power_acc_only,
        "power_acc_roll": power_acc_roll,
        "power_acc_aero_roll": power_acc_aero_roll,
        "energy": energy #in Wh
    }

"""
These are the plots callable from the GUI.py
Each plot of the powers represent a different step of the power gotten for the WLTP

"""
def plot_speed(results):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(results["time"], results["speed_ms"], color='black', linestyle = 'None', marker = '.')
    ax.set_title("WLTP Speed Profile")
    ax.set_ylabel("Speed (m/s)")
    ax.grid(True)
    return fig

def plot_total_power(results):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(results["time"], results["power_total"], color='blue', linestyle = 'None', marker = '.')
    ax.set_title("Total Power vs Time")
    ax.set_ylabel("Power (W)")
    ax.grid(True)
    return fig

def plot_mechanical_power(results):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(results["time"], results["p_mech"], color='blue', linestyle = 'None', marker = '.')
    ax.set_title("Mechanical Power vs Time")
    ax.set_ylabel("Power (W)")
    ax.grid(True)
    return fig

def plot_battery_power(results):
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(results["time"], results["p_batt"], color='blue', linestyle = 'None', marker = '.')
    ax.set_title("Battery Power vs Time")
    ax.set_ylabel("Power (W)")
    ax.grid(True)
    return fig

def plot_power_components(results):
    fig, ax = plt.subplots(figsize=(10, 4))
    t = results["time"]
    ax.plot(t, results["power_total"], label='Total', color='blue', alpha=0.9, linestyle = 'None', marker = '.')
    ax.plot(t, results["power_acc_aero_roll"], label='+ Rolling', color='green', alpha=0.8, linestyle = 'None', marker = '.')
    ax.plot(t, results["power_acc_roll"], label='+ Roll', color='magenta', alpha=0.7, linestyle = 'None', marker = '.')
    #ax.plot(t, results["power_acc_only"], label='Acc Only', color='blue', alpha=0.6, linestyle = 'None', marker = '.')
    
    ax.set_title("Evolution of Power Components")
    ax.legend()
    ax.grid(True)
    return fig


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run WLTP Simulation")

    parser.add_argument(
        "plot_type", 
        choices=["speed", "total", "mechanical", "battery", "components"], 
        help="Select which plot to display"
    )

    args = parser.parse_args()
    
    results = run_simulation(mass=1502, theta=0, wind_speed=0)
    
    if args.plot_type == "speed":
        plot_speed(results)
    elif args.plot_type == "total":
        plot_total_power(results)
    elif args.plot_type == "mechanical":
        plot_mechanical_power(results)
    elif args.plot_type == "battery":
        plot_battery_power(results)
    elif args.plot_type == "components":
        plot_power_components(results)

    plt.show()