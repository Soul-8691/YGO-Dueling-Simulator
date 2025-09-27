import { BOARD, ASSETS } from './config.js';
import { currentGameState } from './sockets.js';




const BASE_WIDTH = 1200;
const BASE_HEIGHT = 800;




export function startGame() {
    // 🔹 Make container flexible with CSS
    const container = document.getElementById('gameContainer');
    container.style.width = '100%';
    container.style.height = '100%';
    container.style.margin = '0';
    container.style.display = 'flex';
    container.style.alignItems = 'center';
    container.style.justifyContent = 'center';

    const config = {
        type: Phaser.AUTO,
        width: BASE_WIDTH,
        height: BASE_HEIGHT,
        parent: 'gameContainer',
        backgroundColor: 0x1a1a1a,
        scale: {
            mode: Phaser.Scale.FIT,              // responsive scaling
            autoCenter: Phaser.Scale.CENTER_BOTH,
            min: { width: 300, height: 200 },    // allow scaling down
            max: { width: 1920, height: 1080 }   // allow scaling up
        },
        scene: { preload, create, update }
    };

    new Phaser.Game(config);
}

// ---------------------- Preload ----------------------
function preload() {
    if (ASSETS.mat) this.load.image('mat', ASSETS.mat);
    if (ASSETS.cardBack) this.load.image('card_back', ASSETS.cardBack);

    if (!currentGameState) return;

    const seen = new Set();
    Object.values(currentGameState.players || {}).forEach(player => {
        const allCards = [...(player.deck?.main || []), ...(player.deck?.extra || []), ...(player.hand || [])];
        allCards.forEach(card => {
            if (card.local_images?.[0] && !seen.has(card.id)) {
                seen.add(card.id);
                this.load.image(`card_${card.id}`, card.local_images[0]);
            }
        });
    });
}

// ---------------------- Create ----------------------
function create() {
    const canvasW = this.sys.game.config.width;
    const canvasH = this.sys.game.config.height;

    // Background mat
    if (ASSETS.mat) {
        this.mat = this.add.image(0, 0, 'mat').setOrigin(0, 0);
        this.mat.displayWidth = canvasW;
        this.mat.displayHeight = canvasH;
    }

    this.fieldContainer = this.add.container(0, 0);
    this.handContainer = this.add.container(0, 0);

    this.waitingText = this.add.text(
        canvasW / 2,
        canvasH / 2,
        'Waiting for players...',
        { fontSize: '28px', color: '#ffffff' }
    ).setOrigin(0.5);
}

// ---------------------- Update ----------------------
function update() {
    if (!this.fieldContainer || !this.handContainer) return;

    this.fieldContainer.removeAll(true);
    this.handContainer.removeAll(true);

    if (!currentGameState) {
        this.waitingText.setVisible(true);
        return;
    }

    this.waitingText.setVisible(false);

    preloadMissingCards.call(this, currentGameState, () => {
        renderGame.call(this, currentGameState);
    });
}

// ---------------------- Preload Missing Cards ----------------------
function preloadMissingCards(state, callback) {
    let loadRequired = false;
    Object.values(state.players || {}).forEach(player => {
        const allCards = [...(player.deck?.main || []), ...(player.deck?.extra || []), ...(player.hand || [])];
        allCards.forEach(card => {
            const key = `card_${card.card_id}`;
            if (!this.textures.exists(key) && card.image?.[0]) {
                this.load.image(key, card.image[0]);
                loadRequired = true;
            }
        });
    });

    if (loadRequired) {
        this.load.once('complete', callback);
        this.load.start();
    } else {
        callback();
    }
}

// ---------------------- Render Game ----------------------
function renderGame(state) {
    const players = Object.values(state.players || {});
    if (!players.length) return;

    const self = players.find(p => p.name === window.USERNAME) || players[0];
    const opp  = players.find(p => p.name !== window.USERNAME) || players[0];

    drawField.call(this, opp, true);
    drawHand.call(this, opp, true);

    drawField.call(this, self, false);
    drawHand.call(this, self, false);
}

