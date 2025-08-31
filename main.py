from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# ✅ Allow frontend (GitHub Pages) to call backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Law Depository Backend is running 🚀"}

@app.get("/law/ibc")
def get_ibc():
    return {
        "law": "Insolvency and Bankruptcy Code, 2016",
        "categories": {
            "Act": [
                {"title": "IBC, 2016 (Bare Act)", "link": "https://ibbi.gov.in/uploads/legalframwork/IBC_2016.pdf"}
            ],
            "Rules": [
                {"title": "Insolvency and Bankruptcy (Application to Adjudicating Authority) Rules, 2016", "link": "https://ibbi.gov.in/uploads/legalframwork/IBBI_Adjudication_Rules.pdf"}
            ],
            "Regulations": [
                {"title": "IBBI (CIRP) Regulations, 2016", "link": "https://ibbi.gov.in/uploads/legalframwork/2016-05-05_cirp_regulations.pdf"}
            ],
            "Notifications": [
                {"title": "MCA Notification – Sections of IBC Enforcement", "link": "https://www.egazette.nic.in/WriteReadData/2016/ibc_notification.pdf"}
            ],
            "Amendments": [
                {"title": "IBC (Amendment) Ordinance, 2021", "link": "https://ibbi.gov.in/uploads/legalframwork/ibc_amendment_ord2021.pdf"}
            ],
            "Reports": [
                {"title": "BLRC Committee Report on Bankruptcy Law Reforms", "link": "https://ibbi.gov.in/uploads/resources/BLRCReportVol1_04112015.pdf"}
            ],
            "Bills": [
                {"title": "IBC (Amendment) Bill, 2021", "link": "https://prsindia.org/files/bills_acts/bills_parliament/IBC_Amendment_Bill_2021.pdf"}
            ]
        }
    }

@app.get("/law/competition")
def get_competition():
    return {
        "law": "Competition Act, 2002",
        "categories": {
            "Act": [
                {"title": "Competition Act, 2002 (Bare Act)", "link": "https://www.cci.gov.in/sites/default/files/cci_pdf/competitionact2012.pdf"}
            ],
            "Rules": [
                {"title": "Competition Commission of India (Procedure) Rules, 2009", "link": "https://www.cci.gov.in/sites/default/files/cci_pdf/competitionrules2009.pdf"}
            ],
            "Regulations": [
                {"title": "CCI (General) Regulations, 2009", "link": "https://www.cci.gov.in/sites/default/files/cci_pdf/generalregulations2009.pdf"}
            ],
            "Notifications": [
                {"title": "CCI Notification on Merger Guidelines", "link": "https://www.cci.gov.in/sites/default/files/whats_newdocument/Notification.pdf"}
            ],
            "Amendments": [
                {"title": "Competition (Amendment) Act, 2023", "link": "https://www.egazette.nic.in/WriteReadData/2023/comp_amendment.pdf"}
            ],
            "Reports": [
                {"title": "High Level Committee Report on Competition Policy", "link": "https://www.cci.gov.in/sites/default/files/whats_newdocument/Report.pdf"}
            ],
            "Bills": [
                {"title": "Competition (Amendment) Bill, 2022", "link": "https://prsindia.org/files/bills_acts/bills_parliament/Competition%20Amendment%20Bill%202022.pdf"}
            ]
        }
    }
