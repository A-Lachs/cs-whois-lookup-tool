# ----------------------- Imports ---------------------------------------------

import whois  # pip install python-whois
import os
import time 
import sys
import re
import idna  # pip install idna
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import csv 

MAX_WORKERS = 5  # concurrency cap

# ---------------------- Utility Functions ------------------------------------

def get_registrar(domain_link: str, sleep_time: float = 1.0, verbose: bool = True, retries: int = 2) -> tuple[str, str]:
    """
    Look up the registrar for a given domain using the WHOIS library.

    This function:
        - Normalizes the domain to punycode for international domains.
        - Queries the WHOIS database.
        - Extracts the registrar using the helper `extract_registrar`.
        - Supports retrying the lookup if errors occur.
        - Optionally prints progress messages.
    
    Args:
        domain_link (str): The domain name to look up (e.g., 'example.com').
        sleep_time (float, optional): Time to sleep before each WHOIS request in seconds. Default is 1.0.
        verbose (bool, optional): If True, prints status messages for each domain. Default is True.
        retries (int, optional): Number of additional attempts if the WHOIS lookup fails. Default is 2.
    
    Returns:
        tuple[str, str]: A tuple containing:
            - The domain name (str).
            - The registrar name (str) or an error message if the lookup failed.
    
    Notes:
        - Errors are truncated to the first line for readability.
    """
    for attempt in range(1, retries + 2):
        try:
            if sleep_time > 0:
                time.sleep(sleep_time)

            # Convert domain to punycode (ASCII) to handle international domains
            ascii_domain = idna.encode(domain_link).decode("ascii")

            # Perform WHOIS lookup
            domain_info = whois.whois(ascii_domain)

            # Extract registrar using the helper function
            registrar = extract_registrar(domain_info)

            if verbose:
                print(f"\n     {domain_link} -> OK: {registrar}")
            return domain_link, registrar

        except idna.IDNAError as e:
            # Handle punycode conversion errors separately
            error_msg = f"IDNA error: {str(e).splitlines()[0].strip()}"
            if verbose:
                print(f"\n    {domain_link} -> Error: {error_msg}")

            return domain_link, error_msg

        except Exception as e:
            # Handle other WHOIS-related errors
            short_error = str(e).splitlines()[0].strip()
            if verbose:
                print(f"\n    {domain_link} -> Attempt {attempt} failed: {short_error}")
            if attempt == retries + 1:
                # Return error after final retry
                return domain_link, short_error
            

def extract_registrar(domain_info) -> str:
    """
    Helper function used by get_registrar().
    Extract the registrar from a WHOIS object.

    Tries the `registrar` attribute first. If None, searches the raw WHOIS text
    for patterns like "Registrar:", "Sponsoring Registrar:", "Registrar Name:".
    If the registrar is a list, deduplicate and join with "; ".

    Args:
        domain_info: WHOIS result object.

    Returns:
        str: Registrar name(s) or "None" if not found.
    """
    # Get the registrar attribute from the whois object without a type hint
    registrar = getattr(domain_info, "registrar", None)

    # Search raw WHOIS text if registrar is missing
    if not registrar and hasattr(domain_info, "text") and domain_info.text:
        text = domain_info.text
        patterns = [
            r"Registrar\s*:\s*(.+)",
            r"Sponsoring Registrar\s*:\s*(.+)",
            r"Registrar Name\s*:\s*(.+)"
        ]
        found = None
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                found = match.group(1).strip()
                break
        registrar = found or "None"

    # Handle lookups with more than one registrar --> list of registrars
    if isinstance(registrar, list):
        # joining, deduping to return one str
        registrar = "; ".join(sorted(set(r.strip() for r in registrar if r.strip())))

    if not registrar:
        registrar = "None"

    return registrar


def process_domains_concurrently(domain_list):
    print("\n+++ Running domain requests -> registrar +++")
    results = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_domain = {executor.submit(get_registrar, d): d for d in domain_list}
        for future in as_completed(future_to_domain):
            result = future.result()
            results.append(result)
    return results


