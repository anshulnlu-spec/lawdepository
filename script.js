
async function loadData() {
  const resp = await fetch("/law/ibc");
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
}
window.onload = loadData;
