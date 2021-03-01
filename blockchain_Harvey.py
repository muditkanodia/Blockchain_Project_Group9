### import the libraries
import datetime
import hashlib
import json
from flask import Flask,jsonify,request
import requests
from uuid import uuid4
from urllib.parse import urlparse
import pandas as pd

import smtplib
import random

## PArt 1- Building the BlockChain
Pan=pd.read_csv("Pancard.csv")

class BlockChain:
    Pan=pd.read_csv("Pancard.csv")
    def __init__(self):
        self.chain=[]
        self.transactions=[]
        self.nodes=set()
        self.create_block(proof=1,previous_hash='0')
        self.otp_verification=""
        
    def create_block(self,proof,previous_hash):
        block={'index':len(self.chain)+1,
               'timestamp':str(datetime.datetime.now()),
               'proof':proof,
               'previous_hash':previous_hash,
               'transactions':self.transactions
            
            }
        self.transactions=[]
        self.chain.append(block)
        return block
    
    def get_previous_block(self):
        return self.chain[-1]
    
    def proof_of_work(self, previous_proof):
        new_proof = 1
        check_proof = False
        while check_proof is False:
            hash_operation = hashlib.sha512(str(new_proof**3 - previous_proof**3).encode()).hexdigest()
            if hash_operation[:4] == '0000':
                check_proof = True
            else:
                new_proof += 1
        return new_proof
    
    def hash(self, block):
        encoded_block = json.dumps(block, sort_keys = True).encode()
        return hashlib.sha512(encoded_block).hexdigest()
    
    def is_chain_valid(self, chain):
        previous_block = chain[0]
        block_index = 1
        while block_index < len(chain):
            block = chain[block_index]
            if block['previous_hash'] != self.hash(previous_block):
                return False
            previous_proof = previous_block['proof']
            proof = block['proof']
            hash_operation = hashlib.sha512(str(proof**3 - previous_proof**3).encode()).hexdigest()
            if hash_operation[:4] != '0000':
                return False
            previous_block = block
            block_index += 1
        return True 
    
    def add_transaction(self,sender,receiver,amount,sender_pan,receiver_pan,otp_verify):
        self.transactions.append({
            'sender':sender,
            'receiver':receiver,
            'amount':amount,
            'sender_pan':sender_pan,
            'receiver_pan' :receiver_pan
            
            })
        previous_block=self.get_previous_block()
        return previous_block['index']+1

        
        
    
    def add_node(self,address):
        parsed_url=urlparse(address)
        self.nodes.add(parsed_url.netloc)
        
    ### consensus protocol
    
    def replace_chain(self):
        network=self.nodes
        longest_chain=None
        max_length=len(self.chain)
        
        for node in network:
            response=requests.get(f'http://{node}/get_chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                if length > max_length and self.is_chain_valid(chain):
                    max_length = length
                    longest_chain = chain
        if longest_chain:
            self.chain = longest_chain
            return True
        return False
        
            

## Part 2- Mining the BlockChain

app=Flask(__name__)

### creating an address for the node on Port 5000
node_address=str(uuid4()).replace('-','')

### Create The BlockChain
blockchain=BlockChain()
## Create a web app for the API
### Mining the new block
@app.route('/mine_block', methods = ['GET'])
def mine_block():
    previous_block = blockchain.get_previous_block()
    previous_proof = previous_block['proof']
    proof = blockchain.proof_of_work(previous_proof)
    previous_hash = blockchain.hash(previous_block)
    blockchain.add_transaction(sender = node_address, receiver = 'Harvey', amount = 1,sender_pan="DAJPC4150P",receiver_pan="NA",otp_verify="NA")
    block = blockchain.create_block(proof, previous_hash)
    
    temp = block["transactions"]
    wallet_amt = (temp[1]["amount"])
    print(wallet_amt)
    
    response = {'message': 'Congratulations, you just mined a block!',
                'index': block['index'],
                'timestamp': block['timestamp'],
                'proof': block['proof'],
                'previous_hash': block['previous_hash'],
                'transactions': block['transactions']}
    return jsonify(response), 200

# Getting the full Blockchain
@app.route('/get_chain', methods = ['GET'])
def get_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200


# Checking if the Blockchain is valid
@app.route('/is_valid', methods = ['GET'])
def is_valid():
    is_valid = blockchain.is_chain_valid(blockchain.chain)
    if is_valid:
        response = {'message': 'All good. The Blockchain is valid.'}
    else:
        response = {'message': 'Houston, we have a problem. The Blockchain is not valid.'}
    return jsonify(response), 200


# Adding a new transaction to the Blockchain
@app.route('/add_transaction', methods = ['POST'])
def add_transaction():
    json = request.get_json()
    transaction_keys = ['sender', 'receiver', 'amount','sender_pan','receiver_pan','otp_verify']
    if not all(key in json for key in transaction_keys):
        return 'Some elements of the transaction are missing', 400
    
    flag_s=0
    flag_r=0
    
    temp2_sen= str(json['sender_pan']).upper().strip()
    temp2_rec= str(json['receiver_pan']).upper().strip()
    
    
    for i in range(len(Pan)):
        temp_sen = str(list(Pan["Pan_Card_Id"])[i]).upper().strip()
        if((temp_sen == temp2_sen)):  
            flag_s=1
            break
        
    for i in range(len(Pan)):
        temp_rec = str(list(Pan["Pan_Card_Id"])[i]).upper().strip()
        if(temp_rec == temp2_rec):  
            flag_r=1
            break
            
    if(flag_s==0):
         return 'Please enter the correct Senders PanCard No:', 400  
     
    if(flag_r==0):
         return 'Please enter the correct receiver PanCard No:', 400 
     
    if(json['sender_pan']==json['receiver_pan']):
        return 'Error! Both senders and receivers pan card are same', 400 
    
    temp_otp=blockchain.otp_verification
    print(temp_otp)
    print(str(json['otp_verify']).strip())
    
    if(str(json['otp_verify']).strip() != str(temp_otp).strip()):
        return 'OTP Verification failed', 400 
              
    ind_s = Pan.index[Pan["Pan_Card_Id"].str.find(json['sender_pan'])==0]
    name_s= str(list(Pan.Name[ind_s])[0]).upper().strip()
    
    ind_r = Pan.index[Pan["Pan_Card_Id"].str.find(json['receiver_pan'])==0]
    name_r= str(list(Pan.Name[ind_r])[0]).upper().strip()
    
    if(flag_s==0):
         return 'Please enter the correct Senders PanCard No', 400  
     
    if(flag_r==0):
         return 'Please enter the correct receiver PanCard No', 400 
     
    sender_name_ex = str((json['sender'])).upper().strip()
    receiver_name_ex = str((json['receiver'])).upper().strip()
    
    if((name_s != sender_name_ex) | (name_r != receiver_name_ex)):
        print(name_s)
        print(sender_name_ex)
        print(name_r)
        print(receiver_name_ex)
        return 'Error! Either the senders or receivers Name entered is incorrect', 400 
    
    index = blockchain.add_transaction(json['sender'], json['receiver'], json['amount'], json['sender_pan'], json['receiver_pan'], json['otp_verify'])
    response = {'message': f'OTP Verified! \\n  Pan Card Verfied! \\n This transaction will be added to Block {index}'}
    return jsonify(response), 201

# Part 3 - Decentralizing our Blockchain

# Connecting new nodes
@app.route('/connect_node', methods = ['POST'])
def connect_node():
    json = request.get_json()
    nodes = json.get('nodes')
    if nodes is None:
        return "No node", 400
    for node in nodes:
        blockchain.add_node(node)
    response = {'message': 'All the nodes are now connected. The Blockchain now contains the following nodes:',
                'total_nodes': list(blockchain.nodes)}
    return jsonify(response), 201

# Replacing the chain by the longest chain if needed
@app.route('/replace_chain', methods = ['GET'])
def replace_chain():
    is_chain_replaced = blockchain.replace_chain()
    if is_chain_replaced:
        response = {'message': 'The nodes had different chains so the chain was replaced by the longest one.',
                    'new_chain': blockchain.chain}
    else:
        response = {'message': 'All good. The chain is the largest one.',
                    'actual_chain': blockchain.chain}
    return jsonify(response), 200


#*************OTP VERIFICATION*********************************
@app.route('/otp_gen', methods = ['POST'])
def otp_gen():
    
    json = request.get_json()
    pan_id_otp = ['Pan_ID']
    
    if not all(key in json for key in pan_id_otp):
        return 'Feild is empty!', 400
    
    flag=0  
    temp2= str(json['Pan_ID']).upper().strip()
    print(temp2)
    for i in range(len(Pan)):
        temp1 = str(list(Pan["Pan_Card_Id"])[i]).upper().strip()
        print(temp1)
        if((temp1 == temp2)):  
            flag = 1
            break
            
    if(flag == 0):
         return 'Please enter the correct PanCard ID Number', 400  
    else:
        ind = Pan.index[Pan["Pan_Card_Id"].str.find(json['Pan_ID'])==0]
        email= str(list(Pan.Email_id[ind])[0]).strip()
           
        s = smtplib.SMTP("smtp.gmail.com" , 587)  # 587 is a port number
        # start TLS for E-mail security 
        s.starttls()
        # Log in to your gmail account
        s.login("project.blockchain4@gmail.com" , "Project_Blockchain_4")
        otp = random.randint(1000, 9999)
        otp = str(otp)
        blockchain.otp_verification=otp
        
        s.sendmail("project.blockchain4@gmail.com" , email , otp)
        #print("OTP sent succesfully..")
        # close smtp session
        s.quit()
        
        response = {'message': 'OTP sent succesfully!'}
        return jsonify(response), 200

# Running the app
app.run(host = '0.0.0.0', port = 5002)





