from flask import Flask, render_template, request, redirect, session, send_file
import sqlite3
import os
from datetime import datetime
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = 'your_secret_key'

USERNAME = "admin"
PASSWORD = "1234"

def generate_bill_pdf(bill_data, output_path):
    c = canvas.Canvas(output_path)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, 800, "🧾 Lumis Billing Pro")

    c.setFont("Helvetica", 12)
    c.drawString(50, 770, f"Customer: {bill_data['customer']}")
    c.drawString(50, 750, f"Date: {bill_data['date']}")

    y = 720
    for line in bill_data['items'].split('\n'):
        c.drawString(50, y, line)
        y -= 20

    c.drawString(50, y-20, f"Subtotal: ₹{bill_data['subtotal']}")
    c.drawString(50, y-40, f"GST: {bill_data['gst']}%")
    c.drawString(50, y-60, f"Total: ₹{bill_data['total']}")
    c.save()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        uname = request.form['username']
        pwd = request.form['password']
        if uname == USERNAME and pwd == PASSWORD:
            session['user'] = uname
            return redirect('/')
        else:
            return render_template('login.html', message="❌ Invalid Credentials")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect('/login')

@app.route("/", methods=["GET", "POST"])
def home():
    if 'user' not in session:
        return redirect('/login')

    if request.method == "POST":
        customer = request.form['customer']
        items = request.form['items']
        subtotal = float(request.form['subtotal'])
        gst = float(request.form['gst'])
        total = subtotal + (subtotal * gst / 100)
        date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = sqlite3.connect('db/database.db')
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bills (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                customer TEXT,
                items TEXT,
                subtotal REAL,
                gst REAL,
                total REAL,
                date TEXT
            )
        """)
        cursor.execute("INSERT INTO bills (customer, items, subtotal, gst, total, date) VALUES (?, ?, ?, ?, ?, ?)",
                       (customer, items, subtotal, gst, total, date))
        conn.commit()
        conn.close()

        return render_template("index.html", message="✅ Bill Saved Successfully!", products={})

    return render_template("index.html", message=None, products={})

@app.route("/history")
def history():
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect('db/database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bills ORDER BY id DESC")
    records = cursor.fetchall()
    conn.close()
    return render_template("history.html", records=records)

@app.route('/export/<int:bill_id>')
def export_pdf(bill_id):
    if 'user' not in session:
        return redirect('/login')

    conn = sqlite3.connect('db/database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM bills WHERE id=?", (bill_id,))
    data = cursor.fetchone()
    conn.close()

    if data:
        bill_data = {
            'customer': data[1],
            'items': data[2],
            'subtotal': data[3],
            'gst': data[4],
            'total': data[5],
            'date': data[6]
        }
        filename = f"bill_{bill_id}.pdf"
        output_path = os.path.join("db", filename)
        generate_bill_pdf(bill_data, output_path)
        return send_file(output_path, as_attachment=True)

    return "❌ Bill not found", 404

if __name__ == "__main__":
    if not os.path.exists('db'):
        os.mkdir('db')
    app.run(debug=True)
