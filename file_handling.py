import os
import csv
import json



def write_to_csv(data, filename='output.csv' ):
    """
    Save data to output.csv in proper CSV format.
    data should be a list of tuples/lists like [(domain, registrar), ...]
    """
    file_exists = os.path.isfile(filename)
    print(f"\n+++ Writing results to {filename} +++\n")

    with open(filename, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Write header only if file is new
        if not file_exists:
            writer.writerow(["Domain", "Registrar"])
        # Write the data
        writer.writerows(data)

    
def write_to_json(data, filename="output.json"):
    """
    Save data to JSON without overwriting existing content.
    data should be a dict: {domain: registrar, ...}
    """
    print(f"\n+++ Writing results to {filename} +++\n")

    # Load existing JSON if file exists
    if os.path.isfile(filename):
        with open(filename, "r", encoding="utf-8") as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                existing_data = {}
    else:
        existing_data = {}

    # Merge new data into existing
    existing_data.update(data)

    # Write back merged data
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=4, ensure_ascii=False)   


def get_existing_data(format_chosen):
    """
    Load existing domain-registrar data from CSV or JSON, returning a list of tuples.
    Returns an empty list if the file does not exist.
    """
    file_path = f"output.{format_chosen}"

    if not os.path.exists(file_path):
        return []

    if format_chosen == "csv":
        data = []
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            next(reader, None)  # skip header if present
            for row in reader:
                if len(row) >= 2:
                    data.append((row[0].strip(), row[1].strip()))
        return data

    elif format_chosen == "json":
        with open(file_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)
        # Convert dict to list of tuples
        return [(k, v) for k, v in json_data.items()]