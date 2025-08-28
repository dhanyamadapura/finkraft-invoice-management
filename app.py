from flask import Flask, render_template, jsonify, request
import json
import os
import csv
from datetime import datetime
import sqlite3

app = Flask(__name__)

# Initialize database
def init_db():
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    
    # Create passengers table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS passengers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticket_number TEXT,
            first_name TEXT,
            last_name TEXT,
            email TEXT,
            download_status TEXT DEFAULT 'Pending',
            parse_status TEXT DEFAULT 'Pending',
            pdf_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create invoices table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            passenger_id INTEGER,
            invoice_number TEXT,
            date TEXT,
            airline TEXT,
            amount REAL,
            gstin TEXT,
            status TEXT DEFAULT 'Pending',
            pdf_path TEXT,
            reviewed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (passenger_id) REFERENCES passengers (id)
        )
    ''')
    
    # Add missing columns if they don't exist (for existing databases)
    try:
        cursor.execute('ALTER TABLE passengers ADD COLUMN pdf_path TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    try:
        cursor.execute('ALTER TABLE invoices ADD COLUMN reviewed BOOLEAN DEFAULT FALSE')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    conn.commit()
    conn.close()

# Load passenger data from CSV
def load_passenger_data():
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    
    # Check if data already exists
    cursor.execute('SELECT COUNT(*) FROM passengers')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    with open('data.csv', 'r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            if row['Ticket Number'] and row['First Name'] and row['Last Name']:
                # Generate email
                email = f"{row['First Name'].lower()}.{row['Last Name'].lower()}@email.com"
                
                cursor.execute('''
                    INSERT INTO passengers (ticket_number, first_name, last_name, email)
                    VALUES (?, ?, ?, ?)
                ''', (row['Ticket Number'], row['First Name'], row['Last Name'], email))
    
    conn.commit()
    conn.close()

@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/passengers')
def get_passengers():
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, ticket_number, first_name, last_name, email, 
               download_status, parse_status, pdf_path
        FROM passengers
        ORDER BY id
    ''')
    
    passengers = []
    for row in cursor.fetchall():
        passengers.append({
            'id': row[0],
            'ticket_number': row[1],
            'first_name': row[2],
            'last_name': row[3],
            'email': row[4],
            'download_status': row[5],
            'parse_status': row[6],
            'pdf_path': row[7],
            'booking_id': f"AI{row[0]:06d}"
        })
    
    conn.close()
    return jsonify(passengers)

@app.route('/api/invoices')
def get_invoices():
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT i.id, i.invoice_number, i.date, i.airline, i.amount, 
               i.gstin, i.status, p.first_name, p.last_name
        FROM invoices i
        JOIN passengers p ON i.passenger_id = p.id
        ORDER BY i.id
    ''')
    
    invoices = []
    for row in cursor.fetchall():
        invoices.append({
            'id': row[0],
            'invoice_number': row[1],
            'date': row[2],
            'airline': row[3],
            'amount': row[4],
            'gstin': row[5],
            'status': row[6],
            'passenger_name': f"{row[7]} {row[8]}"
        })
    
    conn.close()
    return jsonify(invoices)

@app.route('/api/download/<int:passenger_id>', methods=['POST'])
def download_invoice(passenger_id):
    import random
    import time
    
    # Simulate download process with realistic scenarios
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    
    # Get passenger info
    cursor.execute('SELECT ticket_number, first_name, last_name FROM passengers WHERE id = ?', (passenger_id,))
    passenger = cursor.fetchone()
    
    if not passenger:
        return jsonify({'status': 'error', 'message': 'Passenger not found'}), 404
    
    # Simulate different download outcomes
    time.sleep(1)  # Simulate network delay
    
    # 80% success rate, 15% not found, 5% error
    outcome = random.choices(['success', 'not_found', 'error'], weights=[80, 15, 5])[0]
    
    if outcome == 'success':
        # Create PDF path
        pdf_path = f"invoices/invoice_{passenger_id}.pdf"
        
        # Update download status
        cursor.execute('''
            UPDATE passengers 
            SET download_status = 'Downloaded' 
            WHERE id = ?
        ''', (passenger_id,))
        
        # Store PDF path
        cursor.execute('''
            UPDATE passengers 
            SET pdf_path = ? 
            WHERE id = ?
        ''', (pdf_path, passenger_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success', 
            'message': 'Invoice downloaded successfully',
            'pdf_path': pdf_path
        })
    
    elif outcome == 'not_found':
        cursor.execute('''
            UPDATE passengers 
            SET download_status = 'Not Found' 
            WHERE id = ?
        ''', (passenger_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'not_found', 
            'message': 'Invoice not found for this passenger'
        })
    
    else:  # error
        cursor.execute('''
            UPDATE passengers 
            SET download_status = 'Error' 
            WHERE id = ?
        ''', (passenger_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'error', 
            'message': 'Failed to download invoice - network error'
        })

@app.route('/api/parse/<int:passenger_id>', methods=['POST'])
def parse_invoice(passenger_id):
    import random
    import time
    
    # Simulate parsing process with realistic scenarios
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    
    # Check if passenger exists and is downloaded
    cursor.execute('SELECT first_name, last_name, download_status FROM passengers WHERE id = ?', (passenger_id,))
    passenger = cursor.fetchone()
    
    if not passenger:
        return jsonify({'status': 'error', 'message': 'Passenger not found'}), 404
    
    if passenger[2] != 'Downloaded':
        return jsonify({'status': 'error', 'message': 'Invoice must be downloaded first'}), 400
    
    # Simulate parsing delay
    time.sleep(2)  # Simulate processing time
    
    # 90% success rate, 10% error
    outcome = random.choices(['success', 'error'], weights=[90, 10])[0]
    
    if outcome == 'success':
        # Create realistic invoice data
        airlines = ['Thai Airways', 'Air India', 'IndiGo', 'SpiceJet', 'Vistara']
        airline = random.choice(airlines)
        
        invoice_data = {
            'passenger_id': passenger_id,
            'invoice_number': f"INV-2024-{passenger_id:03d}",
            'date': datetime.now().strftime('%m/%d/%Y'),
            'airline': airline,
            'amount': round(15000.0 + (passenger_id * 1000) + random.randint(-2000, 5000), 2),
            'gstin': f"29ABCDE{passenger_id:04d}F1ZX",
            'status': 'Parsed'
        }
        
        # Insert invoice
        cursor.execute('''
            INSERT INTO invoices (passenger_id, invoice_number, date, airline, amount, gstin, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (invoice_data['passenger_id'], invoice_data['invoice_number'], 
              invoice_data['date'], invoice_data['airline'], invoice_data['amount'],
              invoice_data['gstin'], invoice_data['status']))
        
        # Update passenger parse status
        cursor.execute('''
            UPDATE passengers 
            SET parse_status = 'Parsed' 
            WHERE id = ?
        ''', (passenger_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'success', 
            'message': 'Invoice parsed successfully',
            'invoice_data': invoice_data
        })
    
    else:  # error
        cursor.execute('''
            UPDATE passengers 
            SET parse_status = 'Error' 
            WHERE id = ?
        ''', (passenger_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'error', 
            'message': 'Failed to parse invoice - corrupted PDF'
        })

