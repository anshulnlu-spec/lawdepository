// This code runs as soon as the HTML page has finished loading.
document.addEventListener("DOMContentLoaded", () => {
    // Set the "last updated" date in the footer to today.
    document.getElementById('last-updated').textContent = new Date().toLocaleDateString('en-GB', {
        day: 'numeric', month: 'long', year: 'numeric'
    });
    // Start the main process of fetching and displaying the documents.
    fetchAndDisplayData();
});

// This is the main data for the entire application, stored globally.
let allData = {};

/**
 * Fetches the entire dataset from the backend API.
 * This is the first step to loading the website.
 */
async function fetchAndDisplayData() {
    const loadingMessage = document.getElementById('loading-message');
    const repoContainer = document.getElementById('repo-container');
    const apiUrl = '/api/documents'; // The endpoint on our backend server

    try {
        const response = await fetch(apiUrl);
        if (!response.ok) {
            throw new Error(`Network response was not ok (status: ${response.status})`);
        }
        
        const data = await response.json();
        allData = data.topics || {}; // Store the fetched data globally
        
        loadingMessage.style.display = 'none'; // Hide the loading spinner
        
        const topics = Object.keys(allData);
        if (topics.length === 0) {
            repoContainer.innerHTML = '<p>No documents currently in the repository. The AI researcher runs daily to find new content.</p>';
            return;
        }

        // Create the navigation tabs for each law (e.g., "Companies Act")
        createTopicTabs(topics);
        // Display the documents for the very first topic in the list by default.
        displayDocumentsForTopic(topics[0]);

    } catch (error) {
        console.error('Failed to fetch documents:', error);
        loadingMessage.innerHTML = `<p>❌ Failed to load the repository. Please try refreshing the page.</p>`;
    }
}

/**
 * Creates the navigation tabs at the top of the page.
 * @param {string[]} topics - An array of topic names, e.g., ["Companies Act", "RERA"].
 */
function createTopicTabs(topics) {
    const tabsContainer = document.getElementById('topic-tabs');
    tabsContainer.innerHTML = ''; // Clear any existing tabs

    topics.forEach((topic, index) => {
        const tab = document.createElement('button');
        tab.className = 'topic-tab';
        tab.textContent = topic;
        // Make the first tab active by default.
        if (index === 0) {
            tab.classList.add('active');
        }
        // When a tab is clicked, show the documents for that topic.
        tab.onclick = () => {
            // Update the active state for the tabs
            document.querySelectorAll('.topic-tab').forEach(t => t.classList.remove('active'));
            tab.classList.add('active');
            displayDocumentsForTopic(topic);
        };
        tabsContainer.appendChild(tab);
    });
}

/**
 * Clears the main content area and displays all documents for a selected topic.
 * @param {string} topic - The name of the law to display, e.g., "Companies Act".
 */
function displayDocumentsForTopic(topic) {
    const repoContainer = document.getElementById('repo-container');
    repoContainer.innerHTML = ''; // Clear the current view

    const jurisdictions = allData[topic];
    if (!jurisdictions || Object.keys(jurisdictions).length === 0) {
        repoContainer.innerHTML = `<p>No documents found for the topic: ${topic}.</p>`;
        return;
    }

    // Display documents in a specific order: India, US, UK
    const displayOrder = ["India", "United States", "United Kingdom"];
    const sortedJurisdictions = Object.keys(jurisdictions).sort((a, b) => {
        return displayOrder.indexOf(a) - displayOrder.indexOf(b);
    });

    for (const jurisdiction of sortedJurisdictions) {
        const categories = jurisdictions[jurisdiction];
        if (Object.keys(categories).length > 0) {
            repoContainer.appendChild(createJurisdictionSection(jurisdiction, categories));
        }
    }
}

/**
 * Creates a major section for a country (e.g., "India").
 * @param {string} jurisdiction - The name of the country.
 * @param {object} categories - An object containing document categories and lists of documents.
 */
function createJurisdictionSection(jurisdiction, categories) {
    const section = document.createElement('section');
    section.className = 'jurisdiction-section';

    const title = document.createElement('h2');
    title.className = 'jurisdiction-title';
    title.textContent = jurisdiction;
    section.appendChild(title);

    // Loop through each category (e.g., "Legislation", "Case Law")
    for (const category in categories) {
        const docs = categories[category];
        if (docs.length > 0) {
            const categoryTitle = document.createElement('h3');
            categoryTitle.className = 'category-title';
            categoryTitle.textContent = category;
            section.appendChild(categoryTitle);

            // Sort documents by date, newest first.
            docs.sort((a, b) => new Date(b.date) - new Date(a.date));
            // Create a card for each document.
            for (const doc of docs) {
                section.appendChild(createDocumentCard(doc));
            }
        }
    }
    return section;
}

/**
 * Creates a single, professional-looking "card" for one document.
 * @param {object} doc - An object with the document's details (title, date, etc.).
 */
function createDocumentCard(doc) {
    const card = document.createElement('div');
    card.className = 'document-card';

    // Determine if the document is a PDF or a webpage for the tag.
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

    // Find the link we just created and add a click tracker to it.
    const link = card.querySelector('.doc-link');
    link.addEventListener('click', () => {
        trackClick(doc.url);
    });

    return card;
}

/**
 * Sends a signal to the backend to record that a user clicked on a specific link.
 * @param {string} url - The URL of the document that was clicked.
 */
function trackClick(url) {
    fetch('/api/track_click', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: url }),
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            console.log('Successfully tracked click for:', url);
        }
    })
    .catch(error => {
        console.error('Error tracking click:', error);
    });
}

