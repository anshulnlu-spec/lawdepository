document.addEventListener("DOMContentLoaded", () => {
    fetchDocuments();
    document.getElementById('last-updated').textContent = new Date().toLocaleDateString('en-GB', {
        day: 'numeric', month: 'long', year: 'numeric'
    });
});

async function fetchDocuments() {
    const container = document.getElementById('repo-container');
    const loadingMessage = document.getElementById('loading-message');
    const apiUrl = '/api/documents';

    try {
        const response = await fetch(apiUrl);
        if (!response.ok) throw new Error(`Network response was not ok (status: ${response.status})`);
        
        const data = await response.json();
        
        loadingMessage.style.display = 'none';
        
        const jurisdictions = Object.keys(data);
        if (jurisdictions.every(j => Object.keys(data[j]).length === 0)) {
            container.innerHTML = '<p>No documents currently in the repository. The curator runs the AI researcher periodically to find new content.</p>';
            return;
        }

        const displayOrder = ["India", "United States", "United Kingdom"];
        const sortedJurisdictions = jurisdictions.sort((a, b) => {
            return displayOrder.indexOf(a) - displayOrder.indexOf(b);
        });

        for (const jurisdiction of sortedJurisdictions) {
            const categories = data[jurisdiction];
            if (Object.keys(categories).length > 0) {
                container.appendChild(createJurisdictionSection(jurisdiction, categories));
            }
        }

    } catch (error) {
        console.error('Failed to fetch documents:', error);
        loadingMessage.innerHTML = `<p>❌ Failed to load the repository. Please try refreshing the page.</p>`;
    }
}

function createJurisdictionSection(jurisdiction, categories) {
    const section = document.createElement('section');
    section.className = 'jurisdiction-section';

    const title = document.createElement('h2');
    title.className = 'jurisdiction-title';
    title.textContent = jurisdiction;
    section.appendChild(title);

    for (const category in categories) {
        const docs = categories[category];
        if (docs.length > 0) {
            const categoryTitle = document.createElement('h3');
            categoryTitle.className = 'category-title';
            categoryTitle.textContent = category;
            section.appendChild(categoryTitle);

            docs.sort((a, b) => new Date(b.date) - new Date(a.date));
            for (const doc of docs) {
                section.appendChild(createDocumentCard(doc));
            }
        }
    }
    return section;
}

function createDocumentCard(doc) {
    const card = document.createElement('div');
    card.className = 'document-card';

    const docType = doc.content_type.includes('pdf') ? 'PDF' : 'HTML';

    card.innerHTML = `
        <div class="doc-header">
            <h4 class="doc-title">${doc.title || 'Title not available'}</h4>
            <div class="doc-meta">
                <span class="doc-type">${docType}</span>
                <span class="doc-date">${doc.date || 'N/A'}</span>
            </div>
        </div>
        <p class="doc-summary">${doc.summary || 'Summary not available.'}</p>
        <a href="${doc.url}" class="doc-link" target="_blank" rel="noopener noreferrer">View Source</a>
    `;
    return card;
}
