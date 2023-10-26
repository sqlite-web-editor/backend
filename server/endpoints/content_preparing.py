from io import BytesIO

def prepare_int_to_string(content: dict):
    indices = []
    data = []
    for column in content["columns"]:
        if column["type"] == "INTEGER":
            indices.append(column["cid"])

    for row in content["data"]:
        row_data = []
        for index, value in enumerate(row):
            if index in indices:
                value = str(value)
            row_data.append(value)
        data.append(row_data)

    content["data"] = data
    return content


def prepare_blob(content: dict):
    indices = []
    data = []
    for column in content["columns"]:
        if column["type"] == "BLOB":
            indices.append(column["cid"])

    for row in content["data"]:
        row_data = []
        for index, value in enumerate(row):
            if index in indices:
                value = ""
            row_data.append(value)
        data.append(row_data)

    content["data"] = data
    return content