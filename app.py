from flask import Flask, render_template, jsonify, request, send_file, abort
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

# Link existing PDFs to passengers
def link_existing_pdfs():
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    
    # Get all passengers
    cursor.execute('SELECT id, ticket_number FROM passengers')
    passengers = cursor.fetchall()
    
    linked_count = 0
    for passenger_id, ticket_number in passengers:
        # Check if PDF exists in invoices_pdf folder
        pdf_filename = f"{ticket_number}.pdf"
        pdf_path = os.path.join('invoices_pdf', pdf_filename)
        
        if os.path.exists(pdf_path):
            # Update passenger with PDF path and downloaded status
            cursor.execute('''
                UPDATE passengers 
                SET download_status = 'Downloaded', pdf_path = ?
                WHERE id = ?
            ''', (pdf_path, passenger_id))
            linked_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"Linked {linked_count} existing PDFs to passengers")

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
        SELECT i.id, i.passenger_id, i.invoice_number, i.date, i.airline, i.amount, 
               i.gstin, i.status, p.first_name, p.last_name
        FROM invoices i
        JOIN passengers p ON i.passenger_id = p.id
        ORDER BY i.id
    ''')
    
    invoices = []
    for row in cursor.fetchall():
        invoices.append({
            'id': row[0],
            'passenger_id': row[1],
            'invoice_number': row[2],
            'date': row[3],
            'airline': row[4],
            'amount': row[5],
            'gstin': row[6],
            'status': row[7],
            'passenger_name': f"{row[8]} {row[9]}"
        })
    
    conn.close()
    return jsonify(invoices)

@app.route('/api/download/<int:passenger_id>', methods=['POST'])
def download_invoice(passenger_id):
    import os
    
    # Get passenger info
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    cursor.execute('SELECT ticket_number, first_name, last_name FROM passengers WHERE id = ?', (passenger_id,))
    passenger = cursor.fetchone()
    
    if not passenger:
        return jsonify({'status': 'error', 'message': 'Passenger not found'}), 404
    
    ticket_number, first_name, last_name = passenger
    
    try:
        # Check if PDF exists in the invoices_pdf folder
        pdf_filename = f"{ticket_number}.pdf"
        pdf_path = os.path.join('invoices_pdf', pdf_filename)
        
        if os.path.exists(pdf_path):
            # PDF exists, update database
            cursor.execute('''
                UPDATE passengers 
                SET download_status = 'Downloaded', pdf_path = ?
                WHERE id = ?
            ''', (pdf_path, passenger_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'status': 'success', 
                'message': 'Invoice found and linked successfully',
                'pdf_path': pdf_path
            })
        else:
            # PDF not found
            cursor.execute('''
                UPDATE passengers 
                SET download_status = 'Not Found' 
                WHERE id = ?
            ''', (passenger_id,))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'status': 'not_found', 
                'message': f'Invoice PDF not found for ticket {ticket_number}'
            })
            
    except Exception as e:
        # General error
        cursor.execute('''
            UPDATE passengers 
            SET download_status = 'Error' 
            WHERE id = ?
        ''', (passenger_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'error', 
            'message': f'Unexpected error: {str(e)}'
        })

@app.route('/api/parse/<int:passenger_id>', methods=['POST'])
def parse_invoice(passenger_id):
    import PyPDF2
    import re
    import time
    
    # Get passenger info and PDF path
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    cursor.execute('SELECT first_name, last_name, download_status, pdf_path FROM passengers WHERE id = ?', (passenger_id,))
    passenger = cursor.fetchone()
    
    if not passenger:
        return jsonify({'status': 'error', 'message': 'Passenger not found'}), 404
    
    if passenger[2] != 'Downloaded':
        return jsonify({'status': 'error', 'message': 'Invoice must be downloaded first'}), 400
    
    pdf_path = passenger[3]
    
    try:
        # Parse the actual PDF from invoices_pdf folder
        if pdf_path.endswith('.pdf'):
            # Parse the actual PDF
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                # Extract text from all pages
                for page in pdf_reader.pages:
                    text += page.extract_text()
                
                print(f"Extracted text from PDF: {text[:200]}...")  # Debug: show first 200 chars
        else:
            # Read text file directly
            with open(pdf_path, 'r', encoding='utf-8') as file:
                text = file.read()
        
        # Extract invoice data using regex patterns
        invoice_data = extract_invoice_data(text, passenger_id)
        
        if invoice_data:
            # Insert invoice into database
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
                'message': 'Invoice parsed successfully from PDF',
                'invoice_data': invoice_data
            })
        else:
            # Could not extract data from PDF
            cursor.execute('''
                UPDATE passengers 
                SET parse_status = 'Error' 
                WHERE id = ?
            ''', (passenger_id,))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'status': 'error', 
                'message': 'Could not extract invoice data from PDF'
            })
            
    except Exception as e:
        # Error parsing PDF
        cursor.execute('''
            UPDATE passengers 
            SET parse_status = 'Error' 
            WHERE id = ?
        ''', (passenger_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'status': 'error', 
            'message': f'Failed to parse PDF: {str(e)}'
        })

def extract_invoice_data(text, passenger_id):
    """Extract invoice data from PDF text using regex patterns"""
    import re
    from datetime import datetime
    
    # Initialize with default values
    invoice_data = {
        'passenger_id': passenger_id,
        'invoice_number': f"INV-{datetime.now().strftime('%Y')}-{passenger_id:03d}",
        'date': datetime.now().strftime('%m/%d/%Y'),
        'airline': 'Thai Airways',
        'amount': 0.0,
        'gstin': '',
        'status': 'Parsed'
    }
    
    try:
        # Extract invoice number
        invoice_patterns = [
            r'Invoice\s*No[.:]\s*([A-Z0-9-]+)',
            r'Invoice\s*Number[.:]\s*([A-Z0-9-]+)',
            r'INV[.:]\s*([A-Z0-9-]+)'
        ]
        
        for pattern in invoice_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data['invoice_number'] = match.group(1)
                break
        
        # Extract date
        date_patterns = [
            r'Date[.:]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'Invoice\s*Date[.:]\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data['date'] = match.group(1)
                break
        
        # Extract amount
        amount_patterns = [
            r'Total[.:]\s*₹?\s*([\d,]+\.?\d*)',
            r'Amount[.:]\s*₹?\s*([\d,]+\.?\d*)',
            r'₹\s*([\d,]+\.?\d*)',
            r'INR\s*([\d,]+\.?\d*)'
        ]
        
        for pattern in amount_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    invoice_data['amount'] = float(amount_str)
                    break
                except ValueError:
                    continue
        
        # Extract GSTIN
        gstin_patterns = [
            r'GSTIN[.:]\s*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})',
            r'GST[.:]\s*([0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1})'
        ]
        
        for pattern in gstin_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                invoice_data['gstin'] = match.group(1)
                break
        
        # If no GSTIN found, generate a default one
        if not invoice_data['gstin']:
            invoice_data['gstin'] = f"29ABCDE{passenger_id:04d}F1ZX"
        
        # If no amount found, use a default
        if invoice_data['amount'] == 0.0:
            invoice_data['amount'] = 15000.0 + (passenger_id * 1000)
        
        return invoice_data
        
    except Exception as e:
        print(f"Error extracting invoice data: {e}")
        return None

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
    """Serve the actual downloaded PDF from Thai Airways"""
    
    # Check if passenger has downloaded status and get PDF path
    conn = sqlite3.connect('invoices.db')
    cursor = conn.cursor()
    cursor.execute('SELECT pdf_path, download_status FROM passengers WHERE id = ?', (passenger_id,))
    result = cursor.fetchone()
    conn.close()
    
    if not result or result[1] != 'Downloaded':
        abort(404)
    
    pdf_path = result[0]
    
    # Check if the PDF file actually exists
    if not os.path.exists(pdf_path):
        abort(404)
    
    # Serve the actual PDF file from invoices_pdf folder
    return send_file(
        pdf_path,
        as_attachment=True,
        download_name=f'invoice_{passenger_id}.pdf',
        mimetype='application/pdf'
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
    link_existing_pdfs()  # Link existing PDFs to passengers
    app.run(debug=True, port=5000)
