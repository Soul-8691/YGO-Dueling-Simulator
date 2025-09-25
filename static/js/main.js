let socket;

document.addEventListener('DOMContentLoaded', () => {
    const joinForm = document.getElementById('joinForm');
    joinForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const playerName = document.getElementById('playerName').value;
        const gameDiv = document.getElementById('game');
        const gameId = gameDiv.dataset.gameId;
        initGame(gameId, playerName);
        joinForm.style.display = 'none';
        document.getElementById('endTurnBtn').style.display = 'block';
    });
});

function initGame(gameId, playerName) {
    socket = io();

    socket.on('connect', () => {
        console.log('Connected as', socket.id);
        socket.emit('join', { game_id: gameId, name: playerName });
    });

    socket.on('game_state', (state) => {
        if (!state.started) {
            document.getElementById('turnIndicator').innerText = 'Waiting for another player...';
            return;
        }
        renderAllFields(state);
        renderHand(state.players[socket.id], state);
        updateTurnIndicator(state.turn, state.players);
    });

    socket.on('error', (err) => {
        console.error(err);
        alert(err.error || "Socket error");
    });
}

// Render both self and opponent fields
function renderAllFields(state) {
    for (const playerId in state.players) {
        const player = state.players[playerId];
        const container = (playerId === socket.id)
            ? document.querySelector('.player-field.self')
            : document.querySelector('.player-field.opponent');
        renderZones(container, player);
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

    // Populate monster zones
    (player.field || []).forEach((card, i) => {
        if (monsterZones[i]) monsterZones[i].innerText = `${card.name}\nATK: ${card.attack}`;
    });

    // Populate spell zones
    (player.spell || []).forEach((card, i) => {
        if (spellZones[i]) spellZones[i].innerText = card.name;
    });
}

// Render the player's hand
function renderHand(player, state) {
    if (!player) return;
    const handDiv = document.querySelector('.hand-container');
    handDiv.innerHTML = '<strong>Hand:</strong> ';
    (player.hand || []).forEach(card => {
        const btn = document.createElement('button');
        btn.innerText = card.name;
        btn.disabled = (state.turn !== socket.id); // only allow playing on your turn
        btn.onclick = () => socket.emit('play_card', { game_id: state.id, card_id: card.name });
        handDiv.appendChild(btn);
    });
}

// Update turn indicator
function updateTurnIndicator(turnSid, players) {
    const turnDiv = document.getElementById('turnIndicator');
    if (!turnDiv || !turnSid || !players[turnSid]) return;
    turnDiv.innerText = "Current Turn: " + players[turnSid].name;
}

// End turn
function endTurn() {
    const gameDiv = document.getElementById('game');
    if (!gameDiv || !socket) return;
    socket.emit('end_turn', { game_id: gameDiv.dataset.gameId });
}