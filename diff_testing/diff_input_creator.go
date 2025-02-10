func TestCreateDiffInputs(t *testing.T) {
	inputFile := "/Users/bytedance/Desktop/scripts/diff_testing/output_requests.json"
	outputFile := "/Users/bytedance/Desktop/scripts/diff_testing/diff-inputs.txt"

	// Open the input file
	file, err := os.Open(inputFile)
	if err != nil {
		fmt.Println("Error opening input file:", err)
		return
	}
	defer file.Close()

	// Create output file
	outFile, err := os.Create(outputFile)
	if err != nil {
		fmt.Println("Error creating output file:", err)
		return
	}
	defer outFile.Close()

	writer := bufio.NewWriter(outFile)
	scanner := bufio.NewScanner(file)

	for scanner.Scan() {
		line := scanner.Text()

		var jsonData map[string]interface{}
		if err := json.Unmarshal([]byte(line), &jsonData); err != nil {
			fmt.Println("Error unmarshalling JSON:", err)
			continue
		}
		jsonBytes, err := json.Marshal(jsonData)
		if err != nil {
			fmt.Println("Error marshaling map:", err)
			return
		}
		var flightListQueryReq *flight_item.FlightListQueryRequest
		err = json.Unmarshal(jsonBytes, &flightListQueryReq)
		if err != nil {
			fmt.Println("Error unmarshaling JSON:", err)
			return
		}

		formattedData, err := CustomMarshal(flightListQueryReq)
		if err != nil {
			fmt.Println("Error formatting JSON:", err)
			continue
		}

		outputJSON := map[string]interface{}{
			"method":       "QueryFlightList",
			"data":         formattedData,
			"from_psm":     "ea.expense.travel_bff",
			"from_cluster": "default",
			"from_idc":     "mycisb",
		}

		finalOutput, err := json.Marshal(outputJSON)
		if err != nil {
			fmt.Println("Error marshalling final JSON:", err)
			continue
		}

		writer.WriteString(string(finalOutput) + "\n")
	}

	if err := scanner.Err(); err != nil {
		fmt.Println("Error reading file:", err)
	}

	writer.Flush()
}

func CustomMarshal(v interface{}) (string, error) {
	val := reflect.ValueOf(v)
	m := convertValue(val)
	jsonData, err := json.Marshal(m)
	if err != nil {
		return "", err
	}
	return string(jsonData), nil
}

func convertValue(val reflect.Value) interface{} {
	for val.Kind() == reflect.Ptr {
		if val.IsNil() {
			return nil
		}
		val = val.Elem()
	}

	switch val.Kind() {
	case reflect.Struct:
		return convertStruct(val)
	case reflect.Slice, reflect.Array:
		return convertSliceOrArray(val)
	case reflect.Map:
		return convertMap(val)
	default:
		return val.Interface()
	}
}

func convertStruct(val reflect.Value) map[string]interface{} {
	typ := val.Type()
	data := make(map[string]interface{})

	for i := 0; i < val.NumField(); i++ {
		field := typ.Field(i)
		fieldVal := val.Field(i)
		key := field.Name
		data[key] = convertValue(fieldVal)
	}
	return data
}

func convertSliceOrArray(val reflect.Value) []interface{} {
	length := val.Len()
	result := make([]interface{}, length)
	for i := 0; i < length; i++ {
		result[i] = convertValue(val.Index(i))
	}
	return result
}

func convertMap(val reflect.Value) map[string]interface{} {
	result := make(map[string]interface{})
	for _, key := range val.MapKeys() {
		mapKey, ok := key.Interface().(string)
		if !ok {
			continue
		}
		mapVal := val.MapIndex(key)
		result[mapKey] = convertValue(mapVal)
	}
	return result
}