async function loadData() {
  try {
    const response = await fetch("https://lawdepository-backend.onrender.com/law/ibc");
    if (!response.ok) throw new Error("Network error");
    const data = await response.json();
    const categories = data.categories;
    let content = "";
    for (let cat in categories) {
      if (categories[cat].length > 0) {
        content += `<details><summary>${cat}</summary>`;
        content += "<table><tr><th>Title</th><th>Date</th><th>PDF Link</th></tr>";
        categories[cat].forEach(item => {
          content += `<tr><td>${item.title}</td><td>${item.date || ""}</td><td><a href='${item.link}' target='_blank' onclick='registerClick("${item.link}")'>Download PDF</a></td></tr>`;
        });
        content += "</table></details>";
      }
    }
    document.getElementById("content").innerHTML = content;
  } catch (err) {
    document.getElementById("content").innerHTML = "<p style='color:red;'>Failed to load data. Please try again later.</p>";
  }
}

async function registerClick(link) {
  try {
    await fetch("https://lawdepository-backend.onrender.com/click", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ link: link })
    });
  } catch (err) {
    console.error("Failed to register click", err);
  }
}

window.onload = loadData;
