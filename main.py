from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Law Depository Backend is running 🚀"}

@app.get("/laws")
def get_laws():
    # Temporary demo data until scraper is fully connected
    demo_data = [
        {"title": "Insolvency and Bankruptcy Code, 2016", "link": "https://ibbi.gov.in"},
        {"title": "Companies (Amendment) Act, 2020", "link": "https://www.mca.gov.in"},
        {"title": "Competition Act, 2002", "link": "https://cci.gov.in"}
    ]
    return {"laws": demo_data}
