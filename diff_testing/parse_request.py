import json
import re

auth_token = "Bearer @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"

def parse_log_file(input_file, output_file):
    req_pattern = r'req=\[(.*?)\] persistent='
    
    with open(input_file, 'r') as f_in, open(output_file, 'w') as f_out:
        for line in f_in:
            # Find req content
            match = re.search(req_pattern, line)
            if match:
                req_content = match.group(1)
                try:
                    # Parse the content as JSON
                    json_data = json.loads(req_content)
                    json_data["authToken"] = auth_token
                    json_data["flightInfo"]["selectedPassengers"] = [{
                        "passengerType": 1,
                        "userType": 1,
                        "passengerID": "8816510",
                        "nationalityCode": "KZ"
                    }]

                    # Write to output file with newline
                    f_out.write(json.dumps(json_data) + '\n')
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON: {e}")
            else:
                print(f"No req pattern found in line")

# Example usage
if __name__ == "__main__":
    parse_log_file('argos-input.txt', 'output_requests.json')