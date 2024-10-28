import datetime

"""
Inputs:{
    "load": 0  # Load per household (kWh per time interval)
}
Outputs:{
    "load_dem": 0  # Total load demand (kW or kWh depending on output_type)
}
Parameters:{
    "houses": ...,       # Number of houses
    "output_type": ...,  # 'power' or 'energy'
}
States:{
}
"""

class HouseHold:
    def __init__(self, inputs:dict={}, outputs:dict={}, parameters:dict={}, states:dict={}, step_size:int=1, time:datetime.datetime=None):
        self.inputs = inputs
        self.outputs = outputs
        self.parameters = parameters
        self.states = states
        self.step_size = step_size
        self.time = time

        self.time_interval = self.step_size / 60  # Convert step_size from minutes to hours

    def step(self):
        # Get inputs
        load_per_household = self.inputs.get('load', 0)  # kWh per time interval
        houses = self.parameters['houses']
        output_type = self.parameters['output_type']

        # Calculate total load demand
        total_load_demand = load_per_household * houses

        # Set output
        total_load_demand = total_load_demand if output_type == 'energy' else total_load_demand / self.time_interval
        self.outputs['load_dem'] = total_load_demand
        