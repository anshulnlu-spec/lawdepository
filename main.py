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
                {"title": "IBC, 2016 (Bare Act)", "link": "https://www.indiacode.nic.in/bitstream/123456789/2159/1/A2016-31.pdf"}
            ],
            "Rules": [
                {"title": "IBC (Application to Adjudicating Authority) Rules, 2016", "link": "https://ibbi.gov.in/uploads/legalframwork/2016-11-15_adjudicating_authority_rules.pdf"},
                {"title": "IBC (Cross Border Insolvency) Rules, 2020 (Draft)", "link": "https://ibbi.gov.in/uploads/whatsnew/2020-06-20_cross_border_insolvency_rules.pdf"}
            ],
            "Regulations": [
                {"title": "IBBI (CIRP) Regulations, 2016", "link": "https://ibbi.gov.in/uploads/legalframwork/2016-05-05_cirp_regulations.pdf"},
                {"title": "IBBI (Liquidation Process) Regulations, 2016", "link": "https://ibbi.gov.in/uploads/legalframwork/2016-12-15_liquidation_regulations.pdf"}
            ],
            "Notifications": [
                {"title": "MCA Notification – Enforcement of IBC Sections", "link": "https://egazette.nic.in/WriteReadData/2016/ibc_notification.pdf"}
            ],
            "Amendments": [
                {"title": "IBC (Amendment) Ordinance, 2021", "link": "https://ibbi.gov.in/uploads/legalframwork/ibc_amendment_ord2021.pdf"},
                {"title": "IBC (Amendment) Act, 2021", "link": "https://www.indiacode.nic.in/bitstream/123456789/16242/1/A2021-26.pdf"}
            ],
            "Bills": [
                {"title": "IBC (Amendment) Bill, 2021", "link": "http://164.100.47.4/BillsTexts/LSBillTexts/Asintroduced/123_2021_LS_Eng.pdf"}
            ],
            "Reports": [
                {"title": "BLRC Committee Report (2015)", "link": "https://ibbi.gov.in/uploads/resources/BLRCReportVol1_04112015.pdf"},
                {"title": "Standing Committee on Finance Report (2021)", "link": "http://164.100.47.193/lsscommittee/Finance/17_Finance_30.pdf"}
            ]
        }
    }
