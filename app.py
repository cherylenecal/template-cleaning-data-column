import pandas as pd
import streamlit as st
from io import BytesIO

# Function to filter data
def filter_data(df):
    df = df[df['ClaimStatus'] == 'R']
    return df

# Function to handle duplicates
def keep_last_duplicate(df):
    duplicate_claims = df[df.duplicated(subset='ClaimNo', keep=False)]
    if not duplicate_claims.empty:
        st.write("Duplicated ClaimNo values:")
        st.write(duplicate_claims[['ClaimNo']].drop_duplicates())
    df = df.drop_duplicates(subset='ClaimNo', keep='last')
    return df

# Main processing function
def move_to_template(df):
    # Step 1: Filter the data
    new_df = filter_data(df)

    # Step 2: Handle duplicates
    new_df = keep_last_duplicate(new_df)

    # Step 3: Convert date columns to datetime
    date_columns = ["TreatmentStart", "TreatmentFinish"]
    for col in date_columns:
        new_df[col] = pd.to_datetime(new_df[col], format='mixed')
        if new_df[col].isnull().any():
            st.warning(f"Invalid date values detected in column '{col}'")    
    new_df["Date"] = pd.to_datetime(new_df["Date"], format="%d/%m/%Y", dayfirst=True)
    
    # Step 4: Transform to the new template
    df_transformed = pd.DataFrame({
        "No": range(1, len(new_df) + 1),
        "PolicyNo": new_df["PolicyNo"],
        "ClientName": new_df["ClientName"].str.upper(),
        "ClaimNo": new_df["ClaimNo"],
        "MemberNo": new_df["MemberNo"],
        "EmpID": new_df["EmpID"],
        "EmpName": new_df["EmpName"],
        "PatientName": new_df["PatientName"].str.upper(),
        "Membership": new_df["Membership"],
        "ProductType": new_df["ProductType"],
        "ClaimType": new_df["ClaimType"],
        "RoomOption": new_df['RoomOption'].str.replace(" ", "", regex=True).str.upper(),
        "Area": new_df["Area"],
        "Diagnosis": new_df["PrimaryDiagnosis"],
        "Primary Diagnosis": new_df["PrimaryDiagnosis"],
        "Secondary Diagnosis": new_df["SecondaryDiagnosis"],
        "Plan": new_df["PPlan"],
        "Classification": new_df["Classification"],
        "Treatment Place": new_df["TreatmentPlace"].str.upper(),
        "Treatment Start": new_df["TreatmentStart"],
        "Treatment Finish": new_df["TreatmentFinish"],
        "Date": new_df["Date"],
        "Tahun": new_df["Date"].dt.year,
        "Bulan": new_df["Date"].dt.month,
        "Sum of Claim": new_df["ClaimPaidNoteAmount"],
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
