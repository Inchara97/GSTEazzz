from flask import Flask, render_template, request, redirect, url_for, send_file
import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

app = Flask(__name__)


class GSTInvoice:
    def __init__(self, invoice_id, date, amount, gst_rate):
        self.invoice_id = invoice_id
        self.date = date
        self.amount = amount
        self.gst_rate = gst_rate
        self.gst_amount = self.calculate_gst()

    def calculate_gst(self):
        return self.amount * (self.gst_rate / 100)

    def display_invoice(self):
        return {
            'invoice_id': self.invoice_id,
            'date': self.date,
            'amount': self.amount,
            'gst_amount': self.gst_amount,
            'total': self.amount + self.gst_amount
        }


class GSTSimplifyAI:
    def __init__(self):
        self.invoices = []
        self.total_tax_collected = 0
        self.total_sales = 0

    def add_invoice(self, invoice):
        self.invoices.append(invoice)
        self.total_sales += invoice.amount
        self.total_tax_collected += invoice.gst_amount

    def generate_return_report(self):
        report_data = {
            'total_sales': self.total_sales,
            'total_tax_collected': self.total_tax_collected,
            'filing_date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'invoices': [invoice.display_invoice() for invoice in self.invoices]
        }
        return report_data


gst_system = GSTSimplifyAI()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/add_invoice', methods=['GET', 'POST'])
def add_invoice():
    if request.method == 'POST':
        invoice_id = request.form['invoice_id']
        date = request.form['date']
        amount = float(request.form['amount'])
        gst_rate = float(request.form['gst_rate'])
        invoice = GSTInvoice(invoice_id, date, amount, gst_rate)
        gst_system.add_invoice(invoice)
        return redirect(url_for('view_invoices'))
    return render_template('invoice.html')


@app.route('/view_invoices')
def view_invoices():
    invoices = [invoice.display_invoice() for invoice in gst_system.invoices]
    return render_template('invoice_list.html', invoices=invoices)


@app.route('/generate_report')
def generate_report():
    report_data = gst_system.generate_return_report()

    # Generate PDF Report
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 12)
    c.drawString(100, 750, f"GST Report - Filing Date: {report_data['filing_date']}")
    c.drawString(100, 730, f"Total Sales: ₹{report_data['total_sales']}")
    c.drawString(100, 710, f"Total Tax Collected: ₹{report_data['total_tax_collected']}")

    y_position = 680
    for invoice in report_data['invoices']:
        c.drawString(100, y_position, f"Invoice ID: {invoice['invoice_id']}")
        c.drawString(100, y_position - 15, f"Date: {invoice['date']}")
        c.drawString(100, y_position - 30, f"Amount: ₹{invoice['amount']}")
        c.drawString(100, y_position - 45, f"GST Amount: ₹{invoice['gst_amount']}")
        c.drawString(100, y_position - 60, f"Total: ₹{invoice['total']}")
        y_position -= 80
        if y_position < 100:
            c.showPage()  # Create a new page if we run out of space

    c.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="GST_Report.pdf", mimetype="application/pdf")


if __name__ == '__main__':
    app.run(debug=True)
