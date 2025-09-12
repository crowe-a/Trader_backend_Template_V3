import json
import os

DATA_PATH = "activs.json"

# read JSON  (if its null return None)
def read_data():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

# write JSON 
def write_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# add 
def add_record(record):
    data = read_data()
    data.append(record)   # 
    write_data(data)
    print("new record added:", record)

# check index
def get_record(index):
    data = read_data()
    if 0 <= index < len(data):
        return data[index]
    return None

# get all recrods
def get_all_records():
    return read_data()

def update_last_fields(runner_id, open_price, amount, profit, remaining_time):
    data = read_data()
    updated = False

    for record in data:
        if record[0] == runner_id:  # Runner_id 
            record[-4] = open_price
            record[-3] = amount
            record[-2] = profit
            record[-1] = remaining_time
            updated = True
            break

    if updated:
        write_data(data)
        print(f"{runner_id} 4 parametre revised.")
    else:
        print(f"{runner_id} not found.")

def reset_json_file(file_path):
    # 
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump([], f, indent=4)