# mintcontract:0x2725F6b8f4421AaF1b315A851c7829c4FA29E8b9
# abi=selfabi.json
from flask import Flask, send_from_directory, request, jsonify, redirect, render_template, url_for,flash,session
from werkzeug.utils import secure_filename
import ipfsapi
from web3 import Web3, middleware
from web3.exceptions import ContractLogicError
from web3.gas_strategies.time_based import *
from web3.middleware import geth_poa_middleware
import json
import os

from_addr = '0xA93bc4544a77Cc04785B2B9CF4f8f32563f6C55d'
#local
#abifile_path = 'C:/Users/siva/PycharmProjects/smartcontract/mint.json'

# live
abifile_path = './mint.json'

PRIVATE_KEY = ''

ropston_contract = '0xc85493640607E962Fe324BD0f82254dC28B7b4e9'
ropston_url = "https://ropsten.infura.io/v3/d57b9fb8575f4539bd28cf4af07a6251"
ropston_chain_id = 3


polygon_url = "https://rpc-mumbai.maticvigil.com/"
polygon_contract = '0xC055012398d7dA7a2098BD45a16D8fcA44b26645'
polygon_chain_id = 80001


#local
# UPLOAD_FOLDER = "C:/Users/siva/PycharmProjects/smartcontract/ipfscon/images/"

# live
app = Flask(__name__)
UPLOAD_FOLDER = "./images/"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'json', "png"}
# The absolute path of the directory containing images for users to download
# CLIENT_IMAGES="C:/Users/siva/PycharmProjects/smartcontract/ipfscon/clientimages/"
app.config["CLIENT_IMAGES"] = UPLOAD_FOLDER
app.secret_key = "super secret key"
host='http://127.0.0.1'
port=5001
# connect for ipfs server
def ipfs_con():
    api = ipfsapi.Client(host=host, port=port)
    return api


#connecting  rpc and creating the contract instance
def connect_web3(url, contract_addr, ABI):
    w3 = Web3(provider=Web3.HTTPProvider(url))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    w3.middleware_onion.add(middleware.latest_block_based_cache_middleware)
    w3.middleware_onion.add(middleware.simple_cache_middleware)
    strategy = construct_time_based_gas_price_strategy(10)
    w3.eth.setGasPriceStrategy(strategy)
    contract = w3.eth.contract(contract_addr, abi=ABI)
    return w3, contract

# handling the transaction for various smart contract function
def handle_transaction(fn_name, args, chain_id, PRIVATE_KEY, from_addr, w3, contract):
    addr = Web3.toChecksumAddress(from_addr)

    def calculate_nonce():
        return Web3.toHex(w3.eth.getTransactionCount(addr))

    data = contract.encodeABI(fn_name, args=args)

    while True:
        try:
            gas = getattr(contract.functions, fn_name)(*args).estimateGas({'from': addr})
            break
        except ContractLogicError as e:
            print(f"A contract error occurred while calculating gas: {e}")

        except Exception as e:
            print(f"A misc. error occurred while calculating gas: {e}")

    gasprice = w3.eth.generateGasPrice()

    txn_fee = gas * gasprice
    print(f"txn_fee {txn_fee}")

    tr = {'to': contract.address,
          'from': from_addr,
          'value': Web3.toHex(0),
          'gasPrice': Web3.toHex(gasprice),
          'nonce': calculate_nonce(),
          'data': data,
          'gas': gas,
          'chainId': chain_id,
          }

    while True:
        try:
            signed = w3.eth.account.sign_transaction(tr, PRIVATE_KEY)
            tx_hash = w3.eth.sendRawTransaction(signed.rawTransaction)
            print(f"tx_hash {tx_hash.hex()}")
            tx_receipt = w3.eth.waitForTransactionReceipt(tx_hash)
            #             print("TXN RECEIPT: ", dict(tx_receipt))
            break
        except Exception as e:
            print(f"{fn_name} Error: ", e)
    return tx_hash.hex(), dict(tx_receipt)

#simple function to  get keys from abi file
def getkeylis(dict):
    list = []
    for key in dict.keys():
        list.append(key)
    return list

# simple function to get the smart contract function and the argumets for the function
def select_fun(data):
    a = {}
    non_param = []
    param = []
    for i in data:
        service_type = i['type']
        if service_type == "function":
            inputs = i['inputs']
            if inputs == []:
                #                 print("name of function",i['name'])
                non_param.append(i['name'])

            else:
                #             print(i['inputs'][0])
                no_of_param = len(i['inputs'])
                s = i['inputs']
                function_name = i['name']
                param.append(function_name)
                #                 print(f" length of input parameter for function {function_name} {no_of_param}")
                values = i['inputs']
                values.append(i['stateMutability'])
                a[function_name] = values
    #  parameteric functions

    return a, param, non_param

