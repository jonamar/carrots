import PyPDF2
import re
import os
import glob
import argparse
from datetime import datetime

def extract_carrots_kg(pdf_path):
    try:
        reader = PyPDF2.PdfReader(pdf_path)
        text = "\n".join(page.extract_text() or '' for page in reader.pages)
        
        # Extract the order date from the PDF name or content if possible
        order_date = None
        date_pattern = re.compile(r"ORDER-\d+-(\d{4}-\d{2}-\d{2})")
        date_match = date_pattern.search(pdf_path)
        if date_match:
            try:
                order_date = datetime.strptime(date_match.group(1), "%Y-%m-%d").strftime("%Y-%m-%d")
            except ValueError:
                pass
        
        # If date not in filename, try to extract from content
        if not order_date:
            date_pattern = re.compile(r"Delivery date: ([A-Za-z]+ \d+, \d{4})")
            date_match = date_pattern.search(text)
            if date_match:
                try:
                    order_date = datetime.strptime(date_match.group(1), "%B %d, %Y").strftime("%Y-%m-%d")
                except ValueError:
                    order_date = "Unknown"
        
        # Extract order number
        order_number = "Unknown"
        order_pattern = re.compile(r"Order #(\d+)")
        order_match = order_pattern.search(text)
        if order_match:
            order_number = order_match.group(1)
        
        # Regex to find carrot entries (case-insensitive, matches both 'Carrot' and 'carrots')
        carrot_pattern = re.compile(r"(Not So Pretty Carrots.*?)(\d+(?:\.\d+)?)g", re.IGNORECASE)
        total_grams = 0
        for match in carrot_pattern.finditer(text):
            grams = float(match.group(2))
            total_grams += grams
        
        total_kg = total_grams / 1000
        return {
            "file": os.path.basename(pdf_path),
            "order_number": order_number,
            "order_date": order_date,
            "kg": total_kg
        }
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return {
            "file": os.path.basename(pdf_path),
            "order_number": "Error",
            "order_date": "Error",
            "kg": 0
        }

def get_all_pdfs(directory):
    # Get all PDF files in the directory
    pdf_files = glob.glob(os.path.join(directory, "*.pdf"))
    return pdf_files

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Calculate total carrots ordered from Lufa Farms')
    parser.add_argument('pdf_dir', nargs='?', default='pdfs', help='Directory containing PDF invoices or a single PDF file')
    parser.add_argument('--avg-carrot-weight', type=float, default=100.0, 
                        help='Average weight of a single carrot in grams (default: 100g)')
    args = parser.parse_args()
    
    # Get PDF directory from arguments
    pdf_dir = args.pdf_dir
    avg_carrot_weight = args.avg_carrot_weight
    
    # Ensure pdf_dir is a directory, otherwise use the file itself
    if os.path.isfile(pdf_dir):
        pdf_files = [pdf_dir]
    else:
        pdf_files = get_all_pdfs(pdf_dir)
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}")
        sys.exit(1)
    
    results = []
    total_kg = 0
    oldest_date = None
    months_data = {}  # To track carrots per month
    
    # Process each PDF file
    for pdf_file in pdf_files:
        result = extract_carrots_kg(pdf_file)
        results.append(result)
        total_kg += result["kg"]
        
        # Track oldest order date
        if result["order_date"] != "Unknown" and result["order_date"] != "Error":
            try:
                order_date = datetime.strptime(result["order_date"], "%Y-%m-%d")
                if oldest_date is None or order_date < oldest_date:
                    oldest_date = order_date
                
                # Track carrots per month
                month_key = order_date.strftime("%Y-%m")  # Format: YYYY-MM
                if month_key not in months_data:
                    months_data[month_key] = {"kg": 0, "orders": 0}
                months_data[month_key]["kg"] += result["kg"]
                months_data[month_key]["orders"] += 1
            except ValueError:
                pass
    
    # Print individual results
    print(f"{'File':<30} {'Order #':<15} {'Date':<12} {'KG':<10}")
    print("-" * 70)
    for result in results:
        print(f"{result['file']:<30} {result['order_number']:<15} {result['order_date']:<12} {result['kg']:.3f}")
    
    # Calculate KPIs
    total_weight_kg = total_kg
    total_weight_g = total_weight_kg * 1000
    estimated_carrots = total_weight_g / avg_carrot_weight
    carrots_per_order = estimated_carrots / len(results) if results else 0
    oldest_date_str = oldest_date.strftime("%Y-%m-%d") if oldest_date else "Unknown"
    
    # Calculate month with most carrots and average orders per month
    month_most_carrots = None
    max_kg = 0
    total_months = len(months_data)
    total_orders = sum(data["orders"] for data in months_data.values())
    avg_orders_per_month = total_orders / total_months if total_months > 0 else 0
    
    for month, data in months_data.items():
        if data["kg"] > max_kg:
            max_kg = data["kg"]
            month_most_carrots = month
    
    # Calculate total carrots for the top month
    top_month_carrots = 0
    if month_most_carrots and max_kg > 0:
        top_month_carrots = (max_kg * 1000) / avg_carrot_weight
    
    # Format month for display
    if month_most_carrots:
        month_date = datetime.strptime(month_most_carrots, "%Y-%m")
        month_display = month_date.strftime("%B %Y")
    else:
        month_display = "Unknown"
    
    # Print KPIs
    print("-" * 70)
    print(f"KPI SUMMARY:")
    print(f"Total weight of all carrots ordered: {total_weight_kg:.3f} kg")
    print(f"Estimated total number of carrots ordered: {estimated_carrots:.1f} carrots (based on {avg_carrot_weight}g per carrot)")
    print(f"CPO (Carrots Per Order): {carrots_per_order:.1f} carrots")
    print(f"Oldest order date: {oldest_date_str}")
    print(f"Average orders per month: {avg_orders_per_month:.1f}")
    print(f"Carrot Top (Month): {month_display} ({max_kg:.3f} kg, {top_month_carrots:.1f} carrots)")
    print("-" * 70)
