from decimal import Decimal
from stellar_sdk import Server, Keypair, TransactionBuilder, Network, Asset
from api.config import get_secret

# Esta función normalmente consultaría el DEX o una API externa
# Por ahora devuelve un precio fijo para desarrollo

def get_market_price_real8(currency="USD") -> Decimal:
    # """
    # Devuelve el precio de REAL8 en la moneda solicitada (USD o EUR),
    # comparándolo en el DEX contra USDC o EURC según el caso.
    # """
    # server = Server("https://horizon.stellar.org")
    # real8_issuer = os.getenv("REAL8_ISSUER")
    # asset_real8 = Asset("REAL8", real8_issuer)
    #
    # if currency == "EUR":
    #     fiat_asset = Asset("EURC", "GBNZILSTVQDMWZTUSNYZB2OHYKTNJNXQBCSVIMW66ZX4M33Z5QI7UAGW")
    # else:
    #     fiat_asset = Asset("USDC", "GA5ZSEYBKG5JEFYPFOWLSMSX5FZ3UDFZY4LZ74JIXD3S5QSLT5K4BXQX")
    #
    # orderbook = server.orderbook(selling=asset_real8, buying=fiat_asset).call()
    #
    # if orderbook["bids"]:
    #     price = Decimal(orderbook["bids"][0]["price"])
    # else:
    #     price = Decimal("0.0")
    #
    # return price

    if currency=="USD":
        return Decimal("0.0100000")
    else:
        return Decimal("0.0090000")

def get_market_price_real8_usd():
    # """
    # Obtiene el precio actual de REAL8 en USD desde el Stellar DEX (mainnet).
    # """
    # server = Server("https://horizon.stellar.org")  # Mainnet Horizon
    #
    # # Definir el asset REAL8 y USD (suponiendo que esté emparejado con USDC)
    # real8_issuer = os.getenv("REAL8_ISSUER")
    # asset_real8 = Asset("REAL8", real8_issuer)
    # asset_usdc = Asset("USDC", "GA5ZSEYBKG5JEFYPFOWLSMSX5FZ3UDFZY4LZ74JIXD3S5QSLT5K4BXQX")  # Ejemplo: USDC oficial
    #
    # # Obtener la oferta más reciente en el DEX
    # orderbook = server.orderbook(selling=asset_real8, buying=asset_usdc).call()
    #
    # # Precio de la mejor oferta de compra
    # if orderbook["bids"]:
    #     price = Decimal(orderbook["bids"][0]["price"])
    # else:
    #     price = Decimal("0.0")  # Si no hay liquidez
    #
    # return price

    return Decimal("0.0100")


def send_real8_to_user(destination_public_key: str, amount: Decimal) -> dict:
    """
    Simula el envío de REAL8 al comprador en Stellar Testnet.
    """
    server = Server("https://horizon-testnet.stellar.org")
    network_passphrase = Network.TESTNET_NETWORK_PASSPHRASE

    # Datos de la cuenta distribuidora (clave secreta en entorno seguro)
    secret = get_secret("DISTRIBUTOR_SECRET_KEY")
    distributor_keypair = Keypair.from_secret(secret)
    distributor_public = distributor_keypair.public_key
    print(f"Distribuidor secret: {secret}")  # Para comprobar el valor

    # El asset REAL8 debe estar emitido en testnet
    asset_real8 = Asset("TEAL8", get_secret("REAL8_ISSUER"))

    # Cargar la cuenta distribuidora desde Horizon
    distributor_account = server.load_account(distributor_public)

    # Crear transacción
    transaction = (
        TransactionBuilder(
            source_account=distributor_account,
            network_passphrase=network_passphrase,
            base_fee=100,
        )
        .append_payment_op(destination=destination_public_key, amount=str(round(amount,7)), asset=asset_real8)
        .add_text_memo("Compra TEAL8 (testnet)")
        .set_timeout(30)
        .build()
    )

    # Firmar y enviar
    transaction.sign(distributor_keypair)
    response = server.submit_transaction(transaction)
    return response
