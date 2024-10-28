import numpy as np
import datetime

"""
Inputs: {
    "G_Gh": 0,    # Global Horizontal Irradiance (W/m²)
    "G_Dh": 0,    # Diffuse Horizontal Irradiance (W/m²)
    "G_Bn": 0,    # Direct Normal Irradiance (W/m²)
    "Ta": 0,      # Ambient Temperature (°C)
    "hs": 0,      # Sun elevation angle (degrees)
    "FF": 0,      # Wind speed (m/s)
    "Az": 0       # Sun azimuth angle (degrees)
}
Outputs: {
    "pv_gen": 0,      # PV generation (kW or kWh)
    "total_irr": 0    # Total irradiance on the panel (W/m²)
}
Parameters: {
    "m_area": ...,                # Module area (m²)
    "NOCT": ...,                  # Nominal Operating Cell Temperature (°C)
    "m_efficiency_stc": ...,      # Module efficiency at STC
    "G_NOCT": ...,                # Irradiance at NOCT (W/m²)
    "P_STC": ...,                 # Power output at STC (W)
    "peak_power": ...,            # Peak power (W)
    "m_tilt": ...,                # Module tilt angle (degrees)
    "m_az": ...,                  # Module azimuth angle (degrees)
    "cap": ...,                   # Capacity (kW)
    "output_type": ...,           # 'power' or 'energy'
    "inv_eff": 0.96,              # Inverter efficiency
    "mppt_eff": 0.99,             # MPPT efficiency
    "losses": 0.97,               # Other losses
    "sf": 1.1,                    # Safety factor
    "albedo": 0.2                 # Albedo coefficient
}
States: {}
"""

class PV:

    def __init__(self, inputs: dict = {}, outputs: dict = {}, parameters: dict = {}, states: dict = {}, step_size: int = 1, time: datetime.datetime = None):
        self.inputs = inputs
        self.outputs = outputs
        self.parameters = parameters
        self.states = states
        self.step_size = step_size  # Time step in minutes
        self.time = time

        # Time interval in hours
        self.time_interval = self.step_size / 60  # Convert step size from minutes to hours

    def aoi(self):
        """Calculates the angle of incidence (AOI)."""
        m_tilt = self.parameters['m_tilt']
        m_az = self.parameters['m_az']
        hs = self.inputs.get('hs', 0)
        Az = self.inputs.get('Az', 0)

        cos_aoi = (np.cos(np.radians(90 - m_tilt)) * np.cos(np.radians(hs)) * np.cos(np.radians(m_az - Az)) +
                   np.sin(np.radians(90 - m_tilt)) * np.sin(np.radians(hs)))
        cos_aoi = max(cos_aoi, 0)
        return cos_aoi

    def diffused_irr(self):
        """Calculates the diffused irradiance."""
        m_tilt = self.parameters['m_tilt']
        G_Dh = self.inputs.get('G_Dh', 0)

        svf = (1 + np.cos(np.radians(m_tilt))) / 2
        g_diff = svf * G_Dh
        self.states['svf'] = svf  # Store for use in reflected irradiance
        return g_diff

    def reflected_irr(self):
        """Calculates the reflected irradiance."""
        albedo = self.parameters['albedo']
        G_Gh = self.inputs.get('G_Gh', 0)
        svf = self.states.get('svf', 1)  # Retrieve svf from states

        g_ref = albedo * (1 - svf) * G_Gh
        return g_ref

    def direct_irr(self):
        """Calculates the direct irradiance."""
        G_Bn = self.inputs.get('G_Bn', 0)
        cos_aoi = self.aoi()

        g_dir = G_Bn * cos_aoi
        return g_dir

    def total_irr(self):
        """Calculates the total irradiance on the panel."""
        g_diff = self.diffused_irr()
        g_ref = self.reflected_irr()
        g_dir = self.direct_irr()

        g_aoi = g_diff + g_ref + g_dir
        return g_aoi

    def temp_effect(self, g_aoi):
        """Calculates the temperature effect on efficiency."""
        Ta = self.inputs.get('Ta', 0)
        FF = self.inputs.get('FF', 0)
        NOCT = self.parameters['NOCT']
        G_NOCT = self.parameters['G_NOCT']
        m_efficiency_stc = self.parameters['m_efficiency_stc']

        # Prevent division by zero in wind speed
        FF = max(FF, 0.1)

        m_temp = Ta + (g_aoi / G_NOCT) * (NOCT - 20) * (9.5 / (5.7 + 3.8 * FF)) * (1 - (m_efficiency_stc / 0.90))
        efficiency = m_efficiency_stc * (1 + (-0.0035 * (m_temp - 25)))
        return efficiency

    def generation(self, g_aoi, efficiency):
        """Calculates the PV generation (power or energy)."""
        cap = self.parameters['cap']
        sf = self.parameters['sf']
        P_STC = self.parameters['P_STC']
        m_area = self.parameters['m_area']
        output_type = self.parameters['output_type']
        inv_eff = self.parameters['inv_eff']
        mppt_eff = self.parameters['mppt_eff']
        losses = self.parameters['losses']
        time_interval = self.time_interval

        # Generation calculation
        num_of_modules = np.ceil(cap * sf * 1000 / P_STC)  # Convert capacity to W
        total_m_area = num_of_modules * m_area

        # Compute output power or energy
        if output_type == 'energy':
            # Energy in kWh over the time interval
            p_ac = (total_m_area * g_aoi * efficiency * inv_eff * mppt_eff * losses * time_interval) / 1000
        elif output_type == 'power':
            # Instantaneous power in kW
            p_ac = (total_m_area * g_aoi * efficiency * inv_eff * mppt_eff * losses) / 1000
        else:
            raise ValueError("Invalid output_type. Must be 'power' or 'energy'.")

        return p_ac

    def step(self):
        """
        Computes the PV generation and total irradiance based on the inputs and parameters.
        """
        # Calculate total irradiance
        g_aoi = self.total_irr()
        self.outputs['total_irr'] = g_aoi

        # Calculate temperature effect on efficiency
        efficiency = self.temp_effect(g_aoi)

        # Calculate PV generation
        p_ac = self.generation(g_aoi, efficiency)
        self.outputs['pv_gen'] = p_ac # PV generation (kW or kWh)