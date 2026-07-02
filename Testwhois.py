import whois
def perform_whois(domain):
  try:
    # Perform WHOIS lookup
    result = whois.whois(domain)
    # Print the results
    print(f"\nWHOIS information for {domain}:")
    print(f"Domain Name: {result.domain_name}")
    print(f"Registrar: {result.registrar}")
    print(f"Creation Date: {result.creation_date}")
    print(f"Expiration Date: {result.expiration_date}")
    print(f"Updated Date: {result.updated_date}")
    print(f"Name Servers: {result.name_servers}")
    print(f"Status: {result.status}")
    print(f"Email: {result.emails}")
    print(f"Address: {result.address}")
    print(f"City: {result.city}")
    print(f"State: {result.state}")
    print(f"Country: {result.country}")
  except Exception as e:
    print(f"An error occurred: {e}")
def main():
  # Prompt user for domain
  domain = input("Enter the domain to perform a WHOIS lookup: ").strip()
  if domain:
    perform_whois(domain)
  else:
    print("No domain entered. Exiting.")
# Example usage
if __name__ == "__main__":
  main()