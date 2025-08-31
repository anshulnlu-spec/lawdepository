async function loadDocs() {
  const res = await fetch("https://lawdepository-backend.onrender.com/law/ibc");
  const data = await res.json();
  const container = document.getElementById("docs");
  container.innerHTML = "";
  data.docs.forEach(doc => {
    const div = document.createElement("div");
    div.innerHTML = `<h3>${doc.title}</h3><p>${doc.date || ""}</p><p>${doc.category || ""}</p><a href="${doc.url}" target="_blank">Open PDF</a>`;
    container.appendChild(div);
  });
}
loadDocs();
