import secrets
import string

def generate_password(length=12):
  """
  Generates a cryptographically secure password.

  What it does: Uses the 'secrets' module for high-entropy randomness.
  Why: Standard 'random' is predictable; 'secrets' is designed for passwords.
  Target: Non-technical users needing a secure seed for .env files.
  """
  # We use alphanumeric characters and a safe subset of punctuation
  # that avoids common shell-escaping issues for users on Windows/macOS.
  alphabet = string.ascii_letters + string.digits + "!@#%^&*"
  return "".join(secrets.choice(alphabet) for _ in range(length))

def main():
  """
  Prints a generated password to stdout for CLI usage.
  """
  print(generate_password())

if __name__ == "__main__":
  main()
