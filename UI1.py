import streamlit as st
import pdfplumber
import PyPDF2
import pandas as pd
from io import BytesIO

# Define a function for HDFC Bank processing
def process_hdfc_bank(pdf_file):
    extracted_text = ""
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            extracted_text += page.extract_text() + "\n"
    return extracted_text

def parse_hdfc_bank_text(raw_text):
    lines = raw_text.split("\n")
    return {
        "Date Of Receipt": lines[12].split()[-1],
        "Nature of Payment": lines[7].strip().replace("Nature of Payment ", ""),
        "Basic Tax": float(lines[9].replace("Basic Tax", "").strip().replace(",", "")),
        "Interest": float(lines[14].split()[1].replace(",", "")),
        "Penalty": float(lines[12].split()[1].replace(",", "")),
        "Fee Under Sec.234E": float(lines[15].split()[3].replace(",", "")),
        "TOTAL": float(lines[16].split("Drawn on")[0].replace("TOTAL", "").strip().replace(",", "")),
        "Drawn on": lines[16].split("Drawn on")[-1].strip(),
        "Payment Realisation Date": lines[19].split()[-1],
        "Challan No": int(lines[10].split()[-1].replace(",", "")),
        "Challan Serial No.": int(lines[13].split()[-1].replace(",", ""))
    }

# Define a function for Income Tax Department processing
def process_income_tax(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

def parse_income_tax_text(text):
    details = {}
    lines = text.split("\n")
    for line in lines:
        if "Nature of Payment" in line:
            details["Nature of Payment"] = line.split(":")[-1].strip()
        elif "Amount (in Rs.)" in line:
            details["Amount (in Rs.)"] = line.split(":")[-1].strip()
        elif "Challan No" in line:
            details["Challan No."] = line.split(":")[-1].strip()
        elif "Tender Date" in line:
            details["Tender Date"] = line.split(":")[-1].strip()
        elif line.startswith("DInterest"):
            details["Interest"] = line.split("₹")[-1].strip()
        elif line.startswith("EPenalty"):
            details["Penalty"] = line.split("₹")[-1].strip()
        elif line.startswith("FFee under section 234E"):
            details["Fee under Section 234E"] = line.split("₹")[-1].strip()
        elif line.startswith("Total (A+B+C+D+E+F)"):
            details["Total (A+B+C+D+E+F)"] = line.split("₹")[-1].strip()
    return details

# Save to Excel
def save_to_excel(data_frames):
    output = BytesIO()
    combined_df = pd.concat(data_frames, ignore_index=True)
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        combined_df.to_excel(writer, index=False, sheet_name="Extracted Data", float_format="%.2f")
    output.seek(0)
    return output

# Streamlit App
st.set_page_config(page_title="Challan Data Extraction Tool", layout="wide")
st.title("🧾 TDS Challan Data Extraction Tool")
st.markdown(
    """
    Welcome to the **Challan Data Extraction Tool**. 
    Effortlessly extract and analyze data from HDFC Bank and Income Tax Department PDF files. 
    Use the sidebar to configure your options and upload the files. 
    """
)

# Sidebar
st.sidebar.header("🔧 Configuration Panel")
option = st.sidebar.radio(
    "Choose Process Type",
    ["HDFC Bank", "Income Tax Department"],
    help="Select the type of PDF to process."
)
uploaded_files = st.sidebar.file_uploader(
    "Upload PDF Files", 
    type="pdf", 
    accept_multiple_files=True, 
    help="You can upload multiple PDF files."
)
submit = st.sidebar.button("🚀 Process Files")

# Main Area
if submit and uploaded_files:
    st.subheader("📂 Processing Files")
    progress = st.progress(0)
    extracted_data = []

    if option == "HDFC Bank":
        for idx, pdf_file in enumerate(uploaded_files):
            try:
                raw_text = process_hdfc_bank(pdf_file)
                parsed_data = parse_hdfc_bank_text(raw_text)
                df = pd.DataFrame([parsed_data])
                extracted_data.append(df)
                progress.progress((idx + 1) / len(uploaded_files))
            except Exception as e:
                st.error(f"Error processing {pdf_file.name}: {e}")

    elif option == "Income Tax Department":
        for idx, pdf_file in enumerate(uploaded_files):
            try:
                raw_text = process_income_tax(pdf_file)
                parsed_data = parse_income_tax_text(raw_text)
                df = pd.DataFrame([parsed_data])
                extracted_data.append(df)
                progress.progress((idx + 1) / len(uploaded_files))
            except Exception as e:
                st.error(f"Error processing {pdf_file.name}: {e}")

    if extracted_data:
        combined_df = pd.concat(extracted_data, ignore_index=True)
        st.subheader("🔍 Extracted Data")
        st.dataframe(combined_df)

        excel_data = save_to_excel([combined_df])
        st.download_button(
            label="📥 Download Extracted Data as Excel",
            data=excel_data,
            file_name="extracted_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        st.success("🎉 Processing completed successfully!")
    else:
        st.error("❌ No valid data could be extracted!")
else:
    st.info("📂 Please upload files and click 'Process Files' to start.")
