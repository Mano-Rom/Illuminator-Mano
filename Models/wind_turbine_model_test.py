import unittest
from datetime import datetime
import numpy as np
from wind_turbine_model import WindTurbine  # Import the WindTurbine class

class TestWindTurbine(unittest.TestCase):
    def setUp(self):
        self.inputs = {"u": 0}  # Wind speed at measurement height (m/s)
        self.outputs = {"wind_gen": 0, "u_at_hub_height": 0}
        self.parameters = {
            "p_rated": 1500,            # Rated power output of the turbine (kW)
            "u_rated": 12,              # Rated wind speed (m/s)
            "u_cutin": 3,               # Cut-in wind speed (m/s)
            "u_cutout": 25,             # Cut-out wind speed (m/s)
            "diameter": 80,             # Rotor diameter (m)
            "cp": 0.45,                 # Coefficient of performance (<= 0.59)
            "output_type": 'power',     # 'power' or 'energy'
            "hub_height": 100,          # Turbine hub height (m)
            "measurement_height": 10,   # Wind speed measurement height (m)
            "roughness_length": 0.1,    # Surface roughness length (m)
            "air_density": 1.225        # Air density (kg/m³)
        }
        self.states = {}
        self.step_size = 60  # Time step in minutes
        self.time = datetime.now()

    def test_below_cutin_speed(self):
        """Test that wind generation is zero when wind speed is below cut-in speed."""
        wind_turbine = WindTurbine(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=self.step_size,
            time=self.time
        )
        wind_turbine.inputs['u'] = 2  # Below cut-in speed
        wind_turbine.step()
        self.assertEqual(wind_turbine.outputs['wind_gen'], 0)

    def test_at_cutin_speed(self):
        """Test that wind generation starts at cut-in speed."""
        wind_turbine = WindTurbine(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=self.step_size,
            time=self.time
        )
        wind_turbine.inputs['u'] = 3  # At cut-in speed
        wind_turbine.step()
        self.assertGreater(wind_turbine.outputs['wind_gen'], 0)

    def test_between_cutin_and_rated_speed(self):
        """Test wind generation between cut-in and rated speed."""
        wind_turbine = WindTurbine(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=self.step_size,
            time=self.time
        )
        wind_turbine.inputs['u'] = 8  # Between cut-in and rated speed
        wind_turbine.step()
        self.assertGreater(wind_turbine.outputs['wind_gen'], 0)
        self.assertLess(wind_turbine.outputs['wind_gen'], self.parameters['p_rated'])

    def test_at_rated_speed(self):
        """Test that wind generation is at rated power at rated wind speed."""
        wind_turbine = WindTurbine(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=self.step_size,
            time=self.time
        )
        wind_turbine.inputs['u'] = self.parameters['u_rated']  # At rated speed
        wind_turbine.step()
        self.assertEqual(wind_turbine.outputs['wind_gen'], self.parameters['p_rated'])

    def test_between_rated_and_cutout_speed(self):
        """Test wind generation remains at rated power between rated and cut-out speed."""
        wind_turbine = WindTurbine(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=self.step_size,
            time=self.time
        )
        wind_turbine.inputs['u'] = 20  # Between rated and cut-out speed
        wind_turbine.step()
        self.assertEqual(wind_turbine.outputs['wind_gen'], self.parameters['p_rated'])

    def test_at_cutout_speed(self):
        """Test that wind generation stops at cut-out speed."""
        wind_turbine = WindTurbine(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=self.step_size,
            time=self.time
        )
        wind_turbine.inputs['u'] = self.parameters['u_cutout']  # At cut-out speed
        wind_turbine.step()
        self.assertEqual(wind_turbine.outputs['wind_gen'], self.parameters['p_rated'])

    def test_above_cutout_speed(self):
        """Test that wind generation is zero when wind speed is above cut-out speed."""
        wind_turbine = WindTurbine(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=self.step_size,
            time=self.time
        )
        wind_turbine.inputs['u'] = 30  # Above cut-out speed
        wind_turbine.step()
        self.assertEqual(wind_turbine.outputs['wind_gen'], 0)

    def test_adjust_wind_speed(self):
        """Test the wind speed adjustment from measurement height to hub height."""
        wind_turbine = WindTurbine(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=self.step_size,
            time=self.time
        )
        u_measured = 5  # Wind speed at measurement height
        expected_u_hub = wind_turbine.adjust_wind_speed(u_measured)
        wind_turbine.inputs['u'] = u_measured
        wind_turbine.step()
        self.assertAlmostEqual(wind_turbine.outputs['u_at_hub_height'], expected_u_hub, places=5)

    def test_output_type_energy(self):
        """Test that output is calculated correctly when output_type is 'energy'."""
        self.parameters['output_type'] = 'energy'
        wind_turbine = WindTurbine(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=60,  # 1 hour
            time=self.time
        )
        wind_turbine.inputs['u'] = self.parameters['u_rated']  # At rated speed
        wind_turbine.step()
        expected_energy = self.parameters['p_rated'] * (wind_turbine.step_size / 60)
        self.assertEqual(wind_turbine.outputs['wind_gen'], expected_energy)

    def test_invalid_parameters(self):
        """Test that missing required parameters raise a ValueError."""
        invalid_parameters = self.parameters.copy()
        del invalid_parameters['p_rated']
        with self.assertRaises(ValueError):
            WindTurbine(
                inputs=self.inputs.copy(),
                outputs=self.outputs.copy(),
                parameters=invalid_parameters,
                states=self.states.copy(),
                step_size=self.step_size,
                time=self.time
            )

    def test_invalid_output_type(self):
        """Test that an invalid output_type raises a ValueError."""
        self.parameters['output_type'] = 'invalid'
        with self.assertRaises(ValueError):
            wind_turbine = WindTurbine(
                inputs=self.inputs.copy(),
                outputs=self.outputs.copy(),
                parameters=self.parameters.copy(),
                states=self.states.copy(),
                step_size=self.step_size,
                time=self.time
            )
            wind_turbine.inputs['u'] = self.parameters['u_rated']
            wind_turbine.step()

    def test_negative_wind_speed(self):
        """Test that negative wind speeds result in zero generation."""
        wind_turbine = WindTurbine(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=self.step_size,
            time=self.time
        )
        wind_turbine.inputs['u'] = -5  # Negative wind speed
        with self.assertRaises(ValueError):
            wind_turbine.step()

if __name__ == '__main__':
    unittest.main()
