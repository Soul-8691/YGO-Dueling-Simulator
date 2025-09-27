import { initSocket } from './sockets.js';
import { startGame } from './game.js'; // Phaser setup is in game.js

// Initialize sockets
initSocket();



// Start Phaser game
window.onload = () => {
    startGame();
};