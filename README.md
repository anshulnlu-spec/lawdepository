# 📖 Law Depository – PDF Registry Model

## 🔹 What is this?
This project is a **centralised law depository** for Indian legislation.  
Instead of scraping whole government websites, it works on a **PDF registry model**:  

- You manually add working **PDF links** (from Gazette, IBBI, MCA, Sansad, etc.)  
- The backend automatically:  
  - Extracts **title + date** from each PDF (OCR fallback for scanned ones).  
  - Categorises into **Act, Rules, Regulations, Notifications, Reports, Circulars, Treatises**.  
- The frontend displays clean tables for each law.

---

## 🔹 Project Structure
```
lawdepository/
 ├── main.py          # FastAPI backend – serves /law/{lawname}
 ├── utils.py         # PDF title/date extraction + categorisation
 ├── ibc.json         # Example registry for IBC (list of PDF links)
 ├── index.html       # Homepage
 ├── ibc.html         # IBC repository page
 ├── style.css        # Styling
 ├── script.js        # Frontend logic
 ├── requirements.txt # Python dependencies
 ├── apt.txt          # System dependencies (OCR support)
 └── render.yaml      # Render deployment config
```

---

## 🔹 How to Add New Laws
1. Create a new JSON file, e.g. `competition.json`.  
2. Add PDF links in this format:
   ```json
   {
     "pdfs": [
       "https://egazette.nic.in/WriteReadData/2021/12345.pdf",
       "https://ibbi.gov.in/uploads/legalframework/2022-notification.pdf"
     ]
   }
   ```
3. Commit the file to GitHub.  
4. The backend will automatically serve it at:
   ```
   /law/competition
   ```

---

## 🔹 Running Backend (Render)
1. Connect this repo to **Render**.  
2. Deploy as a **Web Service** with:  
   - Start Command:  
     ```
     uvicorn main:app --host 0.0.0.0 --port 10000
     ```  
   - Add **apt.txt** and **requirements.txt** (Render installs automatically).  
3. Once deployed, you’ll have endpoints like:  
   - `https://your-service.onrender.com/` → health check.  
   - `https://your-service.onrender.com/law/ibc` → JSON for IBC law.  

---

## 🔹 Frontend (GitHub Pages)
1. Commit the frontend files (`index.html`, `ibc.html`, etc.) to the repo.  
2. Enable **GitHub Pages** in repo settings (branch = `main`, folder = `/root`).  
3. Visit:  
   ```
   https://<your-username>.github.io/lawdepository/
   ```

---

## 🔹 Example Output
Visiting `/law/ibc` may return:
```json
{
  "law": "IBC",
  "categories": {
    "Act": [
      {
        "title": "Insolvency and Bankruptcy Code, 2016 (amended upto 12.08.2021)",
        "date": "12 Aug 2021",
        "link": "https://ibbi.gov.in/...pdf",
        "source": "IBC"
      }
    ]
  }
}
```

---

## ✅ Benefits
- 🚀 Fast – only processes PDFs you add.  
- 🎯 Accurate – no wrong documents.  
- 🔒 Stable – no scraping fragile government websites.  
- 📂 Modular – add laws one by one (`xyz.json`).  

---

👉 Recommended workflow: **Delete old `scraper_*.py` files**, keep only the Phase-3 registry files.  
