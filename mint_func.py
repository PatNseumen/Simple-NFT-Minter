# connect for ipfs server
def ipfs_con():
    api = ipfsapi.Client(host='http://127.0.0.1', port=5001)
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