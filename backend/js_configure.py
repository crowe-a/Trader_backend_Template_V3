import json
import os

DATA_PATH = "activs.json"

# JSON dosyasını oku (yoksa boş liste döner)
def read_data():
    if not os.path.exists(DATA_PATH):
        return []
    with open(DATA_PATH, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

# JSON dosyasına yaz
def write_data(data):
    with open(DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Yeni kayıt ekle
def add_record(record):
    data = read_data()
    data.append(record)   # iç içe tuple/list ekleme
    write_data(data)
    print("Yeni kayıt eklendi:", record)

# Belirli index’teki kaydı getir
def get_record(index):
    data = read_data()
    if 0 <= index < len(data):
        return data[index]
    return None

# Tüm kayıtları getir
def get_all_records():
    return read_data()

def update_last_fields(runner_id, open_price, amount, profit, remaining_time):
    data = read_data()
    updated = False

    for record in data:
        if record[0] == runner_id:  # Runner_id eşleşirse
            record[-4] = open_price
            record[-3] = amount
            record[-2] = profit
            record[-1] = remaining_time
            updated = True
            break

    if updated:
        write_data(data)
        print(f"{runner_id} için son 4 alan güncellendi.")
    else:
        print(f"{runner_id} bulunamadı.")

def reset_json_file(file_path):
    # Dosyayı açıp boş bir liste yazıyoruz
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump([], f, indent=4)