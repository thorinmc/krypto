from flask import Flask

app = Flask(__name__)

# =========================
# 🎨 TUTAJ ZMIENIASZ STYL
# =========================
STYLE = {
    "bg_color": "#FF1871",
    "text_color": "#ffffff",
    "font_size": "20px",
    "font_family": "Arial",
    "padding": "40px",
    "box_color": "rgba(0,0,0,0.6)",
    "title_size": "40px"
}

# =========================
# 🏠 ROUTE HOME
# =========================
@app.route("/")
def home():
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Panel</title>

        <style>
            body {{
                margin: 0;
                background: {STYLE['bg_color']};
                color: {STYLE['text_color']};
                font-size: {STYLE['font_size']};
                font-family: {STYLE['font_family']};
                background-image: url('https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcS6xlRkliEZYciqqMDSWzvTeoTPX72UlHVN9w&s');
                background-size: cover;
                background-position: center;
            }}

            .container {{
                max-width: 900px;
                margin: 80px auto;
                padding: {STYLE['padding']};
                background: {STYLE['box_color']};
                border-radius: 12px;
                text-align: center;
            }}

            h1 {{
                font-size: {STYLE['title_size']};
                margin-bottom: 20px;
            }}

            .btn {{
                display: inline-block;
                margin-top: 20px;
                padding: 10px 20px;
                background: #00bcd4;
                color: white;
                text-decoration: none;
                border-radius: 8px;
            }}

            .btn:hover {{
                background: #0097a7;
            }}
        </style>
    </head>

    <body>
        <div class="container">
            <h1>Szabelki tanio</h1>
            <p>szabelki zrobione jak dla obcego a sprzedaje jakby byly dobre</p>

            <a class="btn" href="/about">Kupuj</a>
        </div>
    </body>
    </html>
    """

# =========================
# ℹ️ ROUTE ABOUT
# =========================
@app.route("/about")
def about():
    return """
    <h1 style="text-align:center;margin-top:100px;">
        nalezy się 10 000
    </h1>
    <h1 style="text-align:center;margin-top:10px;">
        jestes zgejowany do zapłacenia tej kwoty w innym wypadku wpierol
    </h1>
    """

# =========================
# 🚀 START SERWERA
# =========================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",   # działa na sieci lokalnej
        port=5000,
        debug=True
    )