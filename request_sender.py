import requests
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, wait
import pandas as pd
from typing import List, Dict, Any

city_to_id = {
    "Shanghai": "1286269045196331239",
    "Beijing": "1286269045196331238",
    "Shenzhen": "1286269045196331264",
    "Hangzhou": "1286269045196331252",
    "Guangzhou": "1286269045196331266",
    "Chengdu": "1286269045196331263",
    "Chongqing": "1286269045196331241",
    "Changsha": "1286269045196331393",
    "Wuhan": "1286269045196331623",
    "Dubai": "1286269045196331406",
    "Singapore": "1290937685439025152"
}

id_to_city = {
    "1286269045196331239": "Shanghai",
    "1286269045196331238": "Beijing",
    "1286269045196331264": "Shenzhen",
    "1286269045196331252": "Hangzhou",
    "1286269045196331266": "Guangzhou",
    "1286269045196331263": "Chengdu",
    "1286269045196331241": "Chongqing",
    "1286269045196331393": "Changsha",
    "1286269045196331623": "Wuhan",
    "1286269045196331406": "Dubai",
    "1290937685439025152": "Singapore"
}

class FlightAPITester:
    def __init__(self):
        self.base_url_old = "https://travel-pre.bytedance.net/api/bff/flight/item/flightList"
        self.base_url_new = "https://travel-pre.bytedance.net/api/bff/flight/item/flightList"  # Update with new endpoint
        self.headers_old = {
            'content-type': 'application/json;charset=UTF-8',
            'Cookie': 'TRAVEL_SESSION=YmExNzQwNzAtNzQwOS00NDlkLWI5MGUtNTQyMGJkY2NkNzI0',
            'origin': 'https://travel-pre.bytedance.net',
            'x-use-ppe': '1',
            'x-tt-env': 'ppe_master_flight',
            'x-lang': 'en-US'
        }
        self.headers_new = {
            'content-type': 'application/json;charset=UTF-8',
            'Cookie': 'TRAVEL_SESSION=YmExNzQwNzAtNzQwOS00NDlkLWI5MGUtNTQyMGJkY2NkNzI0',
            'origin': 'https://travel-pre.bytedance.net',
            'x-use-ppe': '1',
            'x-tt-env': 'ppe_flight_optimization',
            'x-lang': 'en-US'
        }
        raw_routes = [
            # "Dubai Singapore"
            "Shanghai Beijing", "Beijing Shanghai", "Shenzhen Beijing", "Hangzhou Beijing", "Beijing Shenzhen",
            "Beijing Hangzhou", "Guangzhou Beijing", "Beijing Guangzhou", "Chengdu Beijing", "Shenzhen Shanghai",
            "Beijing Chengdu", "Shanghai Shenzhen", "Guangzhou Shanghai", "Shanghai Guangzhou", "Shenzhen Hangzhou",
            "Chengdu Shanghai", "Chongqing Beijing", "Hangzhou Shenzhen", "Shanghai Chengdu", "Beijing Chongqing",
            "Guangzhou Hangzhou", "Changsha Beijing", "Hangzhou Guangzhou", "Hangzhou Shanghai", "Wuhan Beijing"
        ]
        self.routes = [
            {
                "departureCityRegionCode": city_to_id[raw_route.split(" ")[0]],
                "departureAirportCode": "",
                "arrivalCityRegionCode": city_to_id[raw_route.split(" ")[1]],
                "arrivalAirportCode": "",
            } for raw_route in raw_routes
        ]

    def get_request_payload(self, route: Dict[str, str], date: str) -> Dict[str, Any]:
        return {
            "flightInfo": {
                "seatClass": 2,
                "tripType": 1,
                "seatClassList": [2],
                "selectedPassengers": [
                    {
                        "passengerType": 1,
                        "userType": 1,
                        "passengerID": "8816510",
                        "nationalityCode": "KZ"
                    }
                ]
            },
            "routeInfos": [
                {
                    **route,
                    "departureDate": date
                }
            ],
            "flightSegmentControl": None,
            "segment": 1,
            "supplierType": None,
            "flightDataSource": 1,
            "chinaDomestic": True,
            "Lang": "en-US",
            "peoplecompanyidforbooking": "",
            "transactionID": ""
        }
    
    def to_curl(self, url, headers, payload):
        command = f"curl -X POST '{url}' \\\n"
        
        # Add headers
        for header, value in headers.items():
            command += f"  -H '{header}: {value}' \\\n"
        
        # Add json payload
        import json
        command += f"  -d '{json.dumps(payload)}'"
        
        return command
    
    def is_success(self, resp: requests.Response) -> bool:
        body = resp.json()
        return body["code"] == "200" and len(body.get("data", {}).get("flights", [])) > 0

    def make_request(self, url: str, headers: Dict[str, str], route: Dict[str, str], date: str, endpoint: str) -> Dict[str, Any]:
        payload = self.get_request_payload(route, date)
        start_time = time.time()
        try:
            response = requests.post(url, headers=headers, json=payload)
            response.raise_for_status()
            return {
                "success": self.is_success(response),
                "response_time": time.time() - start_time,
                "status_code": response.json()["code"],
                "route": f"{id_to_city[route['departureCityRegionCode']]} -> {id_to_city[route['arrivalCityRegionCode']]}",
                "date": date,
                "endpoint": endpoint,
                "flightCount": len(response.json().get("data", {}).get("flights", [])),
                "logid": response.headers.get('X-Tt-Logid')
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "response_time": time.time() - start_time,
                "error": str(e),
                "route": f"{id_to_city[route['departureCityRegionCode']]} -> {id_to_city[route['arrivalCityRegionCode']]}",
                "date": date,
                "endpoint": endpoint,
                "logid": response.headers.get('X-Tt-Logid')
            }

    def test_route(self, route: Dict[str, str], num_requests: int = 2) -> List[Dict[str, Any]]:
        results = []
        start_date = datetime(2025, 8, 20)
        for i in range(num_requests):
            date = (start_date + timedelta(days=i % 30)).strftime("%Y-%m-%d")
            
            # Create a ThreadPoolExecutor for parallel requests
            with ThreadPoolExecutor(max_workers=2) as executor:
                # Submit both requests to run in parallel
                future_old = executor.submit(
                    self.make_request, 
                    self.base_url_old, 
                    self.headers_old, 
                    route, 
                    date, 
                    "old"
                )
                future_new = executor.submit(
                    self.make_request, 
                    self.base_url_new, 
                    self.headers_new, 
                    route, 
                    date, 
                    "new"
                )
                
                # Wait for both requests to complete
                wait([future_old, future_new])
                
                # Get results
                results.append(future_old.result())
                results.append(future_new.result())
            
            # Small delay between iterations
            time.sleep(15)
            
        return results

    def run_tests(self) -> None:
        all_results = []
        
        # Use ThreadPoolExecutor for parallel processing of routes
        with ThreadPoolExecutor(max_workers=5) as executor:
            future_to_route = {executor.submit(self.test_route, route): route for route in self.routes}
            
            for future in future_to_route:
                results = future.result()
                all_results.extend(results)

        # Convert results to DataFrame for analysis
        df = pd.DataFrame(all_results)
        
        # Save detailed results to CSV
        df.to_csv('flight_api_test_results.csv', index=False)
        print("\nDetailed results saved to 'flight_api_test_results.csv'")

if __name__ == "__main__":
    tester = FlightAPITester()
    tester.run_tests()