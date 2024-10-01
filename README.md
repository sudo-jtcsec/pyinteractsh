# pyinteractsh-client

Creates a unique interactsh URL and poll it for interactions

- use create_instance() to create an object to use for polling - optionally, call it with a hostname value to register with your own interactsh isntance
- use poll() to poll instance at desired interval to retrieve JSON object of interaction
- use deregister() to cleanup an instance

# interactsh_instance Object
Calling create_instance() returns an object with the following values - it will mainly be used to pass required data to the poll function as well as to provide a proper URL to use for interactions. The data youll want is the list returend by poll()

 - private_key: the bytes of the private key used to register your client. Needed for decrypting poll data
 - public_key: the bytes of public key used to register your client. I don't think you'll need it after registering, but I save it just in case
 - server: the URL to the interactsh server you're registering to. Can be changed to custom interactsh server by calling create_instance with a hostname value
 - host: hostname of the interactsh server youre using. Can be changed to custom interactsh server by calling create_instance with a hostname value
 - secret_key: the random UID generated when registering. Required to poll data
 - correlation_id: the string used to identify your interactions. Required to poll data
 - url: an example URL to interact with using your correlation_id

# InteractSH Workflow
Since there is no good documentation on how to register Ill try to document it here - most of the info I have is from trial and error referencing the go client and https://github.com/wdahlenburg/interactsh-collaborator

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
After you've registered your correlation ID, you need to craft the interaction URL. Again, Im not entirely sure what the requirements are - a 33 character length correlation ID does NOT seem to work; rather, the correlation plus at least one additional character combined to equal 33 characters worked. This means, if your corelation ID is 20 characters long, then you need to add 13 random characters to the end and append that to your server
```
correlation ID: xyxyxyxyxyxyxyxyxyxy
Interaction URL: https://xyxyxyxyxyxyxyxyxyxyABABABABABABA.interact.sh
```
This means that both of the below modified URLS will generate interactions for your correlation ID:
```
https://xyxyxyxyxyxyxyxyxyxyABABABAnewnew.interact.sh # I believe this still must be 33 characters in length
https://newneww.xyxyxyxyxyxyxyxyxyxyABABABABABABA.interact.sh
```
In practice, I usually just modify the subdomain so I dont have to worry about preserving length
## Poll
Next, you have to poll your interactions
```
GET /poll?id=(your correlation id)&secret=(your secret)
```
This will ALWAYS return a json object, regardless of if there are interactions. If there are interactions, each one will be a JSON object inside a list, stored at the "data" entry and encrypted

The returned json entries:
 - data: encrypted list of JSON objects that are your interactions 
 - extra: honestly no idea
 - aes_key: base64 encoded key to decrypt the data object  

Now, this is where the fun begins. Im not a crypto expert, so I may butcher the explanation, but these are the steps I take:

1) Base64 Decode the aes_key from the response
2) Decrypt the aes_key using your PRIVATE key - it was encrypted with your PUBLIC key that was sent when you registered
3) Now you have the decrypted AES key, which will be used to decode the data object recieved from your poll request. This uses AES CFB and you must provide the intiialization vector (iv). I slice of the first 16 bits of the data block to get the IV, then pass the rest of data to be decrypted. Segmentsize has to be 128. However the decryption is done in your desired language, perform it with the described parameters
4) Once the data is decrypted, you have a serialized JSON object. Deserialize it to retrieve it (in python use json.loads)

## Deregister
Pretty straightforward: send a POST to the interactSH server with a JSON body containing correlation-id and secret-key

# Example Code Implementation
Below snippet will create a new instance, poll it every second for interactions, and print the response object if it returns any interactions

```
import pyinteractsh, time

import warnings
import requests
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the specific SSL warning
warnings.simplefilter('ignore', InsecureRequestWarning)

# create the instance
ish = pyinteractsh.create_instance()
# get the URL to interact with
print(ish.url)
while True:
    # pol the URL. If theres data, print it
    ints = pyinteractsh.poll(ish)
    if len(ints) != 0:
        print(ints)
        # We got our callback, lets cleanup the instance
        pyinteractsh.deregister(ish)
    time.sleep(1)
```
# TODO
Add server configuration options (use custom URL)
