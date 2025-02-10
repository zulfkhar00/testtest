def sort_json_recursively(data):
    if isinstance(data, dict):
        return {k: sort_json_recursively(v) for k in sorted(data.keys()) for v in [data[k]]}
    elif isinstance(data, list):
        return [sort_json_recursively(item) for item in data]
    return data

# Example usage:
import json

def sort_json_file(filename = "cabinList1.json"):
    with open(filename, 'r') as f:
        data = json.load(f)
    
    sorted_data = sort_json_recursively(data)
    
    with open(filename, 'w') as f:
        json.dump(sorted_data, f, indent=2)

sort_json_file()