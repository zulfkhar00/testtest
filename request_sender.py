import aiohttp
import asyncio
import json
from typing import List, Dict
import time

def sort_json_recursively(data):
    """Sort JSON data recursively."""
    if isinstance(data, dict):
        return {k: sort_json_recursively(v) for k, v in sorted(data.items())}
    elif isinstance(data, list):
        return [sort_json_recursively(x) for x in data]
    else:
        return data

def sort_json(json_data: Dict) -> Dict:
    """Sort JSON data and return sorted version."""
    return sort_json_recursively(json_data)

async def make_request(session: aiohttp.ClientSession, payload: Dict) -> Dict:
    """Make a single request with the given payload"""
    url = 'https://travel-pre.bytedance.net/api/bff/flight/item/flightList'
    headers = {
        'content-type': 'application/json;charset=UTF-8',
        'Cookie': 'TRAVEL_SESSION=YmExNzQwNzAtNzQwOS00NDlkLWI5MGUtNTQyMGJkY2NkNzI0; CICD-GRAY-TENANT=MmUyZTRlOWE5MThmMTY1MA==; CICD-GOOFY-SESSION=ODYzODAwMA==; EA-LANE-TENANTID=2e2e4e9a918f1650; SPEND_AUTH_EMPLOYEE_UNION_ID=U1298515983643709440; SPEND_AUTH_TENANT_KEY=2e2e4e9a918f1650; TRAVEL_AUTH_CLUSTER=default; TRAVEL_SESSION=NDk1NTY4NzUtZWNmNS00MmE0LWIyNDAtNzVmZDUyMzYzZjMw',
        'origin': 'https://travel.bytedance.net',
        'x-use-ppe': '1',
        'x-tt-env': 'ppe_master_temp',
        'x-lang': 'en-US'
    }

    try:
        async with session.post(url, json=payload, headers=headers) as response:
            resp = await response.json()
            return sort_json(resp)
    except Exception as e:
        print(f"Error making request: {e}")
        return None

async def process_pair(session: aiohttp.ClientSession, payloads: List[Dict], pair_index: int) -> None:
    """Process a pair of requests in parallel"""
    print(f"Processing pair {pair_index + 1}")
    
    # Create tasks for both requests
    tasks = [
        asyncio.create_task(make_request(session, payload))
        for payload in payloads
    ]
    
    # Wait for both requests to complete
    responses = await asyncio.gather(*tasks)
    
    # Save responses
    for i, response in enumerate(responses):
        if response:
            filename = f'responses/response_{pair_index}_{i}.json'
            with open(filename, 'w') as f:
                json.dump(response, f, indent=2)
            print(f"Saved response to {filename}")

async def main(input_file: str):
    """Main function to process the input file"""
    # Read all payloads from file
    payloads = []
    with open(input_file, 'r') as f:
        for line in f:
            try:
                payload = json.loads(line.strip())
                payloads.append(payload)
            except json.JSONDecodeError as e:
                print(f"Error parsing JSON line: {e}")
                continue

    # Process payloads in pairs
    async with aiohttp.ClientSession() as session:
        for i in range(0, len(payloads), 5):
            # Get current pair of payloads
            current_pair = payloads[i:i + 5]
            
            # Process the pair
            await process_pair(session, current_pair, i // 5)
            
            # Wait 5 seconds if this isn't the last pair
            if i + 5 < len(payloads):
                print("Waiting 5 seconds before next pair...")
                await asyncio.sleep(5)

if __name__ == "__main__":
    # Replace with your input file name
    input_file = "diff_testing/output_requests_ctrip.json"
    
    # Run the async main function
    asyncio.run(main(input_file))