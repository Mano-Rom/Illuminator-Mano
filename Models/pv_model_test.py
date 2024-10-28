import unittest
from datetime import datetime
from pv_model import PV  # Import the PV class
import numpy as np

class TestPV(unittest.TestCase):
    def setUp(self):
        self.inputs = {
            "G_Gh": 1000,   # Global Horizontal Irradiance (W/m²)
            "G_Dh": 100,    # Diffuse Horizontal Irradiance (W/m²)
            "G_Bn": 800,    # Direct Normal Irradiance (W/m²)
            "Ta": 25,       # Ambient Temperature (°C)
            "hs": 45,       # Sun elevation angle (degrees)
            "FF": 5,        # Wind speed (m/s)
            "Az": 180       # Sun azimuth angle (degrees)
        }
        self.outputs = {"pv_gen": 0, "total_irr": 0}
        self.parameters = {
            "m_area": 1.6,               # Module area (m²)
            "NOCT": 45,                  # Nominal Operating Cell Temperature (°C)
            "m_efficiency_stc": 0.15,    # Module efficiency at STC
            "G_NOCT": 800,               # Irradiance at NOCT (W/m²)
            "P_STC": 250,                # Power output at STC (W)
            "peak_power": 250,           # Peak power (W)
            "m_tilt": 30,                # Module tilt angle (degrees)
            "m_az": 180,                 # Module azimuth angle (degrees)
            "cap": 5,                    # Capacity (kW)
            "output_type": 'power',      # 'power' or 'energy'
            "inv_eff": 0.96,             # Inverter efficiency
            "mppt_eff": 0.99,            # MPPT efficiency
            "losses": 0.97,              # Other losses
            "sf": 1.1,                   # Safety factor
            "albedo": 0.2                # Albedo coefficient
        }
        self.states = {}
        self.step_size = 60  # Time step in minutes
        self.time = datetime.now()

    def test_pv_generation_power(self):
        """Test PV generation output in 'power' mode under standard conditions."""
        pv_system = PV(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=self.step_size,
            time=self.time
        )
        pv_system.step()
        # Calculate expected values manually
        expected_total_irradiance = pv_system.total_irr()
        expected_efficiency = pv_system.temp_effect(expected_total_irradiance)
        expected_pv_gen = pv_system.generation(expected_total_irradiance, expected_efficiency)
        self.assertAlmostEqual(pv_system.outputs['total_irr'], expected_total_irradiance, places=2)
        self.assertAlmostEqual(pv_system.outputs['pv_gen'], expected_pv_gen, places=2)

    def test_pv_generation_energy(self):
        """Test PV generation output in 'energy' mode over multiple steps."""
        self.parameters['output_type'] = 'energy'
        pv_system = PV(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=self.step_size,  # 60 minutes
            time=self.time
        )
        pv_system.step()
        # Calculate expected values manually
        expected_total_irradiance = pv_system.total_irr()
        expected_efficiency = pv_system.temp_effect(expected_total_irradiance)
        expected_pv_gen = pv_system.generation(expected_total_irradiance, expected_efficiency)
        self.assertAlmostEqual(pv_system.outputs['pv_gen'], expected_pv_gen, places=2)

    def test_zero_irradiance(self):
        """Test PV generation when there is no irradiance (night time)."""
        self.inputs['G_Gh'] = 0
        self.inputs['G_Dh'] = 0
        self.inputs['G_Bn'] = 0
        self.inputs['hs'] = -5  # Sun below horizon
        pv_system = PV(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=self.step_size,
            time=self.time
        )
        pv_system.step()
        self.assertEqual(pv_system.outputs['pv_gen'], 0)
        self.assertEqual(pv_system.outputs['total_irr'], 0)

    def test_varying_irradiance(self):
        """Test PV generation with varying irradiance over multiple steps."""
        irradiance_values = [200, 400, 600, 800, 1000]
        pv_system = PV(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=15,  # 15 minutes
            time=self.time
        )
        expected_pv_gens = []
        for G_Gh in irradiance_values:
            pv_system.inputs['G_Gh'] = G_Gh
            pv_system.inputs['G_Dh'] = G_Gh * 0.1  # Assume 10% diffuse
            pv_system.inputs['G_Bn'] = G_Gh * 0.9  # Assume 90% direct
            pv_system.step()
            expected_total_irradiance = pv_system.total_irr()
            expected_efficiency = pv_system.temp_effect(expected_total_irradiance)
            expected_pv_gen = pv_system.generation(expected_total_irradiance, expected_efficiency)
            expected_pv_gens.append(expected_pv_gen)
            self.assertAlmostEqual(pv_system.outputs['pv_gen'], expected_pv_gen, places=2)
        # Check that PV generation increases with irradiance
        self.assertTrue(all(x < y for x, y in zip(expected_pv_gens, expected_pv_gens[1:])))

    def test_invalid_output_type(self):
        """Test behavior when an invalid output_type is provided."""
        self.parameters['output_type'] = 'invalid'
        pv_system = PV(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=self.step_size,
            time=self.time
        )
        with self.assertRaises(ValueError):
            pv_system.step()

    def test_extreme_temperatures(self):
        """Test PV generation under extreme ambient temperatures."""
        extreme_temperatures = [-20, 0, 25, 50, 75]
        pv_system = PV(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=60,
            time=self.time
        )
        for Ta in extreme_temperatures:
            pv_system.inputs['Ta'] = Ta
            pv_system.step()
            expected_total_irradiance = pv_system.total_irr()
            expected_efficiency = pv_system.temp_effect(expected_total_irradiance)
            expected_pv_gen = pv_system.generation(expected_total_irradiance, expected_efficiency)
            self.assertAlmostEqual(pv_system.outputs['pv_gen'], expected_pv_gen, places=2)

    def test_different_tilt_angles(self):
        """Test PV generation with different module tilt angles."""
        tilt_angles = [0, 15, 30, 45, 60, 90]
        pv_system = PV(
            inputs=self.inputs.copy(),
            outputs=self.outputs.copy(),
            parameters=self.parameters.copy(),
            states=self.states.copy(),
            step_size=60,
            time=self.time
        )
        for tilt in tilt_angles:
            pv_system.parameters['m_tilt'] = tilt
            pv_system.step()
            expected_total_irradiance = pv_system.total_irr()
            expected_efficiency = pv_system.temp_effect(expected_total_irradiance)
            expected_pv_gen = pv_system.generation(expected_total_irradiance, expected_efficiency)
            self.assertAlmostEqual(pv_system.outputs['pv_gen'], expected_pv_gen, places=2)

if __name__ == '__main__':
    unittest.main()
