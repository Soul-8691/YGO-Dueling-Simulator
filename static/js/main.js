// Make socket global
if (!window.socket) window.socket = io();

document.addEventListener('DOMContentLoaded', async () => {
    const playerName = window.USERNAME;
    const gameId = window.GAME_ID;

    if (!playerName || !gameId) {
        alert("Username or game ID not found!");
        return;
    }

    await initGame(gameId, playerName);

    const endBtn = document.getElementById('endTurnBtn');
    if (endBtn) endBtn.style.display = 'block';
});

async function initGame(gameId, playerName) {
    const socket = window.socket;

    // Load player's deck
    let deckData = null;
    if (window.USER_DECK) {
        const res = await fetch(`/load_ydk/${window.USER_DECK}`);
        deckData = await res.json();
    }

    socket.on('connect', () => {
        console.log('Connected as', socket.id);
        socket.emit('join', { game_id: gameId, name: playerName, deck: deckData });
    });

    // Listen for game state updates
    socket.on('game_state', (state) => {
        if (!state.started) {
            document.getElementById('turnIndicator').innerText = 'Waiting for another player...';
            return;
        }

        renderAllFields(state);
        renderOpponentHands(state);
        const selfPlayer = state.players[socket.id];
        renderHand(selfPlayer, state);
        updateTurnIndicator(state.turn, state.players);
    });

    socket.on('error', (err) => {
        console.error(err);
        alert(err.error || "Socket error");
    });
}

// Render all player fields
function renderAllFields(state) {
    for (const playerId in state.players) {
        const player = state.players[playerId];
        const container = (playerId === window.socket.id)
            ? document.querySelector('.player-field.self')
            : document.querySelector('.player-field.opponent');
        renderZones(container, player);
    }
}

// Render opponent hands as card backs
function renderOpponentHands(state) {
    const opponentDiv = document.querySelector('.opponent-hand');
    if (!opponentDiv) return;

    opponentDiv.innerHTML = '<strong>Opponent Hand:</strong> ';
    for (const playerId in state.players) {
        if (playerId === window.socket.id) continue; // skip self
        const player = state.players[playerId];
        for (let i = 0; i < (player.hand?.length || 0); i++) {
            const img = document.createElement('img');
            img.src = '/static/images/card_back.png'; // card back image
            img.alt = 'Card Back';
            img.className = 'hand-card';
            opponentDiv.appendChild(img);
        }
    }
}

// Render a single player's zones
function renderZones(container, player) {
    if (!container || !player) return;

    const monsterZones = container.querySelectorAll('.monster-zone');
    const spellZones = container.querySelectorAll('.spell-zone');

    container.querySelector('.extra').innerText = `Extra (${player.extra?.length || 0})`;
    container.querySelector('.deck').innerText = `Deck (${player.deck?.length || 0})`;
    container.querySelector('.grave').innerText = `GY (${player.grave?.length || 0})`;
    container.querySelector('.field').innerText = player.fieldSpell?.name || 'Field';

    // Render monster zones as images
    (player.field || []).forEach((card, i) => {
        if (monsterZones[i]) {
            monsterZones[i].innerHTML = '';
            const img = document.createElement('img');
            img.src = card.image || '/static/images/default_card.png';
            img.alt = card.name;
            img.title = `${card.name}\nATK: ${card.attack ?? card.atk}\nDEF: ${card.defense ?? card.def}`;
            img.classList.add('board-card');
            monsterZones[i].appendChild(img);
        }
    });

    // Render spell zones as images
    (player.spell || []).forEach((card, i) => {
        if (spellZones[i]) {
            spellZones[i].innerHTML = '';
            const img = document.createElement('img');
            img.src = card.image || '/static/images/default_card.png';
            img.alt = card.name;
            img.title = card.name;
            img.classList.add('board-card');
            spellZones[i].appendChild(img);
        }
    });
}

// Render player's hand as images
function renderHand(player, state) {
    if (!player) return;

    const handDiv = document.querySelector('.hand-container');
    handDiv.innerHTML = '<strong>Hand:</strong> ';

    (player.hand || []).forEach(card => {
        const img = document.createElement('img');
        img.src = card.image || '/static/images/default_card.png';
        img.alt = card.name;
        img.title = card.name;
        img.classList.add('hand-card');
        img.onclick = () => {
            if (state.turn === window.socket.id) {
                window.socket.emit('play_card', { game_id: state.id, card_id: card.id ?? card.name });
            }
        };
        handDiv.appendChild(img);
    });
}

// Update turn indicator
function updateTurnIndicator(turnSid, players) {
    const turnDiv = document.getElementById('turnIndicator');
    if (!turnDiv || !turnSid || !players[turnSid]) return;
    turnDiv.innerText = "Current Turn: " + players[turnSid].name;
}

// End turn button
function endTurn() {
    if (!window.socket) return;
    const gameDiv = document.getElementById('game');
    window.socket.emit('end_turn', { game_id: gameDiv.dataset.gameId });
}