@app.route('/api/stats')
def get_stats():
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    
    # Get download stats
    cursor.execute('SELECT COUNT(*) FROM passengers WHERE download_status = "Downloaded"')
    downloaded = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM passengers')
    total = cursor.fetchone()[0]
    
    # Get parse stats
    cursor.execute('SELECT COUNT(*) FROM invoices WHERE status = "Parsed"')
    parsed = cursor.fetchone()[0]
    
    # Get total amount
    cursor.execute('SELECT SUM(amount) FROM invoices WHERE status = "Parsed"')
    total_amount = cursor.fetchone()[0] or 0
    
    # Get high value count
    cursor.execute('SELECT COUNT(*) FROM invoices WHERE amount > 20000')
    high_value = cursor.fetchone()[0]
    
    conn.close()
    
    return jsonify({
        'total_downloads': f"{downloaded}/{total}",
        'parsed_invoices': parsed,
        'total_amount': total_amount,
        'high_value': high_value
    })

@app.route('/api/pdf/<int:passenger_id>')
def view_pdf(passenger_id):
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT pdf_path, download_status FROM passengers WHERE id = ?', (passenger_id,))
    result = cursor.fetchone()
    
    conn.close()
    
    if not result or result[1] != 'Downloaded':
        return jsonify({'status': 'error', 'message': 'PDF not available'}), 404
    
    # Return the PDF URL for the frontend to handle
    return jsonify({
        'status': 'success',
        'pdf_url': f'/pdf/{passenger_id}',
        'message': 'PDF available for viewing'
    })

@app.route('/pdf/<int:passenger_id>')
def serve_pdf(passenger_id):
    """Serve a sample PDF file for demonstration purposes"""
    from flask import Response, abort
    import io
    import uuid
    
    # Check if passenger has downloaded status
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    cursor.execute('SELECT download_status FROM passengers WHERE id = ?', (passenger_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result or result[0] != 'Downloaded':
        abort(404)
    
    # Create a simple PDF content (in real app, this would be the actual PDF)
    pdf_content = f"""
    INVOICE DOCUMENT
    ================
    
    Passenger ID: {passenger_id}
    Invoice Number: INV-2024-{passenger_id:03d}
    Date: {datetime.now().strftime('%Y-%m-%d')}
    Airline: Thai Airways
    Amount: ₹{15000 + (passenger_id * 1000)}
    
    This is a sample invoice for demonstration purposes.
    In a real application, this would be the actual PDF
    downloaded from the airline portal.
    
    Generated by Finkraft Invoice Management System
    """
    
    # Create a BytesIO object to simulate file content
    file_like = io.BytesIO(pdf_content.encode('utf-8'))
    
    # Return the content as a downloadable file
    return Response(
        file_like.getvalue(),
        mimetype='text/plain',
        headers={
            'Content-Disposition': f'attachment; filename=invoice_{passenger_id}.txt',
            'Content-Type': 'text/plain; charset=utf-8'
        }
    )

@app.route('/api/review/<int:invoice_id>', methods=['POST'])
def toggle_review(invoice_id):
    data = request.get_json()
    review_status = data.get('reviewed', False)
    
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    
    # Update review status (we'll add a reviewed column to invoices table)
    cursor.execute('''
        UPDATE invoices 
        SET reviewed = ? 
        WHERE id = ?
    ''', (review_status, invoice_id))
    
    conn.commit()
    conn.close()
    
    return jsonify({
        'status': 'success',
        'message': f'Invoice {"marked for review" if review_status else "unmarked for review"}'
    })

if __name__ == '__main__':
    init_db()
    load_passenger_data()
    app.run(debug=True, port=5000)
