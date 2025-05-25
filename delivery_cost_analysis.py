import PyPDF2
import re
import os
import glob
import argparse
from datetime import datetime

def extract_order_data(pdf_path):
    try:
        reader = PyPDF2.PdfReader(pdf_path)
        text = "\n".join(page.extract_text() or '' for page in reader.pages)
        
        # Extract the order date from the PDF name or content
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
        
        # Extract total cost - try multiple patterns to handle different PDF formats
        total_cost = 0.0
        
        # Pattern 1: Look for "Total" followed by a dollar amount (with optional $ sign)
        total_patterns = [
            r"Total\s*\$?\s*(\d+\.\d{2})",
            r"TOTAL\s*\$?\s*(\d+\.\d{2})",
            r"Amount Due\s*\$?\s*(\d+\.\d{2})",
            r"AMOUNT DUE\s*\$?\s*(\d+\.\d{2})",
            r"Order Total\s*\$?\s*(\d+\.\d{2})",
            r"ORDER TOTAL\s*\$?\s*(\d+\.\d{2})",
            r"Total\s*\$?\s*(\d+,\d+\.\d{2})"  # For numbers with commas
        ]
        
        for pattern in total_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
            if matches:
                # Get the last match (often the grand total is last)
                total_str = matches[-1].replace(',', '')  # Remove commas if present
                try:
                    total_cost = float(total_str)
                    if total_cost > 0:
                        break
                except (ValueError, IndexError):
                    continue
        
        # If still no total found, try to find any number that looks like a total
        if total_cost == 0.0:
            # Look for the largest number that could be a total (likely between $20 and $200)
            money_matches = re.findall(r'\$?\s*(\d{1,3}(?:,\d{3})*\.\d{2})\b', text)
            potential_totals = []
            
            for match in money_matches:
                try:
                    amount = float(match.replace(',', ''))
                    if 20 <= amount <= 200:  # Reasonable range for a grocery order total
                        potential_totals.append(amount)
                except ValueError:
                    continue
            
            if potential_totals:
                total_cost = max(potential_totals)  # Assume the largest is the total
        
        return {
            "file": os.path.basename(pdf_path),
            "order_number": order_number,
            "order_date": order_date,
            "total_cost": total_cost
        }
    except Exception as e:
        print(f"Error processing {pdf_path}: {e}")
        return {
            "file": os.path.basename(pdf_path),
            "order_number": "Error",
            "order_date": "Error",
            "total_cost": 0.0
        }

def get_all_pdfs(directory):
    # Get all PDF files in the directory
    pdf_files = glob.glob(os.path.join(directory, "*.pdf"))
    return pdf_files

if __name__ == "__main__":
    # Set up argument parser
    parser = argparse.ArgumentParser(description='Analyze delivery costs from Lufa Farms invoices')
    parser.add_argument('pdf_dir', nargs='?', default='pdfs', 
                        help='Directory containing PDF invoices or a single PDF file')
    parser.add_argument('--baskets-per-order', type=float, default=2.5,
                        help='Average number of baskets per order (default: 2.5)')
    args = parser.parse_args()
    
    # Get PDF directory from arguments
    pdf_dir = args.pdf_dir
    baskets_per_order = args.baskets_per_order
    
    # Ensure pdf_dir is a directory, otherwise use the file itself
    if os.path.isfile(pdf_dir):
        pdf_files = [pdf_dir]
    else:
        pdf_files = get_all_pdfs(pdf_dir)
    
    if not pdf_files:
        print(f"No PDF files found in {pdf_dir}")
        sys.exit(1)
    
    results = []
    total_cost = 0.0
    total_orders = 0
    months_data = {}  # To track costs per month
    
    # Process each PDF file
    for pdf_file in pdf_files:
        result = extract_order_data(pdf_file)
        results.append(result)
        total_cost += result["total_cost"]
        total_orders += 1
        
        # Track costs per month
        if result["order_date"] not in ["Unknown", "Error"]:
            try:
                order_date = datetime.strptime(result["order_date"], "%Y-%m-%d")
                month_key = order_date.strftime("%Y-%m")  # Format: YYYY-MM
                if month_key not in months_data:
                    months_data[month_key] = {"cost": 0.0, "orders": 0}
                months_data[month_key]["cost"] += result["total_cost"]
                months_data[month_key]["orders"] += 1
            except ValueError:
                pass
    
    # Calculate metrics
    avg_cost_per_delivery = total_cost / total_orders if total_orders > 0 else 0
    total_baskets = total_orders * baskets_per_order
    avg_cost_per_basket = total_cost / total_baskets if total_baskets > 0 else 0
    
    # Calculate monthly averages
    monthly_avg_cost = {}
    for month, data in months_data.items():
        monthly_avg_cost[month] = data["cost"] / data["orders"] if data["orders"] > 0 else 0
    
    # Find the month with highest average cost per delivery
    max_avg_month = max(monthly_avg_cost, key=monthly_avg_cost.get) if monthly_avg_cost else "N/A"
    max_avg_cost = monthly_avg_cost.get(max_avg_month, 0) if max_avg_month != "N/A" else 0
    
    # Print individual order results
    print(f"{'File':<30} {'Order #':<15} {'Date':<12} {'Cost ($)':<10}")
    print("-" * 70)
    for result in results:
        print(f"{result['file']:<30} {result['order_number']:<15} {result['order_date']:<12} ${result['total_cost']:.2f}")
    
    # Print summary statistics
    print("\n" + "="*70)
    print("DELIVERY COST ANALYSIS SUMMARY:")
    print("="*70)
    print(f"Total number of orders analyzed: {total_orders}")
    print(f"Total cost of all orders: ${total_cost:.2f}")
    print(f"Average cost per delivery: ${avg_cost_per_delivery:.2f}")
    print(f"Average cost per basket (assuming {baskets_per_order} baskets per order): ${avg_cost_per_basket:.2f}")
    
    # Print monthly statistics if available
    if months_data:
        print("\n" + "-"*70)
        print("MONTHLY AVERAGES:")
        print(f"{'Month':<10} {'Avg Cost/Delivery':<20} {'Orders'}")
        print("-"*40)
        for month in sorted(months_data.keys()):
            month_avg = months_data[month]["cost"] / months_data[month]["orders"]
            print(f"{month:<10} ${month_avg:<19.2f} {months_data[month]['orders']}")
        
        print("\n" + "-"*70)
        print(f"Month with highest average cost per delivery: {max_avg_month} (${max_avg_cost:.2f})")
    
    print("="*70)
