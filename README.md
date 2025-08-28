# Invoice Management Dashboard

A full-stack web application that automates the workflow of downloading and processing airline invoices from the Thai Airways ETAX portal. This system addresses the manual, time-consuming process of invoice retrieval and data extraction.

## 🚀 Features

### ✅ **Complete Feature Coverage**
- **Passenger Records Management** - View all passengers with download/parse status
- **Interactive Download Process** - Click-to-download with realistic success/error scenarios
- **PDF Parsing** - Extract structured data from invoices (Invoice No, Date, Airline, Amount, GSTIN)
- **Real-time Status Updates** - Live tracking of download and parse operations
- **Error Handling** - Graceful handling of network errors, not found, and parsing failures
- **Review System** - Checkbox-based review flagging for invoices
- **PDF Viewing** - Direct links to view downloaded PDFs
- **High Value Detection** - Automatic flagging of invoices above ₹20,000
- **Responsive Design** - Works seamlessly on desktop and mobile devices
- **Loading States** - Professional loading indicators and empty states

### 📊 **Dashboard Features**
- **Statistics Cards** - Total downloads, parsed invoices, total amount, high-value count
- **Passenger Records Table** - Complete passenger information with status badges
- **Parsed Invoices Table** - Detailed invoice information with review capabilities
- **Toast Notifications** - Real-time feedback for all operations

## 🛠️ Tech Stack

### **Backend**
- **Flask** - Lightweight Python web framework for REST APIs
- **SQLite** - File-based database for data persistence
- **Python** - Core language for business logic and data processing

### **Frontend**
- **HTML5/CSS3/JavaScript** - Vanilla web technologies for responsive UI
- **RESTful APIs** - Clean separation between frontend and backend

### **Data Processing**
- **PyPDF2/pdfplumber** - PDF text extraction and parsing
- **BeautifulSoup** - Web scraping for invoice downloads
- **Selenium** - Browser automation for dynamic content

## 📁 Project Structure

```
invoice-management-dashboard/
├── app.py                 # Flask backend application
├── requirements.txt       # Python dependencies
├── data.csv              # Passenger data input
├── invoices.db           # SQLite database (auto-generated)
├── templates/
│   └── dashboard.html    # Main dashboard UI
├── static/               # Static assets (CSS, JS, images)
├── invoices/             # Downloaded PDF storage
└── README.md            # Project documentation
```

## 🚀 Quick Start

### **Prerequisites**
- Python 3.7+
- pip (Python package installer)

### **Installation**

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/invoice-management-dashboard.git
   cd invoice-management-dashboard
   ```

2. **Create virtual environment (recommended)**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5000`

## 📋 Usage Guide

### **User Workflow**

1. **View Dashboard** - See all passenger records with current status
2. **Download Invoices** - Click "Download" button for each passenger
   - ✅ **Success** - Invoice downloaded successfully
   - ⚠️ **Not Found** - Invoice not available for this passenger
   - ❌ **Error** - Network or system error
3. **Parse Invoices** - Click "Parse" button for downloaded invoices
   - Extracts: Invoice Number, Date, Airline, Amount, GSTIN
   - Updates parse status and adds to invoices table
4. **Review Invoices** - Use checkboxes to flag invoices for review
5. **View PDFs** - Click "View PDF" links to access downloaded invoices

### **Status Indicators**

- 🔵 **Pending** - Operation not yet started
- 🟢 **Downloaded/Parsed** - Operation completed successfully
- 🟠 **Not Found** - Invoice not available
- 🔴 **Error** - Operation failed

## 🔧 API Endpoints

### **Passenger Management**
- `GET /api/passengers` - Retrieve all passenger records
- `POST /api/download/<id>` - Download invoice for passenger
- `POST /api/parse/<id>` - Parse downloaded invoice

### **Invoice Management**
- `GET /api/invoices` - Retrieve all parsed invoices
- `GET /api/pdf/<id>` - Get PDF link for passenger
- `POST /api/review/<id>` - Toggle review status

### **Statistics**
- `GET /api/stats` - Get dashboard statistics

## 🎯 Business Value

### **For Users**
- **Time Savings** - Automates manual invoice processing
- **Accuracy** - Reduces human error in data entry
- **Visibility** - Real-time tracking of invoice status
- **Organization** - Centralized invoice management

### **For Business**
- **Cost Reduction** - Eliminates manual data entry
- **Compliance** - Ensures all invoices are captured and processed
- **Scalability** - Can handle multiple airlines and high volumes
- **Audit Trail** - Complete history of invoice processing

## 🔍 Technical Implementation

### **Database Schema**
```sql
-- Passengers table
CREATE TABLE passengers (
    id INTEGER PRIMARY KEY,
    ticket_number TEXT,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    download_status TEXT DEFAULT 'Pending',
    parse_status TEXT DEFAULT 'Pending',
    pdf_path TEXT,
    created_at TIMESTAMP
);

-- Invoices table
CREATE TABLE invoices (
    id INTEGER PRIMARY KEY,
    passenger_id INTEGER,
    invoice_number TEXT,
    date TEXT,
    airline TEXT,
    amount REAL,
    gstin TEXT,
    status TEXT DEFAULT 'Pending',
    reviewed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
);
```

### **Error Handling**
- **Network Errors** - Graceful handling of connection issues
- **Data Validation** - Input validation and sanitization
- **User Feedback** - Toast notifications for all operations
- **Fallback States** - Empty states and error messages

## 🚀 Deployment

### **Local Development**
```bash
python app.py
```

### **Production Deployment**
1. Set up a production WSGI server (Gunicorn)
2. Configure reverse proxy (Nginx)
3. Set up SSL certificates
4. Configure environment variables

## 📈 Future Enhancements

- **Multi-airline Support** - Extend to other airline portals
- **Batch Processing** - Process multiple invoices simultaneously
- **Advanced Analytics** - Detailed reporting and insights
- **User Authentication** - Multi-user support with roles
- **API Rate Limiting** - Prevent abuse and ensure stability
- **Caching** - Improve performance with Redis
- **Real-time Updates** - WebSocket integration for live updates

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👨‍💻 Author

**Dhanya Madhapura**
- GitHub: [@dhanyamadhapura](https://github.com/dhanyamadhapura)
- LinkedIn: [Dhanya Madhapura](https://linkedin.com/in/dhanya-madhapura)
- Email: dhanya.madhapura@email.com

## 🙏 Acknowledgments

--Thanks to FINKRAFT for this problem statment 


---

**Built with ❤️ for full-stack development assessment**
