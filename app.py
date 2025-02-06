import pandas as pd
import streamlit as st
from io import BytesIO

# Function to filter data
def filter_data(df):
    df = df[df['Claim Status'] == 'R']
    return df

# Function to handle duplicates
def keep_last_duplicate(df):
    duplicate_claims = df[df.duplicated(subset='Claim No', keep=False)]
    if not duplicate_claims.empty:
        st.write("Duplicated ClaimNo values:")
        st.write(duplicate_claims[['Claim No']].drop_duplicates())
    df = df.drop_duplicates(subset='Claim No', keep='last')
    return df

# Main processing function
def move_to_template(df):
    # Step 1: Filter the data
    new_df = filter_data(df)

    # Step 2: Handle duplicates
    new_df = keep_last_duplicate(new_df)

    # Step 3: Convert date columns to datetime
    date_columns = ["Treatment Start", "Treatment Finish", "Date"]
    for col in date_columns:
        new_df[col] = pd.to_datetime(new_df[col], errors='coerce')
        if new_df[col].isnull().any():
            st.warning(f"Invalid date values detected in column '{col}'. Coerced to NaT.")
            
    if new_df['Product Type'] == "IP" and new_df['Room Option'] == "":
        new_df['Room Option'] == "Unknown"
    # Step 4: Transform to the new template
    df_transformed = pd.DataFrame({
        "No": range(1, len(new_df) + 1),
        "Policy No": new_df["Policy No"],
        "Client Name": new_df["Client Name"].str.upper(),
        "Claim No": new_df["Claim No"],
        "Member No": new_df["Member No"],
        "Emp ID": new_df["Emp ID"],
        "Emp Name": new_df["Emp Name"],
        "Patient Name": new_df["Patient Name"].str.upper(),
        "Membership": new_df["Membership"],
        "Product Type": new_df["Product Type"],
        "Claim Type": new_df["Claim Type"],
        "Room Option": new_df['Room Option'].str.replace(" ", "", regex=True).str.upper(),
        "Area": new_df["Area"],
        "Diagnosis": new_df["Primary Diagnosis"].str.upper(),
        "Treatment Place": new_df["Treatment Place"].str.upper(),
        "Treatment Start": new_df["Treatment Start"],
        "Treatment Finish": new_df["Treatment Finish"],
        "Date": new_df["Date"],
        "Tahun": new_df["Date"].dt.year,
        "Bulan": new_df["Date"].dt.month,
        "Sum of Billed": new_df["Billed"],
        "Sum of Accepted": new_df["Accepted"],
        "Sum of Excess Coy": new_df["Excess Coy"],
        "Sum of Excess Emp": new_df["Excess Emp"],
        "Sum of Excess Total": new_df["Excess Total"],
        "Sum of Unpaid": new_df["Unpaid"],
    })
    return df_transformed

# Save the processed data to Excel and return as BytesIO
def save_to_excel(df, filename):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Write the transformed data
        df.to_excel(writer, index=False, sheet_name='SC')
    output.seek(0)
    return output, filename

# Streamlit app
st.title("Claim Data Raw to Template")

# File uploader
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file, encoding='unicode_escape')
    
    # Process data
    st.write("Processing data...")
    transformed_data = move_to_template(df)
    
    # Show a preview of the transformed data
    st.write("Transformed Data Preview:")
    st.dataframe(transformed_data.head())

    # Compute summary statistics
    total_claims = len(transformed_data)
    total_billed = int(transformed_data["Sum of Billed"].sum())
    total_accepted = int(transformed_data["Sum of Accepted"].sum())
    total_excess = int(transformed_data["Sum of Excess Total"].sum())
    total_unpaid = int(transformed_data["Sum of Unpaid"].sum())

    st.write("Claim Summary:")
    st.write(f"- Total Claims: {total_claims:,}")
    st.write(f"- Total Billed: {total_billed:,.2f}")
    st.write(f"- Total Accepted: {total_accepted:,.2f}")
    st.write(f"- Total Excess: {total_excess:,.2f}")
    st.write(f"- Total Unpaid: {total_unpaid:,.2f}")

    # User input for filename
    filename = st.text_input("Enter the Excel file name (without extension):", "Transformed_Claim_Data")

    # Download link for the Excel file
    if filename:
        excel_file, final_filename = save_to_excel(transformed_data, filename=filename + ".xlsx")
        st.download_button(
            label="Download Excel File",
            data=excel_file,
            file_name=final_filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
