#!/bin/bash
pip install --upgrade pipS
pip install streamlit pandas gspread oauth2client matplotlib seaborn scikit-learn streamlit-calendar

# Run the Streamlit app
streamlit run app.py
