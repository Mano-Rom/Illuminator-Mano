import yaml
from datetime import datetime
import os

class YamlInterpreter:
    def __init__(self, file_path):
        self.file_path = file_path

        # Load defaults and scenario data, then merge them
        self.defaults_data = self.load_yaml('Illuminator_Engine/defaults.yaml')
        scenario_data = self.load_yaml(self.file_path)
        self.yaml_data = {}
        self.merge_dicts(self.yaml_data, self.defaults_data)
        self.merge_dicts(self.yaml_data, scenario_data)

        # Build a map of default simulator configurations by model_type
        self.build_defaults_map()

        self.load_scenario()     # Load scenario settings
        self.load_simulators()   # Load simulators and models
        self.load_connections()  # Load connections
        self.load_monitors()     # Load monitors

    def merge_dicts(self, a, b):
        """
        Recursively merge dictionary b into dictionary a.
        If there is a conflict, values from b overwrite those from a.
        """
        for key, value in b.items():
            if key in a and isinstance(a[key], dict) and isinstance(value, dict):
                self.merge_dicts(a[key], value)
            else:
                a[key] = value

    def build_defaults_map(self):
        self.defaults_map = {}
        for sim_conf in self.defaults_data.get('simulators', []):
            model_type = sim_conf['model_type']
            self.defaults_map[model_type] = sim_conf

    def load_scenario(self):
        self.scenario = self.yaml_data.get('scenario', 'DefaultScenario')
        self.start_time = self.yaml_data.get('start_time', '2012-01-01 00:00:00')
        self.end_time = self.yaml_data.get('end_time', 1440)

        # Convert start_time to datetime if necessary
        if isinstance(self.start_time, str):
            self.start_time = datetime.fromisoformat(self.start_time)

    def load_simulators(self):
        available_models = self.get_model_files()
        self.simulators = {}  # Key: model name, value: model data

        for sim_conf in self.yaml_data.get('simulators', []):
            model_type = sim_conf['model_type']
            model_mode = sim_conf.get('model_mode', 'hybrid')
            step_size = sim_conf.get('step_size', 1)  # Default step size if not specified
            model_path = available_models.get(model_type.lower(), None)

            # Get default simulator configuration for this model_type
            default_sim_conf = self.defaults_map.get(model_type, {})

            # Merge default simulator configuration with scenario-specific configuration
            merged_sim_conf = {}
            self.merge_dicts(merged_sim_conf, default_sim_conf)
            self.merge_dicts(merged_sim_conf, sim_conf)

            # Process models
            models = merged_sim_conf.get('models', [])
            if not models:
                # If no models defined, create one default model
                models = [{'name': model_type + '_default'}]

            for model_conf in models:
                model_name = model_conf['name']

                # Initialize model_data with common attributes
                model_data = {
                    'model_type': model_type,
                    'model_mode': model_mode,
                    'step_size': step_size,
                    'model_path': model_path,
                    'start_time': self.start_time,
                }

                # Merge attributes (Inputs, Outputs, Parameters, etc.) from defaults and model_conf
                for attr in ['Inputs', 'Outputs', 'Parameters', 'States', 'Triggers', 'Scenario_File']:
                    default_attr = merged_sim_conf.get(attr)
                    model_attr = model_conf.get(attr)
                    if isinstance(default_attr, dict) and isinstance(model_attr, dict):
                        merged_attr = {}
                        self.merge_dicts(merged_attr, default_attr)
                        self.merge_dicts(merged_attr, model_attr)
                    else:
                        # Use model_attr if it's not None; otherwise, default_attr; otherwise, empty dict
                        merged_attr = model_attr if model_attr is not None else default_attr
                        if merged_attr is None and attr != 'Scenario_File':
                            merged_attr = {}

                    model_data[attr.lower()] = merged_attr

                # Generate meta data
                meta = self.generate_meta(model_data)
                model_data['meta'] = meta

                self.simulators[model_name] = model_data

    def generate_meta(self, model_data):
        inputs = set((model_data.get('inputs') or {}).keys())
        outputs = set((model_data.get('outputs') or {}).keys())
        parameters = set((model_data.get('parameters') or {}).keys())
        states = set((model_data.get('states') or {}).keys())
        triggers = set((model_data.get('triggers') or {}).keys())

        models_meta = {
            "Model": {
                'public': True,
                'params': list(parameters | states),
                'attrs': list(inputs | outputs | states | triggers),
                'any_inputs': False,
                'trigger': list(triggers),
            }
        }

        meta = {
            'api_version': '3.0',
            'type': model_data.get('model_mode', 'hybrid'),
            'models': models_meta,
        }
        return meta

    def load_connections(self):
        self.connections = []
        for conn_conf in self.yaml_data.get('connections', []):
            from_str = conn_conf['from']
            to_str = conn_conf['to']

            # from: source_model.attribute
            # to: dest_model.attribute
            from_model_attr = from_str.split('.')
            to_model_attr = to_str.split('.')
            if len(from_model_attr) != 2 or len(to_model_attr) != 2:
                print(f"Invalid connection format: {conn_conf}")
                continue

            from_model, from_attr = from_model_attr
            to_model, to_attr = to_model_attr

            connection = {
                'from_model': from_model,
                'from_attr': from_attr,
                'to_model': to_model,
                'to_attr': to_attr,
            }

            self.connections.append(connection)

    def load_monitors(self):
        self.monitors = []
        for monitor_str in self.yaml_data.get('monitor', []):
            # monitor_str is in the format 'ModelName.Attribute'
            model_attr = monitor_str.split('.')
            if len(model_attr) != 2:
                print(f"Invalid monitor format: {monitor_str}")
                continue

            model_name, attr_name = model_attr
            monitor = {
                'model_name': model_name,
                'attribute': attr_name,
            }
            self.monitors.append(monitor)

    @staticmethod
    def get_model_files(models_folder='Models'):
        """
        Get a dictionary of available model names and their corresponding file paths.
        """
        model_files = {}
        # Ensure the Models folder exists
        if not os.path.isdir(models_folder):
            print(f"The folder '{models_folder}' does not exist.")
            return model_files

        # List all files in the Models folder
        for filename in os.listdir(models_folder):
            # Check if the file matches the pattern *_model.py
            if filename.endswith('_model.py'):
                # Extract the model_name from the filename
                model_name = filename[:-len('_model.py')]
                # Get the full file path
                file_path = os.path.join(models_folder, filename)
                # Add the model_name and file_path to the dictionary
                model_files[model_name.lower()] = file_path

        return model_files

    @staticmethod
    def load_yaml(file_path):
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        return data

if __name__ == "__main__":
    interpreter = YamlInterpreter('example_scenario.yaml')
    print(interpreter.scenario)
    print(interpreter.start_time)
    print(interpreter.end_time)
    print(interpreter.simulators)
    print(interpreter.connections)
    print(interpreter.monitors)
