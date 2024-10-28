import unittest
from datetime import datetime
from battery_model import Battery

class TestBattery(unittest.TestCase):
    def setUp(self):
        self.inputs = {"requested_power_flow": 0}
        self.outputs = {"effective_power_flow": 0}
        self.parameters = {
            "charge_power_max": 100,    # Maximum charging power (kW)
            "discharge_power_max": 200, # Maximum discharging power (kW)
            "soc_min": 0.1,             # Minimum State of Charge (fraction)
            "soc_max": 0.9,             # Maximum State of Charge (fraction)
            "capacity": 1000,           # Battery capacity (kWh)
        }
        self.states = {"soc": 0.5}       # Initial State of Charge (fraction)

    def test_charging(self):
        """Test charging over multiple steps and check SoC increases correctly."""
        battery = Battery(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=1,
            time=datetime.now()
        )
        battery.inputs["requested_power_flow"] = 50  # Request charging power of 50 kW
        steps = 5
        expected_soc = battery.states["soc"]  # SoC is already in absolute value
        for _ in range(steps):
            battery.step()
            self.assertEqual(battery.outputs["effective_power_flow"], 50)
            expected_soc += 50  # Increase SoC by 50 kWh
            self.assertEqual(battery.states["soc"], expected_soc)

    def test_discharging(self):
        """Test discharging over multiple steps and check SoC decreases correctly."""
        battery = Battery(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=1,
            time=datetime.now()
        )
        battery.inputs["requested_power_flow"] = -100  # Request discharging power of 100 kW
        steps = 3
        expected_soc = battery.states["soc"]  # SoC is already in absolute value
        for _ in range(steps):
            battery.step()
            self.assertEqual(battery.outputs["effective_power_flow"], -100)
            expected_soc -= 100  # Decrease SoC by 100 kWh
            self.assertEqual(battery.states["soc"], expected_soc)

    def test_soc_limits_charging(self):
        """Test that SoC does not exceed soc_max when charging."""
        battery = Battery(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=1,
            time=datetime.now()
        )
        battery.inputs["requested_power_flow"] = 200  # Request charging power exceeding max
        steps = 5
        effective_power_flows = []
        for _ in range(steps):
            battery.step()
            effective_power_flows.append(battery.outputs["effective_power_flow"])
        # Expected effective power flows considering soc_max limit
        expected_effective_power_flows = [100, 100, 100, 100, 0]
        self.assertEqual(effective_power_flows, expected_effective_power_flows)
        max_soc = battery.parameters["soc_max"] * battery.parameters["capacity"]
        self.assertEqual(battery.states["soc"], max_soc)

    def test_soc_limits_discharging(self):
        """Test that SoC does not go below soc_min when discharging."""
        battery = Battery(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=1,
            time=datetime.now()
        )
        battery.inputs["requested_power_flow"] = -200  # Request discharging power exceeding max
        steps = 5
        effective_power_flows = []
        for _ in range(steps):
            battery.step()
            effective_power_flows.append(battery.outputs["effective_power_flow"])
        # Expected effective power flows considering soc_min limit
        expected_effective_power_flows = [-200, -200, -200, -100, 0]
        self.assertEqual(effective_power_flows, expected_effective_power_flows)
        min_soc = battery.parameters["soc_min"] * battery.parameters["capacity"]
        self.assertEqual(battery.states["soc"], min_soc)

    def test_power_limits_charging(self):
        """Test that effective power flow does not exceed charge_power_max when charging."""
        battery = Battery(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=1,
            time=datetime.now()
        )
        battery.inputs["requested_power_flow"] = 150  # Request charging power exceeding max
        battery.step()
        self.assertEqual(battery.outputs["effective_power_flow"], battery.parameters["charge_power_max"])

    def test_power_limits_discharging(self):
        """Test that effective power flow does not exceed discharge_power_max when discharging."""
        battery = Battery(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=1,
            time=datetime.now()
        )
        battery.inputs["requested_power_flow"] = -250  # Request discharging power exceeding max
        battery.step()
        self.assertEqual(battery.outputs["effective_power_flow"], -battery.parameters["discharge_power_max"])

if __name__ == '__main__':
    unittest.main()