def interactive_input_mode() -> list[str]:
    """
    Handles interactive input for domain registrar lookup.

    - Continuously prompts the user for domains until 'exit' is typed.
    - Normalizes input using process_input() (removes www., trims, dedupes per input).
    - Returns a list of cleaned, unique domain strings collected during the session.
    """

    print("\n+++ Welcome! Enter one or more domains to check their registrars.\n")
    session_domains = set()  # keep unique domains in this session
    
    while True:
            user_input = input("    Enter domains here (or type 'c' to continue processing): ")
            
            # Check for exit command
            if user_input.strip().lower() == 'c':
                return list(session_domains)  # return all collected domains collected so far
            
            # Process non-empty input 
            if user_input: 
                processed_input = process_input(user_input)

                if processed_input:  # Only proceed if there are valid domains
                    session_domains.update(processed_input)
                    print(f"\n+++ Collected {len(processed_input)} new domain(s). Total so far: {len(session_domains)}")
                else:
                    print("\n+++ No valid domains found. Please try again.\n")            
            else:
                print("\n+++ Invalid input! Please enter one or more domain names or type 'c' to continue.\n")


def process_input(input_given: str| list) -> list[str]:
    """
    Normalize raw input containing domain names into a clean, unique list.

    This function accepts either:
      - a string of domains separated by spaces, commas, semicolons, or pipes
      - a list of such strings

    It removes leading 'www.' prefixes, trims whitespace, normalizes case,
    and returns the domains as a deduplicated list of strings.

    Args:
        input_given (str | list):   Raw input string or list of strings
                                    containing domain names.
    Returns:
        list[str]:                  A list of cleaned domain names.
    """
    
    # If input is a list, join all elements into a single string
    if isinstance(input_given, list):
        input_given = " ".join(input_given)

    if isinstance(input_given, str):  # Non-empty string
        # Replace separators with spaces
        separators = [",", ";", "|"]
        cleaned_input = input_given
        for separator in separators:
            cleaned_input = cleaned_input.replace(separator, " ")

        # Split on spaces, drop extra spaces with strip, normalize to lowercase
        parts = [p.strip().lower() for p in cleaned_input.split(" ") if p.strip()]

        # Strip "www." prefix from each domain
        domains = [p.removeprefix("www.") for p in parts]

        # return a list of unique domains
        return list(set(domains))


def read_or_return(arg: str) -> str | list[str]:
    """
    Attempt to read the argument as a file.
    If the file exists, returns a list of non-empty stripped lines.
    Otherwise, returns the original argument as a string.
    """
    try:
        with open(arg, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return arg  # treat as domain string if file not found


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
        print("+++ No new data to process.")
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
        print("+++ No unique new data to save.")
        return

    # Save to chosen format
    if format_choice.lower() == "csv":
        write_to_csv(unique_data_to_save)
    else:
        write_to_json(unique_data_to_save)

    print(f"+++ Saved {len(unique_data_to_save)} new entries to {format_choice.upper()} file.")


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
    print("\n+++ How to save the results?")
    print("    Press Enter for default (CSV)")
    print("    Type 'json' to save as JSON")
    print("    Type 'skip' to not save the data at all")
    
    choice = input("    Your choice: ").strip().lower()

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
    `data` should be a dict: {domain: registrar, ...}
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

# ---------------------- Main Program -----------------------------------------

if __name__ == "__main__":
    """
    Main program: performs WHOIS lookup for domains in different modes.
    Guarantees globally unique domains in the final results.
    """
    all_domains = set()  # Using a set ensures global uniqueness

    if len(sys.argv) == 1:
        # Mode 1: Interactive input
        processed_domains = interactive_input_mode()
        all_domains.update(processed_domains)
    else:
        # Modes 2 & 3: Command-line arguments (files or domain strings)
        for arg in sys.argv[1:]:
            raw_input = read_or_return(arg)
            
            # Process input: normalize, dedupe per batch
            processed_domains = process_input(raw_input)
            
            # Add to global set for uniqueness
            all_domains.update(processed_domains)

    # Convert set to list for further processing or saving
    final_domains = list(all_domains)

    # Lookup registrars concurrently
    results = process_domains_concurrently(final_domains)

    # Save or process results
    process_and_save_new_data(results)

    print("+++ Closing the program. Goodbye! +++\n")