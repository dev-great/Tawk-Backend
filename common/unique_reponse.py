def process_data(data_list):
    processed_data = list(set(item.capitalize() for item in data_list))
    return processed_data
