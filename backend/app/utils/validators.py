def validate_request(data, fields):
    return all(field in data for field in fields)
