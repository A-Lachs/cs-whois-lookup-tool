import os
import csv
import json

def process_and_save_new_data(new_data: list[tuple]):
    """
    Handles saving of new domain registrar data.
    
    - Deduplicates new data (safety check)
    - Prompts user for output format (CSV, JSON, or None)
    - Loads existing data and avoids duplicates
    - Writes only unique new data to the chosen format, or skips saving

    Args:
        new_data (list[tuple]): List of tuples containing registrar info
    """
    if not new_data:
        print("\n    - No new data to process ")
        return

    # Deduplicate new data (safety check)
    deduped_new_data = list(set(new_data))

    # Ask user for desired output format (CSV, JSON, or None)
    format_choice = ask_output_file_format()  # Should return "csv", "json", or "none"

    if format_choice.lower() == "none":
        print("+++ Skipping saving of data as per user choice.")
        return

    # Load existing data from file
    existing_data = get_existing_data(format_choice) or []

    # Deduplicate against existing data
    unique_data_to_save = list(set(deduped_new_data) - set(existing_data))

    if not unique_data_to_save:
        print("\n+++ No unique new data to save. +++")
        return

    # Save to chosen format
    if format_choice.lower() == "csv":
        write_to_csv(unique_data_to_save)
    else:
        write_to_json(unique_data_to_save)

    print(f"\n+++ Saved {len(unique_data_to_save)} new entries to {format_choice.upper()} file. +++")


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


def ask_output_file_format() -> str:
    """
    Ask the user which output format they want.
    Options:
      - 'csv' (default)
      - 'json'
      - 'skip' to not save the data

    Returns:
        str: One of 'csv', 'json', or 'none' (skip saving)
    """
    print("\n+++ How to save the results? +++\n")
    print("    Press Enter for default format CSV")
    print("    Type 'json' to change format")
    print("    Type 'skip' to finish without saving")
    
    choice = input("\n    Your choice: ").strip().lower()

    if choice == "json":
        return "json"
    elif choice == "skip":
        return "none"
    else:
        return "csv"


def write_to_csv(data, filename='output.csv' ):
    """
    Save data to output.csv in proper CSV format.
    data should be a list of tuples/lists like [(domain, registrar), ...]
    """
    file_exists = os.path.isfile(filename)
    # print(f"\n+++ Writing results to {filename} +++\n")

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
    `data` should be a dict: {domain: registrar, ...}
    """
    # print(f"\n+++ Writing results to {filename} +++\n")

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