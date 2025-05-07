import PyPDF2
import re

def extract_carrots_kg(pdf_path):
    reader = PyPDF2.PdfReader(pdf_path)
    text = "\n".join(page.extract_text() or '' for page in reader.pages)
    # Regex to find carrot entries (case-insensitive, matches both 'Carrot' and 'carrots')
    carrot_pattern = re.compile(r"(Not So Pretty Carrots.*?)(\d+(?:\.\d+)?)g", re.IGNORECASE)
    total_grams = 0
    for match in carrot_pattern.finditer(text):
        grams = float(match.group(2))
        total_grams += grams
    total_kg = total_grams / 1000
    return total_kg

if __name__ == "__main__":
    import sys
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else "ORDER-21459074-2025-01-05.pdf"
    kg = extract_carrots_kg(pdf_path)
    print(f"Total KG of carrots purchased: {kg:.3f} kg")
