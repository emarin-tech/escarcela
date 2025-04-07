from flask import Blueprint, request, jsonify
from decimal import Decimal
import uuid
import os
from datetime import datetime
from api.comprar_real8.services import get_market_price_real8, send_real8_to_user
from flask import render_template

template_path = os.path.join(os.path.dirname(__file__), "templates")
print(f"Template Path: {template_path}")

comprar_real8_bp = Blueprint(
    'comprar_real8',
    __name__,
    template_folder=template_path
)

# Simulador de "base de datos" temporal
buy_requests = []

@comprar_real8_bp.route("/comprar-real8", methods=["GET"])
def mostrar_formulario():
    return render_template("formulario.html")

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
