import json
import uuid
import globals
from datetime import datetime

class DataCollector:
    def __init__(self, ):
        self._save_dir = globals.args.results_dir # saves the json file here
        self._data_table = {
            'time_slot': [],
            'src_name': [],
            'dst_name': [],
            'path': [],
            'fidelity': [],
            'num_eprs_used': [],
            'num_eprs_created': [],
            'x_dist': [],
            'y_dist': [],
        }

    def add_data(self, ts, src_name, dst_name, path, fidelity, num_eprs_used, num_eprs_created, x_dist, y_dist):
        self._data_table['time_slot'].append(ts)
        self._data_table['src_name'].append(src_name)
        self._data_table['dst_name'].append(dst_name)
        self._data_table['path'].append(path)
        self._data_table['fidelity'].append(fidelity)
        self._data_table['num_eprs_used'].append(num_eprs_used)
        self._data_table['num_eprs_created'].append(num_eprs_created)
        self._data_table['x_dist'].append(x_dist)
        self._data_table['y_dist'].append(y_dist)

    def save_results(self):
        filename = globals.args.results_file
        filename = f"{str(uuid.uuid4())}.json" if filename == '' else filename
        timestamp = datetime.now().strftime("%d/%B/%Y %H:%M:%S")
        file_contents = {
            "results_generated": timestamp,
            "params_used": self._args_as_dict(),
            "results": self._data_table
        }
        json_obj = json.dumps(file_contents, indent=4)
        with open(f"{self._save_dir}/{filename}", "w") as f:
            f.write(json_obj)

        print(f"results saved to {self._save_dir}{filename} with timestamp {timestamp}.")

    def _args_as_dict(self):
        remove_list = ['help', 'config_file', 'results_dir', 'results_file']
        args_dict = vars(globals.args)
        
        for k in remove_list:
            args_dict.pop(k, None)

        # this works fine but it is too static. making any changes would affect this. so not doing it like this anymore. loop below is a better way to do this.
        # enums_list = ['network', 'alg', 'yen_metric', 'qc_noise_model', 'qc_loss_model', 'qc_delay_model', 'cc_delay_model', 'cc_loss_model', 'qm_noise_model']
        # for k in enums_list:
        #     args_dict[k] = args_dict[k].value
        
        for k in args_dict.keys():
            if isinstance(args_dict[k], globals.Enum): # save the value string of enums
                args_dict[k] = args_dict[k].value
            
            if args_dict[k] == float('inf'): # infinity cannot be stored in json. so we are using -1 as an alias for infinity
                args_dict[k] = -1

        return args_dict