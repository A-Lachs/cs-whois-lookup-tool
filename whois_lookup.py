# ----------------------- Imports ---------------------------------------------

import whois   # pip install python-whois
import idna    # pip install idna
import time 
import sys
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

from file_handling import process_and_save_new_data


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
                print(f"\n    {domain_link} -> OK: {registrar}")
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

    - Continuously prompts the user for domains until 'c' for continue is typed.
    - Normalizes input using process_input() -> removes www., trims, dedupes per input.
    - Returns a list of cleaned, unique domain strings collected during the session.
    """

    print("\n+++ Welcome! Enter one or more domains to check their registrars.")
    session_domains = set()  # keep unique domains in this session
    
    while True:
            user_input = input("\n    Enter domains here (or type 'c' to continue processing): ")
            
            # Check for continue command 
            if user_input.strip().lower() == 'c':
                return list(session_domains)  # return all domains collected so far
            
            # Process non-empty input 
            if user_input: 
                processed_input = process_input(user_input)

                if processed_input:  # Only proceed if there are valid domains
                    session_domains.update(processed_input)
                    print(f"\n    - Collected {len(processed_input)} new domain(s). Total so far: {len(session_domains)}")
                else:
                    print("\n    - No valid domains found. Please try again.")            
            else:
                print("\n    - Invalid input! Please enter one or more domain names or type 'c' to continue.")


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

    if isinstance(input_given, str):  # do preprocessing
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


def determine_input_format(arg: str) -> str | list[str]:
    """
    Helder function used to deptermine the input mode (2 or 3).
    Attempts to read the argument as a file.
    If the file exists, returns a list of non-empty stripped lines -> Mode 2
    Otherwise, returns the original argument as a string -> Mode 3
    """
    try:
        with open(arg, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        return arg  # treat as domain string if file not found

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
            # read input arg from file or string
            raw_input = determine_input_format(arg)
            
            # Process input: normalize, dedupe per batch
            processed_domains = process_input(raw_input)
            
            # Add to global set for uniqueness
            all_domains.update(processed_domains)

    # Convert set to list for further processing or saving
    final_domains = list(all_domains)

    # Lookup registrars concurrently
    results = process_domains_concurrently(final_domains)

    # Save results
    process_and_save_new_data(results)

    print("\n+++ Closing the program. Goodbye! +++\n")