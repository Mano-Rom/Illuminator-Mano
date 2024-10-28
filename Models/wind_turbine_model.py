import numpy as np
import math
import datetime

"""
Inputs: {
    "u": 0   # Wind speed at measurement height (m/s)
}
Outputs: {
    "wind_gen": 0,        # Wind generation (kW or kWh)
    "u_at_hub_height": 0  # Adjusted wind speed at hub height (m/s)
}
Parameters: {
    "p_rated": ...,            # Rated power output of the turbine (kW)
    "u_rated": ...,            # Rated wind speed (m/s)
    "u_cutin": ...,            # Cut-in wind speed (m/s)
    "u_cutout": ...,           # Cut-out wind speed (m/s)
    "diameter": ...,           # Rotor diameter (m)
    "cp": ...,                 # Coefficient of performance (<= 0.59)
    "output_type": ...,        # 'power' or 'energy'
    "hub_height": ...,         # Turbine hub height (m)
    "measurement_height": ..., # Wind speed measurement height (m)
    "roughness_length": 0.2,   # Surface roughness length (m), default 0.2
    "air_density": 1.225       # Air density (kg/m³), default at sea level
}
States: {}
"""

class WindTurbine:

    def __init__(self, inputs: dict = {}, outputs: dict = {}, parameters: dict = {}, states: dict = {}, step_size: int = 15, time: datetime.datetime = None):
        self.inputs = inputs
        self.outputs = outputs
        self.parameters = parameters
        self.states = states
        self.step_size = step_size  # Time step in minutes
        self.time = time

        # Required parameters
        required_parameters = ['p_rated', 'u_rated', 'u_cutin', 'u_cutout', 'diameter', 'cp', 'output_type', 'hub_height', 'measurement_height']

        for param in required_parameters:
            if param not in self.parameters:
                raise ValueError(f"Missing required parameter: {param}")

        # Set default parameters if not provided
        self.parameters.setdefault('air_density', 1.225)     # kg/m³ at sea level
        self.parameters.setdefault('roughness_length', 0.2)  # Surface roughness length in meters

        # Time interval in hours
        self.time_interval = self.step_size / 60  # Convert step size from minutes to hours

    def adjust_wind_speed(self, u):
        """
        Adjusts the wind speed from the measurement height to the turbine hub height using the logarithmic wind profile.
        """
        measurement_height = self.parameters['measurement_height']
        hub_height = self.parameters['hub_height']
        roughness_length = self.parameters['roughness_length']

        if measurement_height <= roughness_length or hub_height <= roughness_length:
            raise ValueError("Measurement height and hub height must be greater than roughness length.")

        # Logarithmic wind profile formula
        u_hub = u * (np.log(hub_height / roughness_length) / np.log(measurement_height / roughness_length))

        return u_hub

    def production(self, u_hub):
        """
        Calculates the power output when wind speed is within operational range but below rated speed.
        """
        radius = self.parameters['diameter'] / 2
        air_density = self.parameters['air_density']
        cp = self.parameters['cp']
        output_type = self.parameters['output_type']
        time_interval = self.time_interval

        # Power in watts
        p = 0.5 * air_density * cp * math.pi * radius ** 2 * u_hub ** 3  # W

        # Ensure the power does not exceed rated power
        p_rated_watts = self.parameters['p_rated'] * 1000  # Convert p_rated from kW to W
        p = min(p, p_rated_watts)

        if output_type == 'energy':
            # Energy in kWh over the time interval
            p_output = (p / 1000) * time_interval  # kWh
        elif output_type == 'power':
            # Instantaneous power in kW
            p_output = p / 1000  # kW
        else:
            raise ValueError("Invalid output_type. Must be 'power' or 'energy'.")

        return p_output

    def generation(self, u_hub):
        """
        Determines the power output based on the wind speed at hub height.
        """
        p_rated = self.parameters['p_rated']
        u_rated = self.parameters['u_rated']
        u_cutin = self.parameters['u_cutin']
        u_cutout = self.parameters['u_cutout']
        output_type = self.parameters['output_type']
        time_interval = self.time_interval

        if u_cutin <= u_hub < u_rated:
            # Operating below rated power
            p_output = self.production(u_hub)
        elif u_rated <= u_hub <= u_cutout:
            # Operating at rated power
            if output_type == 'energy':
                p_output = p_rated * time_interval  # kWh
            elif output_type == 'power':
                p_output = p_rated  # kW
        else:
            # No power generation (wind speed too low or too high)
            p_output = 0

        return p_output

    def step(self):
        """
        Main method to compute wind generation based on the current wind speed input.
        """
        # Get the input wind speed
        u = self.inputs.get('u', 0)  # Wind speed at measurement height (m/s)

        # Adjust wind speed to hub height
        u_hub = self.adjust_wind_speed(u)
        self.outputs['u_at_hub_height'] = u_hub

        # Calculate power generation
        p_output = self.generation(u_hub)
        self.outputs['wind_gen'] = p_output # Wind generation (kW or kWh)