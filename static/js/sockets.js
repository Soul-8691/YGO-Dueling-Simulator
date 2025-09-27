import { USER, GAME_ID } from './config.js';

export let currentGameState = null;
let socket = null;

// ---------------------- Initialize Socket ----------------------
export function initSocket() {
    if (!window.socket) window.socket = io();
    socket = window.socket;

    // On connect
    socket.on('connect', () => {
        console.log('[SOCKET] Connected:', socket.id);
        joinGame();
    });

    // Receive game state updates
    socket.on('game_state', (state) => {
        currentGameState = state;
        console.log('[SOCKET] Game state updated:', state);

        // Update turn indicator
        const turnDiv = document.getElementById('turnIndicator');
        if (turnDiv && state.turn && state.players) {
            const activeName = state.players[state.turn]?.name || '—';
            turnDiv.innerText = `Current Turn: ${activeName}`;
        }
    });

    // Handle errors
    socket.on('error', (err) => console.error('[SOCKET] Error:', err));
}

// ---------------------- Join Game ----------------------
export async function joinGame() {
    if (!socket || !USER || !GAME_ID) return;

    let deckData = { main: [], extra: [] };

    // Fetch deck JSON from server if specified
    if (window.USER_DECK) {
        try {
            const res = await fetch(`/load_ydk/${window.USER_DECK}`);
            if (!res.ok) throw new Error('Failed to fetch deck');
            deckData = await res.json();
            console.log('[SOCKET] Loaded deck:', deckData);
        } catch (e) {
            console.warn('[SOCKET] Could not load deck, using empty:', e);
        }
    }

    // Emit join with deck
    socket.emit('join', { game_id: GAME_ID, name: USER, deck: deckData });
    console.log('[SOCKET] Joining game', GAME_ID, 'as', USER);
}

// ---------------------- End Turn ----------------------
export function endTurn() {
    if (!socket) return;
    socket.emit('end_turn', { game_id: GAME_ID });
    console.log('[SOCKET] End turn emitted');
}
