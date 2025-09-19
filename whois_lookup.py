# ----------------------- Imports ---------------------------------------------

import whois  # pip install python-whois
import os
import time 
import sys
import re
import idna  # pip install idna
from concurrent.futures import ThreadPoolExecutor, as_completed 

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


def interactive_input_mode():
    """
    This function handles the interactive input mode.
    - Keeps asking for domain links until you type 'exit'.
    - Calls the helper function process_input() to format the input.
    - Uses the threading function process_domains_concurrently() to lookup the registrars.
    """
    print("\n+++ Welcome! Enter one or more domains to check their registrars.")
    new_data = []
    
    while True:
            user_input = input("    Enter domains here or type exit to quit the program: ")
            
            if user_input == 'exit'.strip().lower():
                if new_data:
                    # if there is data, return it --> will be saved before exiting the program 
                    return new_data
                break
            elif user_input:
                processed_input = process_input(user_input)
                # Use threads instead of sequential loop
                new_data.extend(process_domains_concurrently(processed_input))             
            else:
                print("+++ Invalid input, please try again or type exit.\n")


def process_input(input_given: str| list) -> list | None: 
    pass

def unique_items_to_process(old_data, new_data):
    # Keep only new unique items
    return [item for item in new_data if item not in old_data]

def ask_output_file_format() -> str:
    """
    Ask the user which output format they want.
    Default is CSV unless the user types 'json'.
    """
    print("\n+++ How to save the results?")
    choice = input("    Type 'json' to change format or press Enter to keep default: ").strip().lower()

    if choice == "json":
        return "json"
    else:
        return "csv"
    
def process_and_save_new_data(new_data):
    # Wrapper function for data handling.
    pass

# ---------------------- Main Program -----------------------------------------

if __name__ == "__main__":
    
    # starts a whoois lookup for registrars in different modes 
    # depending on the number and type of arguments given in the command line 

    if len(sys.argv) == 1: # no extra argument
    
    # --- Mode 1: Interactive Domain input
        new_data = interactive_input_mode()   
        
    else:
        new_data = []   
    # --- Modes 2 & 3: Process command line arguments as files or domains
        for arg in sys.argv[1:]:
            try:
                # Mode 2: Try to treat argument as a filename
                with open(arg, 'r', encoding='utf-8') as f:
                    domain_lines = [line.strip() for line in f if line.strip()]
                    new_data.extend(process_domains_concurrently(domain_lines))
                                  
            except FileNotFoundError:
                # Mode 3: If argument not a file, treat as domain
                domain_list = [d.strip() for d in arg.split(",") if d.strip()]
                new_data.extend(process_domains_concurrently(domain_list))

    process_and_save_new_data(new_data) 

    print("+++ Closing the program. Goodbye! +++\n")