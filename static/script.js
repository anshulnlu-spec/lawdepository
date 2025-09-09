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
        // Step 1: Fetch the list of available legal topics from our new API endpoint.
        const topicsResponse = await fetch('/api/topics');
        if (!topicsResponse.ok) throw new Error('Failed to fetch topics.');
        
        const topics = await topicsResponse.json();

        // If there are no topics, show a message and stop.
        if (!topics || topics.length === 0) {
            loadingMessage.textContent = 'No legislation topics are configured for the depository.';
            return;
        }

        // Step 2: Create the navigation tabs for each topic.
        tabsContainer.innerHTML = ''; // Clear any existing tabs.
        topics.forEach((topic, index) => {
            const tab = document.createElement('button');
            tab.className = 'topic-tab';
            tab.textContent = topic;
            // When a tab is clicked, fetch documents for that topic.
            tab.onclick = () => fetchDocuments(topic);
            tabsContainer.appendChild(tab);

            // Make the first tab active by default.
            if (index === 0) {
                tab.classList.add('active');
            }
        });

        // Step 3: Fetch the documents for the first topic automatically.
        fetchDocuments(topics[0]);

    } catch (error) {
        console.error('Initialization failed:', error);
        loadingMessage.innerHTML = `<p>❌ Failed to initialize the application. Please try refreshing the page.</p>`;
        repoContainer.style.display = 'none';
    }
}

// This function fetches and displays documents for a given topic.
async function fetchDocuments(topic) {
    const container = document.getElementById('repo-container');
    const loadingMessage = document.getElementById('loading-message');
    const tabs = document.querySelectorAll('.topic-tab');

    // Show loading spinner and hide old content while we fetch new data.
    loadingMessage.style.display = 'block';
    container.style.display = 'none';

    // Update which tab is visually marked as "active".
    tabs.forEach(tab => {
        if (tab.textContent === topic) {
            tab.classList.add('active');
        } else {
            tab.classList.remove('active');
        }
    });

    try {
        // Use the new, topic-specific API endpoint. We encode the topic to handle special characters.
        const apiUrl = `/api/documents/${encodeURIComponent(topic)}`;
        const response = await fetch(apiUrl);
        if (!response.ok) throw new Error(`Network response was not ok (status: ${response.status})`);
        
        const data = await response.json();
        
        // Hide the loading message and show the container for the new content.
        loadingMessage.style.display = 'none';
        container.innerHTML = ''; // Clear out old document cards.
        container.style.display = 'block';
        
        const jurisdictions = Object.keys(data);
        // Check if all jurisdictions for this topic are empty.
        if (jurisdictions.every(j => Object.keys(data[j]).length === 0)) {
            container.innerHTML = `<p>No documents currently in the repository for "${topic}". The AI researcher runs periodically to find new content.</p>`;
            return;
        }

        // Display the documents, sorted by a preferred order of jurisdictions.
        const displayOrder = ["India", "United States", "United Kingdom"];
        const sortedJurisdictions = jurisdictions.sort((a, b) => displayOrder.indexOf(a) - displayOrder.indexOf(b));

        for (const jurisdiction of sortedJurisdictions) {
            const categories = data[jurisdiction];
            if (Object.keys(categories).length > 0) {
                container.appendChild(createJurisdictionSection(jurisdiction, categories));
            }
        }

    } catch (error) {
        console.error(`Failed to fetch documents for topic "${topic}":`, error);
        loadingMessage.innerHTML = `<p>❌ Failed to load the repository for "${topic}". Please try refreshing the page or selecting another topic.</p>`;
        loadingMessage.style.display = 'block';
        container.style.display = 'none';
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

    // Sort categories alphabetically for consistent order.
    const sortedCategories = Object.keys(categories).sort();

    for (const category of sortedCategories) {
        const docs = categories[category];
        if (docs.length > 0) {
            const categoryTitle = document.createElement('h3');
            categoryTitle.className = 'category-title';
            categoryTitle.textContent = category;
            section.appendChild(categoryTitle);

            // Sort documents by date, with the newest first.
            docs.sort((a, b) => new Date(b.date) - new Date(a.date));
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

    // Determine the document type label (PDF or HTML).
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

