from django.template.defaultfilters import lower, upper
from flask import Blueprint, request, jsonify
from decimal import Decimal
import uuid
import os
import stripe
from datetime import datetime
from api.comprar_real8.services import get_market_price_real8, send_real8_to_user
from flask import render_template
from api.config import get_secret

template_path = os.path.join(os.path.dirname(__file__), "templates")
print(f"Template Path: {template_path}")

comprar_real8_bp = Blueprint(
    'comprar_real8',
    __name__,
    template_folder=template_path
)
STRIPE_SECRET_KEY = get_secret("STRIPE_SECRET_KEY")
STRIPE_PUBLIC_KEY = get_secret("STRIPE_PUBLIC_KEY")
# Simulador de "base de datos" temporal
buy_requests = []

@comprar_real8_bp.route("/api/comprar-real8", methods=["GET"])
def mostrar_formulario():
    return render_template("formulario.html")

@comprar_real8_bp.route("/api/comprar-real8/resumen", methods=["POST"])
def mostrar_resumen():
    data = request.form
    print(f"Data: {data}")  # Para comprobar el valor
    stripe.api_key = get_secret("STRIPE_SECRET_KEY")
    print(f"Stripe Key: {stripe.api_key}")
    # Extraemos los datos enviados
    amount_fiat = Decimal(str(data.get("amount_fiat")))
    fiat_currency = data.get("fiat_currency", "USD")
    print(f"Data: {get_market_price_real8(fiat_currency)}")  # Para comprobar el valor
    real8_amount = round(amount_fiat / get_market_price_real8(fiat_currency),7)

    # Calcular tarifas de Stripe
    stripe_fee = round((float(amount_fiat) * 0.015) + 0.25, 2)
    total_amount = round(amount_fiat + Decimal(stripe_fee), 2)

    # Pasamos todo al template
    return render_template("resumen.html", amount_fiat=amount_fiat,
                           amount_real8=real8_amount, stripe_fee=stripe_fee,
                           total_amount=total_amount, fiat_currency=fiat_currency, public_key=request.form['public_key'])

@comprar_real8_bp.route("/api/comprar-real8/solicitud", methods=["POST"])
def solicitud_y_envio():
    data = request.form

    public_key = data.get("public_key")
    fiat_currency = data.get("fiat_currency", "USD")
    amount_fiat = Decimal(str(data.get("amount_fiat")))

    if not public_key or not amount_fiat:
        return jsonify({"error": "Faltan campos obligatorios"}), 400

    markup_percent = Decimal("5.0")
    market_price = get_market_price_real8(fiat_currency)
    price_with_markup = market_price * (1 + (markup_percent / 100))
    real8_to_send = amount_fiat / price_with_markup

    try:
        result = send_real8_to_user(public_key, real8_to_send)
        return jsonify({
            "status": "success",
            "public_key": public_key,
            "real8_sent": float(round(real8_to_send, 4)),
            "price_with_markup": float(price_with_markup),
            "transaction_hash": result["hash"]
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@comprar_real8_bp.route("/api/comprar-real8/precio")
def obtener_precio():
    moneda = request.args.get("moneda", "USD")
    precio = float(get_market_price_real8(currency=moneda))
    return jsonify({"price": precio})

@comprar_real8_bp.route('/api/crear-sesion', methods=["POST"])
def crear_sesion():
    try:
        amount_fiat = float(request.form['amount_fiat'])
        currency = lower(request.form['currency'])
        cpk = request.form['cpk']
        ar8 = request.form['ar8']
        print(f"{amount_fiat}: {currency}")
        stripe_fee = (amount_fiat * 0.015) + 0.25  # tarifa de Stripe (1.5% + 0.25€)
        total_to_charge = amount_fiat + stripe_fee  # El total que le cobramos al comprador
        stripe.api_key = get_secret("STRIPE_SECRET_KEY")
        print(f"Private Stripe Key: {stripe.api_key}")
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': currency,
                    'product_data': {
                        'name': 'REAL8',
                    },
                    'unit_amount': int(amount_fiat * 100),  # Stripe usa centavos, así que multiplicamos por 100
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url='http://localhost:5000/exito?session_id={CHECKOUT_SESSION_ID}&cpk='+cpk+'&amount_real8='+ar8,
            cancel_url='http://localhost:5000/cancelado',
        )
        return jsonify({'sessionId': session.id})
    except Exception as e:
        return jsonify(error=str(e)), 403

@comprar_real8_bp.route('/exito')
def exito():
    session_id = request.args.get('session_id')
    session = stripe.checkout.Session.retrieve(session_id)

    if session.payment_status == 'paid':
        # Procesa el pago y envía los tokens REAL8 al comprador
        public_key = upper(request.args.get('cpk'))  # O cualquier dato del cliente
        amount_real8 = session.amount_total / 100  # Convertir de centavos a EUR
        send_real8_to_user(public_key, request.args.get('amount_real8'))
        return render_template('exito.html', status='Pago completado')
    else:
        return render_template('exito.html', status='Pago fallido')