import json


def load_json_file(file_path):
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print("\nThe file not found or is invalid.\n")
        return []


def save_json_file(file_path, data):
    with open(file_path, 'w') as f:
        json.dump(data, f, separators=(',', ':'), ensure_ascii=False)


def load_txt_file_to_list(file_path):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()

        lines = [line.strip() for line in lines]
        return lines
    except FileNotFoundError:
        print("\nThe file not found or is invalid.\n")
        return []
