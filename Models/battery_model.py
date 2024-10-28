import datetime

"""
Inputs:{
    "requested_power_flow": 0  # Requested charging (+) or discharging (-) power/energy
}
Outputs:{
    "effective_power_flow": 0,  # Effective charging/discharging power/energy
}
Parameters:{
    "charge_power_max": 100,    # Maximum charging power (kW)
    "discharge_power_max": 200, # Maximum discharging power (kW)
    "soc_min": 0.1,             # Minimum State of Charge (fraction)
    "soc_max": 0.9,             # Maximum State of Charge (fraction)
    "capacity": 1000,           # Battery capacity (kWh)
}
States:{
    "soc": 0.5                  # Initial State of Charge (fraction)
}
"""

class Battery:
    def __init__(self, inputs:dict={}, outputs:dict={}, parameters:dict={}, states:dict={}, step_size:int=1, time:datetime.datetime=None):
        self.inputs = inputs
        self.outputs = outputs
        self.parameters = parameters
        self.states = states
        self.step_size = step_size
        self.time = time
        self.states["soc"] = self.states["soc"] * parameters["capacity"] # Convert SoC from fraction to absolute value

    def step(self):
        ## Load inputs ##
        # Get the requested power flow
        requested_power_flow = self.inputs["requested_power_flow"]
        # Determine maximum allowed charge and discharge power
        charge_power_max = self.parameters["charge_power_max"]
        discharge_power_max = self.parameters["discharge_power_max"]
        # Determine current SoC as a fraction of capacity
        current_soc_fraction = self.states["soc"] / self.parameters["capacity"]

        ## Calculate effective power flow, update SOC ##
        # Check if the requested power flow is for charging or discharging
        if requested_power_flow > 0:  # Charging
            # Limit power flow to maximum charge power and SOC max
            effective_power_flow = min(requested_power_flow, charge_power_max)
            # Check if the SoC will exceed the maximum SoC
            if current_soc_fraction + (effective_power_flow / self.parameters["capacity"]) > self.parameters["soc_max"]:
                # Limit power flow to the amount that would bring the SoC to the maximum
                effective_power_flow = (self.parameters["soc_max"] - current_soc_fraction) * self.parameters["capacity"]
        elif requested_power_flow < 0:  # Discharging
            # Limit power flow to maximum discharge power and SOC min
            effective_power_flow = max(requested_power_flow, -discharge_power_max)
            # Check if the SoC will fall below the minimum SoC
            if current_soc_fraction + (effective_power_flow / self.parameters["capacity"]) < self.parameters["soc_min"]:
                # Limit power flow to the amount that would bring the SoC to the minimum
                effective_power_flow = (self.parameters["soc_min"] - current_soc_fraction) * self.parameters["capacity"]
        else:  # No power flow
            effective_power_flow = 0
        
        self.states["soc"] += effective_power_flow  # Update SoC
        
        ## Update outputs ##
        self.outputs["effective_power_flow"] = effective_power_flow 
  