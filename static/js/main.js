let socket;

function initGame(gameId, name) {
    socket = io();

    socket.on('connect', () => {
        console.log('Connected as', socket.id);
        socket.emit('join', { game_id: gameId, name: name });
    });

    socket.on('game_state', (state) => {
        if (!state.started) {
            document.getElementById('game').innerHTML = '<p>Waiting for another player...</p>';
            document.getElementById('turnIndicator').innerText = '';
            return;
        }

        renderGame(state);
        updateTurnIndicator(state.turn, state.players);
    });

    socket.on('error', (err) => {
        console.error(err);
        alert(err.error);
    });
}

function renderGame(state) {
    const div = document.getElementById('game');
    div.innerHTML = '';

    for (const sid in state.players) {
        const player = state.players[sid];

        const pDiv = document.createElement('div');
        pDiv.classList.add('player-section');
        pDiv.innerHTML = `<h3>${player.name} (LP: ${player.lp})</h3>`;

        // --- Hand ---
        const handDiv = document.createElement('div');
        handDiv.classList.add('hand');
        handDiv.innerHTML = '<strong>Hand:</strong> ';
        player.hand.forEach((c) => {
            const btn = document.createElement('button');
            btn.innerText = c.name;
            btn.disabled = (sid !== state.turn); // only current player can summon
            btn.onclick = () => {
                socket.emit('play_card', { game_id: state.id, card_id: c.name });
            };
            handDiv.appendChild(btn);
        });
        pDiv.appendChild(handDiv);

        // --- Field ---
        const fieldDiv = document.createElement('div');
        fieldDiv.classList.add('field');
        fieldDiv.innerHTML = '<strong>Field:</strong> ';
        player.field.forEach((c) => {
            const btn = document.createElement('button');
            btn.innerText = `${c.name} (ATK: ${c.attack})`;
            // future: attach attack logic here
            fieldDiv.appendChild(btn);
        });
        pDiv.appendChild(fieldDiv);

        div.appendChild(pDiv);
    }
}

function updateTurnIndicator(turnSid, players) {
    const turnDiv = document.getElementById('turnIndicator');
    if (!turnSid || !players[turnSid]) {
        turnDiv.innerText = '';
        return;
    }
    turnDiv.innerText = "Current Turn: " + players[turnSid].name;
}

function endTurn() {
    socket.emit('end_turn', { game_id: GAME_ID });
}