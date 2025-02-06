import json
from typing import Any, Dict, List, Set, Union
from collections import Counter

def read_json_file(file_path: str) -> Any:
    """
    Read and parse JSON from a file.
    Raises FileNotFoundError if file doesn't exist.
    Raises json.JSONDecodeError if file contains invalid JSON.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()

def normalize_json(obj: Any, skip_keys: Set[str] = set()) -> Any:
    """
    Recursively normalize JSON objects/arrays for comparison,
    ignoring specified keys.
    """
    if isinstance(obj, dict):
        # Create new dict excluding skipped keys and normalize remaining values
        result = {}
        for k, v in sorted(obj.items()):
            if k not in skip_keys:
                result[k] = normalize_json(v, skip_keys)
        return result
    elif isinstance(obj, list):
        # Sort lists of dictionaries by their normalized string representation
        if all(isinstance(x, dict) for x in obj):
            result = []
            for x in obj:
                normalized_x = normalize_json(x, skip_keys)
                result.append(normalized_x)
            
            result.sort(key=lambda x: json.dumps(x, sort_keys=True))
            return result
        # For simple lists, just sort the normalized values
        return sorted(normalize_json(x, skip_keys) for x in obj)
    return obj

def compare_json_responses(response1: str, response2: str, skip_keys: List[str] = []) -> Dict[str, Any]:
    """
    Compare two JSON response strings, ignoring order of items and keys.
    Returns a detailed comparison report.
    """
    try:
        json1 = json.loads(response1)
        json2 = json.loads(response2)
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON format: {str(e)}"}
    
    # Convert skip_keys to set for faster lookup
    skip_keys_set = set(skip_keys)

    # Normalize both JSON objects
    normalized1 = normalize_json(json1, skip_keys_set)
    normalized2 = normalize_json(json2, skip_keys_set)

    # Initialize comparison results
    results = {
        "are_equal": normalized1 == normalized2,
        "differences": [],
        "stats": {
            "total_items_v1": 0,
            "total_items_v2": 0,
            "missing_in_v2": [],
            "new_in_v2": []
        }
    }

    def count_items(obj: Any) -> int:
        """Count total number of items in JSON structure"""
        count = 1
        if isinstance(obj, dict):
            return count + sum(count_items(v) for v in obj.values())
        elif isinstance(obj, list):
            return count + sum(count_items(item) for item in obj)
        return count

    def find_differences(path: str, obj1: Any, obj2: Any) -> None:
        """Recursively find and record differences between JSON objects"""
        if isinstance(obj1, dict) and isinstance(obj2, dict):
            keys1, keys2 = set(obj1.keys()), set(obj2.keys())
            
            # Find missing and new keys
            for key in keys1 - keys2:
                results["differences"].append(f"Key '{key}' at '{path}' missing in version 2")
                results["stats"]["missing_in_v2"].append(f"{path}.{key}")
            
            for key in keys2 - keys1:
                results["differences"].append(f"Key '{key}' at '{path}' is new in version 2")
                results["stats"]["new_in_v2"].append(f"{path}.{key}")
            
            # Recurse into common keys
            for key in keys1 & keys2:
                new_path = f"{path}.{key}" if path else key
                find_differences(new_path, obj1[key], obj2[key])
        
        elif isinstance(obj1, list) and isinstance(obj2, list):
            # For lists, compare lengths and contents
            if len(obj1) != len(obj2):
                results["differences"].append(
                    f"Array length mismatch at '{path}': {len(obj1)} vs {len(obj2)}"
                )
            
            # Compare normalized versions of lists
            norm1 = normalize_json(obj1)
            norm2 = normalize_json(obj2)

            json_data1 = json.loads(json.dumps(norm1))
            with open("norm1.json", "w", encoding="utf-8") as f:
                json.dump(json_data1, f, indent=4)
            json_data2 = json.loads(json.dumps(norm2))
            with open("norm2.json", "w", encoding="utf-8") as f:
                json.dump(json_data2, f, indent=4)
            
            if norm1 != norm2:
                results["differences"].append(
                    f"Array contents differ at '{path}'"
                )
        
        elif obj1 != obj2:
            results["differences"].append(
                f"Value mismatch at '{path}': {obj1} vs {obj2}"
            )

    # Calculate statistics
    results["stats"]["total_items_v1"] = count_items(normalized1)
    results["stats"]["total_items_v2"] = count_items(normalized2)

    # Find all differences
    find_differences("", normalized1, normalized2)

    return results

# Example usage
if __name__ == "__main__":
    response1 = read_json_file("compare1.json")
    
    response2 = read_json_file("compare2.json")

    skip_keys = ["TransactionID"]
    
    result = compare_json_responses(response1, response2, skip_keys)
    print(json.dumps(result, indent=2))