// ---------------------- Draw Field ----------------------
function drawField(player, isOpponent) {
    const canvasW = this.sys.game.config.width;
    const canvasH = this.sys.game.config.height;

    // Dynamic zone size proportional to screen
    const zW = (BOARD.monsterZoneSize.w / BASE_WIDTH) * canvasW;
    const zH = (BOARD.monsterZoneSize.h / BASE_HEIGHT) * canvasH;

    const verticalMargin = canvasH * 0.05;
    const rowSpacing = zH * 0.25;
    const fieldSpacing = zH * 0.5;

    let topRow, bottomRow;
    if (isOpponent) {
        topRow = ['', 'DECK','S5','S4','S3','S2','S1','EXTRA'];
        bottomRow = ['BAN','GY','M5','M4','M3','M2','M1','FIELD'];
    } else {
        topRow = ['FIELD','M1','M2','M3','M4','M5','GY','BAN'];
        bottomRow = ['EXTRA','S1','S2','S3','S4','S5','DECK',''];
    }

    const spacing = (canvasW - topRow.length * zW) / (topRow.length + 1);
    const totalFieldHeight = zH * 2 + rowSpacing + fieldSpacing;
    const topY = isOpponent ? verticalMargin : canvasH - verticalMargin - totalFieldHeight;
    const bottomY = topY + zH + rowSpacing;

    drawRow.call(this, topRow, topY, zW, zH, spacing, isOpponent, canvasW, isOpponent);
    drawRow.call(this, bottomRow, bottomY, zW, zH, spacing, isOpponent, canvasW, isOpponent);
}

// ---------------------- Draw Row & Zone ----------------------
function drawRow(slots, y, w, h, spacing, flipVertically, canvasW, flipHorizontally = false) {
    const n = slots.length;
    const totalW = n * w + (n - 1) * spacing;
    const startX = (canvasW - totalW) / 2;

    slots.forEach((label, i) => {
        let x = startX + i * (w + spacing);
        if (flipHorizontally) x = canvasW - (x + w);
        drawZone.call(this, x, y, w, h, label, flipVertically, flipHorizontally);
    });
}

function drawZone(x, y, w, h, label, flipVertically, flipHorizontally = false) {
    const zone = this.add.container(x, y);
    const bgColor = label ? 0x000000 : 0x222222;

    const bg = this.add.rectangle(0, 0, w, h, bgColor, 0.45)
        .setStrokeStyle(2, 0xffffff, 0.25)
        .setOrigin(0, 0);
    zone.add(bg);

    if (label) {
        const text = this.add.text(w / 2, h / 2, label, { fontSize: Math.max(12, w/8) + 'px', color: '#fff' })
            .setOrigin(0.5);
        zone.add(text);
    }

    if (flipVertically) {
        zone.y += h;
        zone.scaleY = -1;
    }

    if (flipHorizontally) {
        zone.x += w;
        zone.scaleX = -1;
    }

    this.fieldContainer.add(zone);
}

// ---------------------- Draw Hand ----------------------
function drawHand(player, isOpponent) {
    if (!player.hand || !player.hand.length) return;

    const canvasW = this.sys.game.config.width;
    const canvasH = this.sys.game.config.height;

    const cardW = (BOARD.handCardSize.w / BASE_WIDTH) * canvasW;
    const cardH = (BOARD.handCardSize.h / BASE_HEIGHT) * canvasH;
    const handSpacing = cardW * 0.15;

    const totalHandWidth = player.hand.length * cardW + (player.hand.length - 1) * handSpacing;
    const startX = (canvasW - totalHandWidth) / 2;
    const y = isOpponent ? -40 : canvasH - cardH - 10;

    player.hand.forEach((card, i) => {
        const key = `card_${card.card_id}`;
        if (!this.textures.exists(key)) return;

        let x = startX + i * (cardW + handSpacing);
        if (isOpponent) x = canvasW - (x + cardW);

        const spriteKey = isOpponent ? 'card_back' : key;

        const sprite = this.add.image(x, y, spriteKey)
            .setOrigin(0, 0)
            .setDisplaySize(cardW, cardH);

        if (!isOpponent) {
            sprite.setInteractive();
            sprite.on('pointerdown', () => {
                if (currentGameState.turn === window.socket.id) {
                    window.socket.emit('play_card', {
                        game_id: currentGameState.id,
                        card_id: card.card_id
                    });
                }
            });
        }

        this.handContainer.add(sprite);
    });
}
