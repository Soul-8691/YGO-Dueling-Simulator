// Data injected by Flask
const mainDeck = [], extraDeck = [], sideDeck = [];

let currentPage = 1;
let filteredCards = goatCards;

// Responsive max cards per page (2 rows)
function getCardsPerPage() {
    const width = window.innerWidth;
    if (width < 576) return 4;   // 2 cols × 2 rows
    if (width < 768) return 6;   // 3 cols × 2 rows
    if (width < 992) return 8;   // 4 cols × 2 rows
    return 12;                    // 6 cols × 2 rows
}

let cardsPerPage = getCardsPerPage();
window.addEventListener("resize", () => {
    cardsPerPage = getCardsPerPage();
    renderCardPool();
});

const cardList = document.getElementById("card-list");

// -------------------- Render Card Pool --------------------
function renderCardPool() {
    cardList.innerHTML = "";
    const start = (currentPage - 1) * cardsPerPage;
    const end = start + cardsPerPage;
    const pageCards = filteredCards.slice(start, end);

    pageCards.forEach(card => {
        const col = document.createElement("div");
        col.className = "col-6 col-sm-4 col-md-3 col-lg-2";

        const imgSrc = (card.local_images && card.local_images.length > 0)
            ? card.local_images[0]
            : "/static/images/placeholder.jpg";

        col.innerHTML = `
            <div class="card bg-dark text-white h-100 shadow-sm" style="cursor:pointer;">
                <img src="${imgSrc}" class="card-img-top" alt="${card.name}">
                <div class="card-body p-2 text-center">
                    <small>${card.name}</small>
                </div>
            </div>
        `;
        col.onclick = () => addCardToDeck(card.name, card.type || "");
        cardList.appendChild(col);
    });

    document.getElementById("page-info").innerText =
        `Page ${currentPage} of ${Math.ceil(filteredCards.length / cardsPerPage)}`;
}

// -------------------- Add Card to Deck --------------------
function addCardToDeck(name, type) {
    const target = document.querySelector('input[name="deck-target"]:checked').value;

    const countCopies = deck => deck.filter(c => c === name).length;

    if (type.includes("Fusion")) {
        if (extraDeck.length < 15 && countCopies(extraDeck) < 3) extraDeck.push(name);
    } else if (target === "main") {
        if (mainDeck.length < 60 && countCopies(mainDeck) < 3) mainDeck.push(name);
    } else if (target === "side") {
        if (sideDeck.length < 15 && countCopies(sideDeck) < 3) sideDeck.push(name);
    }

    updateDeckDisplay();
}

// -------------------- Update Deck Display --------------------
function updateDeckDisplay() {
    renderDeck("main-deck", mainDeck, true);
    renderDeck("extra-deck", extraDeck, false);
    renderDeck("side-deck", sideDeck, false);

    document.getElementById("main-count").innerText = mainDeck.length;
    document.getElementById("extra-count").innerText = extraDeck.length;
    document.getElementById("side-count").innerText = sideDeck.length;
}

// -------------------- Render Deck --------------------
function renderDeck(containerId, deckArray, categorize = false) {
    const container = document.getElementById(containerId);
    container.innerHTML = "";

    if (categorize) {
        const categories = { Monster: [], Spell: [], Trap: [] };

        deckArray.forEach(name => {
            const card = goatCards.find(c => c.name === name);
            if (!card) return;
            if (card.type.includes("Monster")) categories.Monster.push(card);
            else if (card.type.includes("Spell")) categories.Spell.push(card);
            else if (card.type.includes("Trap")) categories.Trap.push(card);
        });

        for (const [cat, cards] of Object.entries(categories)) {
            if (!cards.length) continue;

            const header = document.createElement("h6");
            header.innerText = `${cat} (${cards.length})`;
            container.appendChild(header);

            const catDiv = document.createElement("div");
            catDiv.className = "d-flex flex-wrap mb-2";

            cards.forEach(card => {
                const div = document.createElement("div");
                div.className = "deck-card d-inline-flex align-items-center bg-secondary text-white rounded me-1 mb-1 px-1 py-1";
                div.style.cursor = "pointer";

                const imgSrc = (card.local_images && card.local_images.length > 0)
                    ? card.local_images[0]
                    : "/static/images/placeholder.jpg";

                div.innerHTML = `
                    <img src="${imgSrc}" alt="${card.name}" style="width:30px; height:42px; object-fit:cover; margin-right:5px;">
                    <span style="font-size:0.8rem;">${card.name}</span>
                `;

                div.onclick = () => {
                    const i = deckArray.indexOf(card.name);
                    if (i > -1) deckArray.splice(i, 1);
                    updateDeckDisplay();
                };

                catDiv.appendChild(div);
            });

            container.appendChild(catDiv);
        }
    } else {
        deckArray.forEach((name, i) => {
            const card = goatCards.find(c => c.name === name);
            const imgSrc = (card && card.local_images && card.local_images.length > 0)
                ? card.local_images[0]
                : "/static/images/placeholder.jpg";

            const div = document.createElement("div");
            div.className = "deck-card d-inline-flex align-items-center bg-secondary text-white rounded me-1 mb-1 px-1 py-1";
            div.style.cursor = "pointer";
            div.innerHTML = `
                <img src="${imgSrc}" alt="${name}" style="width:30px; height:42px; object-fit:cover; margin-right:5px;">
                <span style="font-size:0.8rem;">${name}</span>
            `;
            div.onclick = () => { deckArray.splice(i, 1); updateDeckDisplay(); };
            container.appendChild(div);
        });
    }
}

// -------------------- Search --------------------
document.getElementById("search").addEventListener("input", e => {
    const term = e.target.value.toLowerCase();
    filteredCards = goatCards.filter(c => c.name.toLowerCase().includes(term));
    currentPage = 1;
    renderCardPool();
});

// -------------------- Pagination --------------------
document.getElementById("prev-page").onclick = () => {
    if (currentPage > 1) { currentPage--; renderCardPool(); }
};
document.getElementById("next-page").onclick = () => {
    if (currentPage < Math.ceil(filteredCards.length / cardsPerPage)) { currentPage++; renderCardPool(); }
};

// -------------------- Save Deck --------------------
document.getElementById("save-deck").onclick = async () => {
    const deckName = document.getElementById("deck-name").value || "mydeck";
    const res = await fetch("/deckbuilder", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ main: mainDeck, extra: extraDeck, side: sideDeck, deck_name: deckName })
    });
    const data = await res.json();
    alert(data.success ? "Deck saved as " + data.deck_name : "Error: " + data.error);
};



// -------------------- Load Deck --------------------
document.getElementById("load-deck").onclick = async () => {
    const deckFile = document.getElementById("load-deck-select").value;
    if (!deckFile) return alert("Select a deck to load.");

    // Fetch .ydk from backend
    const res = await fetch(`/load_ydk/${deckFile}`);
    if (!res.ok) return alert("Failed to load deck.");
    const data = await res.json();

    // Clear current decks
    mainDeck.length = 0; extraDeck.length = 0; sideDeck.length = 0;

    // Fill with loaded data
    data.main.forEach(c => mainDeck.push(c));
    data.extra.forEach(c => extraDeck.push(c));
    data.side.forEach(c => sideDeck.push(c));

    updateDeckDisplay();
    alert(`Deck "${deckFile.replace(".ydk","")}" loaded!`);
};

// -------------------- Initial Render --------------------
renderCardPool();
