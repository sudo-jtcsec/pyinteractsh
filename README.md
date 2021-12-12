# pyinteractsh-client

Creates a unique interactsh URL and poll it for interactions

use create_instance() to create an object to use for polling
use poll() to poll instance at desired interval to retrieve JSON object of interaction

# InteractSH Workflow
Since there is no good documentation on how to register Ill try to document it here

First, you need a few things to register
  - an InteractSH server URL to register to
  - RSA private and public keys
  - Client specific UUIDs
    - correlation id: random string that must be less then 32 characters - used to identify your interactions  
    - secret key: random string, unsure of length/format requirements. I use pythons uuid library to create a string that looks like ```351ffe7b-c4ec-4364-8fee-89d2aec91e6d```

## Register
Fairly self explanatory - POST the required details as json to /register on target server
```
POST /register
Host: interactsh server
Content-Type: application/json

{"public-key": (your base64 encoded public key here),"secret-key":(secret key outlined in requirements above),"correlation-id": (correlation id outlined in requirements above)}
```

# Example Code
Below snippet will create a new instance, poll it every second for interactions, and print the response object if it returns any interactions

```
import pyinteractsh, time
ish = pyinteractsh.create_instance()
print(ish.url)
while True:
    ints = pyinteractsh.poll(ish)
    if len(ints) != 0:
        print(ints)
    time.sleep(1)
```

# TODO
Add server configuration options (use custom URL)
