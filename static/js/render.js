// render.js
import { app } from './canvas.js';
import { BOARD, USER, ASSETS } from './config.js';
import { currentGameState } from './sockets.js';
import * as PIXI from './pixi.mjs';

// ---------------- GLOBALS ----------------
let fieldContainer = null;

// ---------------- MAIN LOOP ----------------
export function animateGame() {
    if (!app) return console.error('Pixi app not initialized');

    if (!fieldContainer) {
        fieldContainer = new PIXI.Container();
        app.stage.addChild(fieldContainer);
    }

    app.ticker.add(() => {
        fieldContainer.removeChildren();

        drawMat();

        if (currentGameState) renderGame(currentGameState);
        else drawCentered('Waiting for players...', app.renderer.width / 2, app.renderer.height / 2, 28);
    });
}

// ---------------- RENDER GAME ----------------
function renderGame(state) {
    const players = Object.values(state.players || {});
    if (!players.length) return;

    const self = players.find(p => p.name === USER) || players[0];
    const opp  = players.find(p => p.name !== USER) || players[0];

    drawField(opp, true);
    drawField(self, false);
}

// ---------------- DRAW FIELD ----------------
function drawField(player, isOpponent) {
    const container = new PIXI.Container();
    const canvasW = app.renderer.width;
    const canvasH = app.renderer.height;
    const zW = BOARD.monsterZoneSize.w;
    const zH = BOARD.monsterZoneSize.h;
    const spacing = BOARD.spacing;

    // Row positions
    const rowsHeight = zH * 2 + spacing;
    let topY, bottomY;
    if (isOpponent) {
        topY = 50;                   // opponent top row
        bottomY = topY + zH + spacing;
    } else {
        bottomY = canvasH - 50 - zH; // player bottom row
        topY = bottomY - zH - spacing;
    }

    // Define zones
    let topRow = [], bottomRow = [];
    if (isOpponent) {
        topRow = ['DECK','S5','S4','S3','S2','S1','EXTRA'];
        bottomRow = ['BAN','GY','M5','M4','M3','M2','M1','FIELD'];
    } else {
        topRow = ['FIELD','M1','M2','M3','M4','M5','GY','BAN'];
        bottomRow = ['EXTRA','S1','S2','S3','S4','S5','DECK'];
    }

    drawRow(topRow, topY, container, zW, zH, spacing);
    drawRow(bottomRow, bottomY, container, zW, zH, spacing);

    if (isOpponent) {
        container.y = bottomY + zH; // move pivot to bottom row
        container.pivot.y = container.height;
        container.scale.y = -1;      // flip vertically
    }

    fieldContainer.addChild(container);
}

// ---------------- DRAW ROW ----------------
function drawRow(slots, y, container, w, h, spacing) {
    const n = slots.length;
    const totalW = n * w + (n - 1) * spacing;
    const startX = Math.round((app.renderer.width - totalW) / 2);

    slots.forEach((label, i) => {
        const x = startX + i * (w + spacing);
        drawZone(x, y, w, h, label, container);
    });
}

// ---------------- DRAW ZONE ----------------
function drawZone(x, y, w, h, labelText, container) {
    const zone = new PIXI.Container();

    const bg = new PIXI.Graphics();
    bg.lineStyle(2, 0xffffff, 0.3);
    bg.beginFill(0x000000, 0.2);
    bg.drawRoundedRect(0, 0, w, h, 8);
    bg.endFill();
    zone.addChild(bg);

    if (labelText) {
        const label = new PIXI.Text(labelText, { fontSize: 14, fill: 0xffffff });
        label.anchor.set(0.5);
        label.x = w / 2;
        label.y = h / 2;
        zone.addChild(label);
    }

    zone.x = x;
    zone.y = y;
    container.addChild(zone);
}

// ---------------- DRAW MAT ----------------
function drawMat() {
    if (!ASSETS.mat) return;
    const tex = PIXI.Texture.from(ASSETS.mat);
    const mat = new PIXI.Sprite(tex);
    mat.width = app.renderer.width;
    mat.height = app.renderer.height;
    fieldContainer.addChild(mat); // always behind zones
}

// ---------------- DRAW CENTERED TEXT ----------------
function drawCentered(text, x, y, size) {
    const label = new PIXI.Text(text, { fontSize: size, fill: 0xffffff });
    label.anchor.set(0.5);
    label.x = x;
    label.y = y;
    fieldContainer.addChild(label);
}
