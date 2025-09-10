// This script runs when the webpage is fully loaded.
document.addEventListener("DOMContentLoaded", () => {
    // Set the "last updated" date in the footer.
    document.getElementById('last-updated').textContent = new Date().toLocaleDateString('en-GB', {
        day: 'numeric', month: 'long', year: 'numeric'
    });

    // Start the process of initializing the application.
    initializeApp();
});

// This is the main function that sets up the page.
async function initializeApp() {
    const tabsContainer = document.getElementById('topic-tabs');
    const loadingMessage = document.getElementById('loading-message');
    const repoContainer = document.getElementById('repo-container');

    try {
        // Fetch the list of available legal topics from our API.
        const topicsResponse = await fetch('/api/topics');
        if (!topicsResponse.ok) throw new Error('Failed to fetch topics.');
        
        const topics = await topicsResponse.json();

        // If there are no topics, show a message and stop.
        if (!topics || topics.length === 0) {
            loadingMessage.textContent = 'No legislation topics are configured.';
            return;
        }

        // Create the navigation tabs for each topic.
        tabsContainer.innerHTML = '';
        topics.forEach((topic, index) => {
            const tab = document.createElement('button');
            tab.className = 'topic-tab';
            tab.textContent = topic;
            tab.onclick = () => fetchAndDisplayDocuments(topic);
            tabsContainer.appendChild(tab);

            // Make the first tab active by default.
            if (index === 0) {
                tab.classList.add('active');
            }
        });

        // Fetch the documents for the first topic automatically.
        fetchAndDisplayDocuments(topics[0]);

        // Set up event listeners for search and sort controls.
        document.getElementById('search-bar').addEventListener('input', filterDocuments);
        document.getElementById('sort-order').addEventListener('change', () => fetchAndDisplayDocuments(document.querySelector('.topic-tab.active').textContent));

    } catch (error) {
        console.error('Initialization failed:', error);
        loadingMessage.innerHTML = `<p>❌ Failed to initialize the application. Please try refreshing the page.</p>`;
        repoContainer.style.display = 'none';
    }
}

// This function fetches and then displays documents for a given topic.
async function fetchAndDisplayDocuments(topic) {
    const container = document.getElementById('repo-container');
    const loadingMessage = document.getElementById('loading-message');
    const tabs = document.querySelectorAll('.topic-tab');

    loadingMessage.style.display = 'block';
    container.innerHTML = ''; // Clear old content immediately
    
    // Update which tab is visually marked as "active".
    tabs.forEach(tab => tab.classList.toggle('active', tab.textContent === topic));

    try {
        const apiUrl = `/api/documents/${encodeURIComponent(topic)}`;
        const response = await fetch(apiUrl);
        if (!response.ok) throw new Error(`Network response was not ok (status: ${response.status})`);
        
        const data = await response.json();
        
        loadingMessage.style.display = 'none';
        
        const jurisdictions = Object.keys(data);
        if (jurisdictions.every(j => Object.keys(data[j]).length === 0)) {
            container.innerHTML = `<p>No documents currently in the repository for "${topic}".</p>`;
            return;
        }

        const displayOrder = ["India", "United States", "United Kingdom"];
        const sortedJurisdictions = jurisdictions.sort((a, b) => displayOrder.indexOf(a) - displayOrder.indexOf(b));

        for (const jurisdiction of sortedJurisdictions) {
            const categories = data[jurisdiction];
            if (Object.keys(categories).length > 0) {
                container.appendChild(createJurisdictionSection(jurisdiction, categories));
            }
        }
        // Apply search filter to the newly rendered documents
        filterDocuments();

    } catch (error) {
        console.error(`Failed to fetch documents for topic "${topic}":`, error);
        loadingMessage.innerHTML = `<p>❌ Failed to load documents for "${topic}". Please try another topic.</p>`;
    }
}

// Helper function to create a whole section for a country (e.g., "India").
function createJurisdictionSection(jurisdiction, categories) {
    const section = document.createElement('section');
    section.className = 'jurisdiction-section';

    const title = document.createElement('h2');
    title.className = 'jurisdiction-title';
    title.textContent = jurisdiction;
    section.appendChild(title);

    const sortedCategories = Object.keys(categories).sort();

    for (const category of sortedCategories) {
        let docs = categories[category];
        if (docs.length > 0) {
            const categoryTitle = document.createElement('h3');
            categoryTitle.className = 'category-title';
            categoryTitle.textContent = category;
            section.appendChild(categoryTitle);
            
            // Sort documents by date based on the dropdown selection.
            const sortOrder = document.getElementById('sort-order').value;
            docs.sort((a, b) => {
                const dateA = new Date(a.date);
                const dateB = new Date(b.date);
                return sortOrder === 'newest' ? dateB - dateA : dateA - dateB;
            });

            for (const doc of docs) {
                section.appendChild(createDocumentCard(doc));
            }
        }
    }
    return section;
}

// Helper function to create a single "card" for a document.
function createDocumentCard(doc) {
    const card = document.createElement('div');
    card.className = 'document-card';

    const docType = doc.content_type && doc.content_type.includes('pdf') ? 'PDF' : 'HTML';
    const formattedDate = doc.date ? new Date(doc.date).toLocaleDateString('en-GB', { year: 'numeric', month: 'long', day: 'numeric' }) : 'N/A';

    card.innerHTML = `
        <div class="doc-header">
            <h4 class="doc-title">${doc.title || 'Title not available'}</h4>
            <div class="doc-meta">
                <span class="doc-type">${docType}</span>
                <span class="doc-date">${formattedDate}</span>
            </div>
        </div>
        <p class="doc-summary">${doc.summary || 'Summary not available.'}</p>
        <a href="${doc.url}" class="doc-link" target="_blank" rel="noopener noreferrer">View Source</a>
    `;
    return card;
}

// NEW FUNCTION: Filters documents based on the search bar input.
function filterDocuments() {
    const searchTerm = document.getElementById('search-bar').value.toLowerCase();
    const allCards = document.querySelectorAll('.document-card');

    allCards.forEach(card => {
        const title = card.querySelector('.doc-title')?.textContent.toLowerCase() || '';
        const summary = card.querySelector('.doc-summary')?.textContent.toLowerCase() || '';
        const isVisible = title.includes(searchTerm) || summary.includes(searchTerm);
        card.classList.toggle('hidden', !isVisible);
    });
}
