async function loadData() {
  try {
    const resp = await fetch("https://lawdepository-backend.onrender.com/law/ibc");
    if (!resp.ok) {
      throw new Error("HTTP error " + resp.status);
    }
    const data = await resp.json();
    let html = "";
    for (let cat in data.categories) {
      html += `<h2>${cat}</h2><ul>`;
      data.categories[cat].forEach(doc => {
        html += `<li>${doc.title} (${doc.date || ""}) - <a href="${doc.link}" target="_blank">PDF</a></li>`;
      });
      html += "</ul>";
    }
    document.getElementById("content").innerHTML = html;
  } catch (err) {
    document.getElementById("content").innerHTML = "⚠️ Error loading data: " + err;
    console.error(err);
  }
}
window.onload = loadData;
