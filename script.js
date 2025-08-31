async function loadLaw(law) {
  try {
    const res = await fetch(`https://lawdepository-backend.onrender.com/law/${law}`);
    const data = await res.json();
    const container = document.getElementById("content");
    container.innerHTML = "";

    const grouped = {};
    data.documents.forEach(doc => {
      if (!grouped[doc.category]) grouped[doc.category] = [];
      grouped[doc.category].push(doc);
    });

    for (let cat in grouped) {
      const section = document.createElement("div");
      section.innerHTML = `<div class='category'>${cat}</div>`;
      grouped[cat].forEach(doc => {
        const card = document.createElement("div");
        card.className = "card";
        card.innerHTML = `<b>${doc.title}</b><br>Date: ${doc.date || "N/A"}<br><a href='${doc.link}' target='_blank'>Open PDF</a>`;
        section.appendChild(card);
      });
      container.appendChild(section);
    }
  } catch (err) {
    document.getElementById("content").innerHTML = "⚠️ Error loading data: " + err;
  }
}

document.getElementById("searchBox").addEventListener("input", function() {
  const query = this.value.toLowerCase();
  document.querySelectorAll(".card").forEach(card => {
    card.style.display = card.innerText.toLowerCase().includes(query) ? "" : "none";
  });
});
