


from os import path
import json

import Config
from meta_tasks.ContigencyTetrahedron import ContigencyTetrahedronConfig


led_water_path = path.join(Config.METATASK_DIR, "ContigencyTetrahedron", "LED_Water.json")
puff_water_path = path.join(Config.METATASK_DIR, "ContigencyTetrahedron", "Puff_Water.json")
acclimation_water_path = path.join(Config.METATASK_DIR, "ContigencyTetrahedron", "ACC.json")


def recursive_replace(obj, old, new):
    if isinstance(obj, dict):
        return {k: recursive_replace(v, old, new) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [recursive_replace(v, old, new) for v in obj]
    elif obj == old:
        return new
    return obj

def custom_json_loader(module_name: str):
    ct_config = ContigencyTetrahedronConfig.parse(module_name)
    print(f"\nParsed module: {module_name}\nConfig: {ct_config}\n")

    if ct_config.task == "LW":
        with open(led_water_path, "r") as file:
            module_json = json.load(file)  
    elif ct_config.task == "PW":
        with open(puff_water_path, "r") as file:
            module_json = json.load(file)  
    elif ct_config.task == "ACC":
        with open(acclimation_water_path, "r") as file:
            module_json = json.load(file)  
    else:
        raise ValueError(f"Unknown task: {ct_config.task}")

    ct_prob = ct_config.joint_probabilities
    module_json = recursive_replace(module_json, "AAA", ct_prob[0])
    module_json = recursive_replace(module_json, "BBB", ct_prob[1])
    module_json = recursive_replace(module_json, "CCC", ct_prob[2])
    module_json = recursive_replace(module_json, "DDD", ct_prob[3])
    
    return module_json

    