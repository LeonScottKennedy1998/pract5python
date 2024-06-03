from flask import Flask, render_template, request, redirect, url_for
from web3 import Web3
import re
from web3.middleware import geth_poa_middleware
from account_info import abi, contract_address

app = Flask(__name__)

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
contract = w3.eth.contract(address=contract_address, abi=abi)

def is_strong_password(password):
    if len(password) < 12:
        return False
    if not re.search(r'[A-Z]', password):
        return False
    if not re.search(r'[a-z]', password):
        return False
    if not re.search(r'\d', password):
        return False
    if not re.search(r'[!@#$%^&*()-_+=\[\]{};:\'",.<>?/~`|\\]', password):
        return False
    return True

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        public_key = request.form.get('public_key')
        password = request.form.get('password')
        try:
            w3.geth.personal.unlock_account(public_key, password)
            return redirect(url_for("dashboard", account=public_key))
        except Exception as e:
            return render_template("login.html", error=True, error_message=str(e))
    return render_template("login.html", error=False)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        password = request.form.get('password')
        if is_strong_password(password):
            try:
                address = w3.geth.personal.new_account(password)
                return render_template("register.html", success=True, address=address)
            except Exception as e:
                return render_template("register.html", success=False, error_message=str(e))
        else:
            return render_template("register.html", success=False, error_message="Пароль должен содержать не менее 12 символов, включая заглавные и строчные буквы, цифры и специальные символы.")
    return render_template("register.html", success=False)

@app.route('/dashboard/<account>')
def dashboard(account):
    return render_template("dashboard.html", account=account)

@app.route('/create_estate/<account>', methods=['GET', 'POST'])
def create_estate(account):
    if request.method == 'POST':
        name = request.form.get('name')
        address = request.form.get('address')
        estate_type = request.form.get('estate_type')
        rooms = int(request.form.get('rooms'))
        describe = request.form.get('describe')

        estate_type_map = {"House": 0, "Apartments": 1, "Flat": 2, "Loft": 3}
        estate_type_uint8 = estate_type_map.get(estate_type)

        try:
            tx_hash = contract.functions.createEstate(name, address, estate_type_uint8, rooms, describe).transact({"from": account})
            return render_template("create_estate.html", success=True, tx_hash=tx_hash.hex())
        except Exception as e:
            return render_template("create_estate.html", success=False, error_message=str(e))
    return render_template("create_estate.html", success=False)

@app.route('/create_ad/<account>', methods=['GET', 'POST'])
def create_ad(account):
    if request.method == 'POST':
        estate_id = int(request.form.get('estate_id'))
        price = int(request.form.get('price'))
        date_time = int(request.form.get('date_time'))

        try:
            tx_hash = contract.functions.createAd(estate_id, price, date_time).transact({"from": account})
            return render_template("create_ad.html", success=True, tx_hash=tx_hash.hex())
        except Exception as e:
            return render_template("create_ad.html", success=False, error_message=str(e))
    return render_template("create_ad.html", success=False)

@app.route('/update_estate_status/<account>', methods=['GET', 'POST'])
def update_estate_status(account):
    if request.method == 'POST':
        estate_id = int(request.form.get('estate_id'))
        new_status = request.form.get('new_status').lower()

        try:
            if new_status == "true":
                new_status = True
            elif new_status == "false":
                new_status = False
            else:
                raise ValueError("Неверное значение. Введите true или false.")
            tx_hash = contract.functions.updateEstateStatus(estate_id, new_status).transact({"from": account})
            return render_template("update_estate_status.html", success=True, tx_hash=tx_hash.hex())
        except Exception as e:
            return render_template("update_estate_status.html", success=False, error_message=str(e))
    return render_template("update_estate_status.html", success=False)

@app.route('/update_ad_status/<account>', methods=['GET', 'POST'])
def update_ad_status(account):
    if request.method == 'POST':
        ad_id = int(request.form.get('ad_id'))
        new_status = request.form.get('new_status').capitalize()

        try:
            if new_status == "Opened":
                new_status_enum = 0
            elif new_status == "Closed":
                new_status_enum = 1
            else:
                raise ValueError("Неверное значение. Введите Opened или Closed.")
            tx_hash = contract.functions.updateAdStatus(ad_id, new_status_enum).transact({"from": account})
            return render_template("update_ad_status.html", success=True, tx_hash=tx_hash.hex())
        except Exception as e:
            return render_template("update_ad_status.html", success=False, error_message=str(e))
    return render_template("update_ad_status.html", success=False)

@app.route('/view_estate_by_id', methods=['GET', 'POST'])
def view_estate_by_id():
    if request.method == 'POST':
        estate_id = int(request.form.get('estate_id'))
        try:
            estate_info = contract.functions.estates(estate_id).call()
            return render_template("view_estate_by_id.html", estate_info=estate_info)
        except Exception as e:
            return render_template("view_estate_by_id.html", error=True, error_message=str(e))
    return render_template("view_estate_by_id.html", estate_info=None)

@app.route('/view_ad_by_id', methods=['GET', 'POST'])
def view_ad_by_id():
    if request.method == 'POST':
        ad_id = int(request.form.get('ad_id'))
        try:
            ad_info = contract.functions.ads(ad_id).call()
            return render_template("view_ad_by_id.html", ad_info=ad_info)
        except Exception as e:
            return render_template("view_ad_by_id.html", error=True, error_message=str(e))
    return render_template("view_ad_by_id.html", ad_info=None)

@app.route('/get_balance/<account>')
def get_balance(account):
    try:
        balance = contract.functions.getBalance().call({'from': account})
        return render_template("get_balance.html", balance=balance)
    except Exception as e:
        return render_template("get_balance.html", error=True, error_message=str(e))

@app.route('/get_account_balance/<account>')
def get_account_balance(account):
    try:
        balance_wei = w3.eth.get_balance(account)
        return render_template("get_account_balance.html", balance_wei=balance_wei)
    except Exception as e:
        return render_template("get_account_balance.html", error=True, error_message=str(e))

@app.route('/purchase_estate/<account>', methods=['GET', 'POST'])
def purchase_estate(account):
    if request.method == 'POST':
        ad_id = int(request.form.get('ad_id'))
        try:
            ad_info = contract.functions.ads(ad_id).call()
            price_wei = ad_info[2] * 10**18
            balance_wei = w3.eth.get_balance(account)
            if balance_wei < price_wei:
                raise ValueError("Недостаточно средств для покупки недвижимости")
            tx_hash = contract.functions.purchaseEstate(ad_id).transact({"from": account, "value": price_wei})
            return render_template("purchase_estate.html", success=True, tx_hash=tx_hash.hex())
        except Exception as e:
            return render_template("purchase_estate.html", success=False, error_message=str(e))
    return render_template("purchase_estate.html", success=False)

@app.route('/withdraw_funds/<account>', methods=['GET', 'POST'])
def withdraw_funds(account):
    if request.method == 'POST':
        try:
            balance_wei = contract.functions.getBalance().call({'from': account})
            if balance_wei == 0:
                return render_template("withdraw_funds.html", success=False, error_message="На вашем балансе нет средств для вывода")
            tx_hash = contract.functions.withdraw(balance_wei).transact({'from': account})
            return render_template("withdraw_funds.html", success=True, tx_hash=tx_hash.hex())
        except Exception as e:
            return render_template("withdraw_funds.html", success=False, error_message=str(e))
    return render_template("withdraw_funds.html", success=False)

@app.errorhandler(404)
def page_not_found(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('404.html'), 500

if __name__ == '__main__':
    app.run(debug=True)
