from flask import Flask
from api.comprar_real8.routes import comprar_real8_bp

app = Flask(__name__)
app.register_blueprint(comprar_real8_bp)

if __name__ == "__main__":
    app.run(debug=True)
