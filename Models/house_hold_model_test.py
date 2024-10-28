import unittest
from datetime import datetime
from house_hold_model import HouseHold  # Import the HouseHold class

class TestHouseHold(unittest.TestCase):
    def setUp(self):
        self.inputs = {"load": 0}  # Load per household (kWh per time interval)
        self.outputs = {"load_dem": 0}
        self.parameters = {
            "houses": 10,           # Number of houses
            "output_type": 'energy'  # 'power' or 'energy'
        }
        self.states = {}
        self.step_size = 15  # Step size in minutes
        self.time = datetime.now()

    def test_total_load_energy(self):
        """Test total load demand in 'energy' output_type over multiple steps."""
        household = HouseHold(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=self.step_size,
            time=self.time
        )
        household.inputs["load"] = 2  # 2 kWh per household per time interval
        steps = 5
        expected_load = household.inputs["load"] * household.parameters["houses"]
        for _ in range(steps):
            household.step()
            self.assertEqual(household.outputs["load_dem"], expected_load)

    def test_total_load_power(self):
        """Test total load demand in 'power' output_type over multiple steps."""
        self.parameters["output_type"] = 'power'
        household = HouseHold(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=self.step_size,
            time=self.time
        )
        household.inputs["load"] = 1.5  # 1.5 kWh per household per time interval
        steps = 3
        time_interval_hours = household.step_size / 60  # Convert minutes to hours
        expected_load_energy = household.inputs["load"] * household.parameters["houses"]
        expected_load_power = expected_load_energy / time_interval_hours
        for _ in range(steps):
            household.step()
            self.assertEqual(household.outputs["load_dem"], expected_load_power)

    def test_variable_load(self):
        """Test household with variable loads over multiple steps."""
        loads = [1, 2, 3, 4]  # kWh per household per time interval
        household = HouseHold(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=self.step_size,
            time=self.time
        )
        for load in loads:
            household.inputs["load"] = load
            expected_load = load * household.parameters["houses"]
            if household.parameters["output_type"] == 'power':
                expected_load /= (household.step_size / 60)
            household.step()
            self.assertEqual(household.outputs["load_dem"], expected_load)

    def test_no_houses(self):
        """Test behavior when there are zero houses."""
        self.parameters["houses"] = 0
        household = HouseHold(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=self.step_size,
            time=self.time
        )
        household.inputs["load"] = 2
        household.step()
        self.assertEqual(household.outputs["load_dem"], 0)

if __name__ == '__main__':
    unittest.main()