# simple function to get the arguments for smart contract function
def func(a, fun):
    function_names = getkeylis(a)
    #     print(f"function name {function_names}")
    #     getfunction = input("select the function name ")
    selected_fun = a.get(fun)
    lenofparam = len(selected_fun[0:-1])
    mutablity = selected_fun[-1]
    return lenofparam, selected_fun[0:-1], mutablity



# get the file from the from front end
def fileurl(param):
    uploaded_file = request.files[param]
    # filename = secure_filename(uploaded_file.filename)
    if uploaded_file and allowed_file(uploaded_file.filename):
        filename = secure_filename(uploaded_file.filename)
        uploaded_file.save(os.path.join(
            app.config['UPLOAD_FOLDER'], filename))
        filepath = "{}{}".format(UPLOAD_FOLDER, filename)
        print(f"filepath {filepath}")
        return filename
    else:
        print("file is not valid")

# condition to check the required file with extension

def allowed_file(filename):
    print('.' in filename and
          filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS)
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


#api to get the networktype,and image 
@app.route("/", methods=['GET', 'POST'])
def base():
    
    
    if request.method == "POST":
        option = request.form['options']
        
        try:
            file=fileurl('file')
#             print(filename)
            return redirect(url_for('get_image', filename=file,options=option))
        except Exception as e:
            print("error", e)
            # return render_template("option.html",alert="No data found " )
            return render_template('index.html', alert="No data found")

    return render_template("index.html", file="upload image file",button='submit')



#final result 
@app.route("/get-image", methods=['GET', 'POST'])
def get_image():
    param_fun="mint"
    option = request.args.get('options')
    print(f" option {option}")
    filename = request.args.get('filename')
    print(f"image {filename}")
    file_path = f"{UPLOAD_FOLDER}{filename}"
    print(f"file_path {file_path}")
    with open(abifile_path)as f:
        data = json.load(f)
        a,param,non_param=select_fun(data)
        lenofparam,inputparam,mutablity=func(a,param_fun)
            
    image_upload = ipfs_con().add(file_path).get('Hash')
    print(image_upload)
    url = f"https://ipfs.io/ipfs/{image_upload}"

    json_file = {}
    json_file['name'] = "test"
    json_file['image'] = url
    json_file['description'] = "This image shows the true nature of NFT."
    print(json_file)
    json_object = json.dumps(json_file, indent=4)
    # filename = input("give file name")
    filename2 = "nft.sol"
    # Writing to sample.json
    with open(filename2, "w") as outfile:
        outfile.write(json_object)
    Hash = ipfs_con().add(filename2).get('Hash')
    print(f"final hash {Hash}")
    url = f"https://ipfs.io/ipfs/{Hash}"
    if request.method == "POST":
        if request.form.get("submit_a"):
            paramlis=request.form.getlist("fun_values")
            if option == "Ropston":
                ABI = json.load(open(abifile_path))
                w3, contract = connect_web3(ropston_url, ropston_contract, ABI)
               
                print(f"param_fun {param_fun}")
                print(f"listof {paramlis}")
                if mutablity == "nonpayable":
                    print("nonpayable")
                    tx_hash, parameter_value = handle_transaction(param_fun, paramlis, ropston_chain_id, PRIVATE_KEY, from_addr, w3,
                                                                              contract)
                    return render_template("result.html",network_type="Ropston",param_fun=param_fun,parameter_value=tx_hash)

            elif option == "Polygon":
                
                ABI = json.load(open(abifile_path))
                w3, contract = connect_web3(polygon_url, polygon_contract, ABI)
               
                print(f"param_fun {param_fun}")
                print(f"listof {paramlis}")
                if mutablity == "nonpayable":
                    print("nonpayable")
                    tx_hash, parameter_value = handle_transaction(param_fun, paramlis, polygon_chain_id, PRIVATE_KEY, from_addr, w3,
                                                          contract)
                    return render_template("result.html",network_type="Polygon",
                                   param_fun=param_fun,parameter_value=tx_hash)
               

    return render_template("index.html", options=option,url=url,button="mint",func=inputparam,lenofparam=lenofparam)
    

if __name__ == "__main__":
#     app.secret_key = 'super secret key'
#     app.config['SESSION_TYPE'] = 'filesystem'
#     sess.init_app(app)
    app.run(host="0.0.0.0", port=5003)