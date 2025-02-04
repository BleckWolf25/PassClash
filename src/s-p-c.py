#!/usr/bin/env python3

"""
Simple Password Cracker
A tool to crack MD5 hashed passwords using a wordlist.

This script provides functionality to:
1. Hash passwords using MD5
2. Crack MD5 hashes using a wordlist
3. Demonstrate password cracking with a sample hash
"""

# Import the required modules
import hashlib
from typing import Optional

# Define functions for password hashing
def hash_password(password: str) -> str:
    """
    Hash a password using MD5 algorithm.
    
    Args:
        password (str): The plaintext password to hash.
    
    Returns:
        str: The hexadecimal representation of the MD5 hash.
    """
    return hashlib.md5(password.encode()).hexdigest()

# Define a function to crack the password
def brute_force(target_hash: str, wordlist: str) -> Optional[str]:
    """
    Attempt to crack a password hash by trying each word in the wordlist.
    
    Args:
        target_hash (str): The MD5 hash to crack.
        wordlist (str): File path to the wordlist.
    
    Returns:
        Optional[str]: The cracked password if found, None otherwise.
        
    Raises:
        FileNotFoundError: If wordlist file doesn't exist.
        Exception: For other potential errors during file operations.
    """
    try:
        # Read wordlist file and check each password
        with open(wordlist, 'r', encoding='utf-8') as file:
            for line in file:
                password = line.strip()
                if hash_password(password) == target_hash:
                    return password
    except FileNotFoundError:
        print(f"Error: Wordlist file '{wordlist}' not found.")
    except Exception as e:
        print(f"Error: {str(e)}")
    return None

# Define the main function
def main() -> None:
    """
    Main function to demonstrate password cracking functionality.
    Uses a sample hash and wordlist to show the cracking process.
    """
    # Configuration
    target_hash = 'b78902ebd2885aa3043772e1e8888ed5'    # Sample hash to crack
    wordlist_path = 'wordlist.txt'                      # Path to wordlist file

    # Attempt to crack the hash
    cracked_password = brute_force(target_hash, wordlist_path)

    # Display results
    if cracked_password:
        print(f'Password cracked: {cracked_password}')
    else:
        print('Password not found in wordlist.')

# Call the main function
if __name__ == "__main__":
    main()