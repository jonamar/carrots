import PyPDF2
import re
import os
import glob
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
    import sys
    
    # Default to "pdfs" directory if no path provided
    pdf_dir = sys.argv[1] if len(sys.argv) > 1 else "pdfs"
    
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
    
    # Process each PDF file
    for pdf_file in pdf_files:
        result = extract_carrots_kg(pdf_file)
        results.append(result)
        total_kg += result["kg"]
    
    # Print individual results
    print(f"{'File':<30} {'Order #':<15} {'Date':<12} {'KG':<10}")
    print("-" * 70)
    for result in results:
        print(f"{result['file']:<30} {result['order_number']:<15} {result['order_date']:<12} {result['kg']:.3f}")
    
    # Print total
    print("-" * 70)
    print(f"Total KG of carrots purchased across all {len(results)} PDFs: {total_kg:.3f} kg")
