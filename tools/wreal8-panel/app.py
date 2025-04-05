import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash
from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset, Account, TrustLineFlags
import os
from datetime import timedelta

# Lista de claves públicas autorizadas (solo las G... de los firmantes válidos)
WHITELIST = {
    "GBVYYQ7XXRZW6ZCNNCL2X2THNPQ6IM4O47HAA25JTAG7Z3CXJCQ3W4CD",
    "GB4I7MBTS3445MJKYX5JCIV6VFWBEJNBQQFOAUHKS5PKZGOZ2I5G62NK",
    "GBEGVCIQUC7MYZMKBUTNL77NZGN4JXE2ZTEK6QMY52BPZCAZBK6ZBSJW"
}

app = Flask(__name__, template_folder='templates')
app.secret_key="A2n3S!2vD%C*yHAct3bgm@Urjt#7Gzk^1BES5@a4"
app.config['SERVER_NAME'] = 'wreal8-panel.escarcela.xyz'
app.permanent_session_lifetime = timedelta(minutes=5)

# Configuración Stellar
STELLAR_SERVER = "https://horizon.stellar.org"
NETWORK_PASSPHRASE = Network.PUBLIC_NETWORK_PASSPHRASE
EMISSOR_SECRET = os.getenv("WREAL8_SECRET")
EMISSOR_PUBLIC = os.getenv("WREAL8_PUBLIC")
# Reemplaza con tu asset info:
ASSET_CODE = "wREAL8"
ASSET_ISSUER = "GAN4OHMJ4BWK755SVZMQGZJMH4XTRQM7HTSEQDLDXDW2PILUJ2C67YEK"

server = Server(horizon_url=STELLAR_SERVER)

# Usuario simple para login temporal
USERS = {
    "admin": "adminpass"
}

from stellar_sdk import Keypair

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        secret_key = request.form['secret_key']
        try:
            keypair = Keypair.from_secret(secret_key)
            public_key = keypair.public_key
        except Exception:
            flash('❌ Clave secreta inválida.')
            return redirect(url_for('login'))

        if public_key in WHITELIST:
            session['logged_in'] = True
            session['public_key'] = public_key
            session['secret_key'] = secret_key
            session.permanent = True
            return redirect(url_for('dashboard'))
        else:
            flash('⚠️ Esta clave no está autorizada.')
            return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    # Fetch trustlines to the asset
    url = f"https://horizon.stellar.org/accounts?asset={ASSET_CODE}:{ASSET_ISSUER}"
    response = requests.get(url)
    accounts = response.json()["_embedded"]["records"]

    # Filtrar solo los que están pendientes de autorización
    pending_auths = []
    print(f"🔍 Cuentas encontradas: {len(accounts)}")
    for acc in accounts:
        for balance in acc.get("balances", []):
            if (
                balance.get("asset_code") == ASSET_CODE and
                balance.get("asset_issuer") == ASSET_ISSUER
                # balance.get("is_authorized") is False
            ):
                print(f"🎯 Encontrado balance: {balance}")
                if balance.get("is_authorized") is False:
                    created_at = acc.get("last_modified_time", "Desconocido")
                    pending_auths.append({
                        "account_id": acc["account_id"],
                        "created_at": created_at
                    })

    return render_template("dashboard.html", pending_auths=pending_auths)

@app.route("/autorizar", methods=["POST"])
def autorizar():
    trustor = request.form.get("trustor")
    emitter_secret = request.form.get("emitter_secret")

    try:
        emitter_keypair = Keypair.from_secret(emitter_secret)
    except Exception:
        flash("❌ Clave secreta no válida.")
        return redirect(url_for("dashboard"))

    asset = Asset(ASSET_CODE, ASSET_ISSUER)

    # Construir transacción
    server = Server(horizon_url=STELLAR_SERVER)
    emitter_account = server.load_account(emitter_keypair.public_key)

    tx_builder = TransactionBuilder(
        source_account=emitter_account,
        network_passphrase=NETWORK_PASSPHRASE,
        base_fee=100
    ).append_set_trust_line_flags_op(
        trustor=trustor,
        asset=asset,
        set_flags=TrustLineFlags.AUTHORIZED_FLAG,
        source=emitter_keypair.public_key
    ).set_timeout(60)

    tx = tx_builder.build()
    tx.sign(emitter_keypair)

    try:
        response = server.submit_transaction(tx)
        flash(f"✅ Trustline autorizada para {trustor}")
    except Exception as e:
        flash(f"❌ Error al autorizar trustline: {str(e)}")

    return redirect(url_for("dashboard"))



@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
