import requests, base64, uuid, random, string, time, json
import Cryptodome.Cipher.PKCS1_OAEP as PKCS1_OAEP
import Cryptodome.Cipher.AES as AES
import Cryptodome.PublicKey.RSA as RSA2
import Cryptodome.Hash
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

class interactsh_instance:
    def __init__(self,private_key,public_key,server,host,secret_key,correlation_id,url):
        self.private_key = private_key
        self.public_key = public_key
        self.server = server
        self.host = host
        self.secret_key = secret_key
        self.correlation_id = correlation_id
        self.url = url

def create_instance(hostname="interact.sh"):
    # make keys
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )

    unencrypted_pem_private_key = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption()
    )


    pem_public_key = private_key.public_key().public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    ####################
    # vars
    server = "https://"+hostname
    host = hostname
    public_key_b64 = base64.b64encode(pem_public_key)
    secret_key = str(uuid.uuid4())
    letters = string.ascii_lowercase
    correlation_id_init = ''.join(random.choice(letters) for i in range(20))
    correlation_id = correlation_id_init  + ''.join(random.choice(letters) for i in range(13))


    ########
    # register
    json2send = {"public-key":public_key_b64.decode('ascii'),"secret-key":secret_key,"correlation-id":correlation_id_init}
    response = requests.post(server+"/register",json=json2send,verify=False)
    intsh_instance = interactsh_instance(unencrypted_pem_private_key,public_key_b64,server,host,secret_key,correlation_id_init,"https://"+correlation_id+"."+host)
    return  intsh_instance

# Self explanatory
def deregister(intsh_instance):
    requests.post(intsh_instance.server+"/deregister",json={"correlation-id":intsh_instance.correlation_id,"secret-key":intsh_instance.secret_key},verify=False)

def poll(intsh_instance):
    # Get Interactions
    ints = []
    resp = requests.get(intsh_instance.server+"/poll?id="+intsh_instance.correlation_id+"&secret="+intsh_instance.secret_key,verify=False)
    # pass if none
    if resp.json()["data"] == []:
        pass
    else:
        # get bytes of base64 key (encoded)
        b64_bytes = resp.json()["aes_key"].encode('ascii')
        # Decode bytes of base64 
        decodedkey = base64.b64decode(b64_bytes) 
        # load the provided key
        k = RSA2.importKey(intsh_instance.private_key)
        # create cipher
        cipher1 = PKCS1_OAEP.new(k,Cryptodome.Hash.SHA256)
        keyPlaintext = cipher1.decrypt(decodedkey)
        
        # Pares data list
        for d in resp.json()["data"]:
            try:
                # get base64 bytes of entry
                d64_bytes = d.encode('ascii')
                # get plain bytes of entry
                dataenc = base64.b64decode(d64_bytes)
                # prep IV
                iv = dataenc[:16]
                # create cipher with proper key, mode, and sizes
                cipher = AES.new(keyPlaintext, AES.MODE_CFB, iv,segment_size=128)
                # decrypt interaction (ignore IV)
                interactionb = cipher.decrypt( dataenc[16:] )

            except (ValueError, KeyError):
                print("Incorrect decryption")

            ## testing stuf vvvvvv
            #print(interactionb.decode("latin1"))
            interaction = json.loads(interactionb,strict=False)
            ints.append(interaction)
    return ints
                
