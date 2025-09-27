// pixiBoard.js
// Goat-format responsive board with PixiJS

// Create PixiJS app
const app = new PIXI.Application({
    width: Math.floor(window.innerWidth * 0.95),
    height: Math.floor(window.innerHeight * 0.8),
    backgroundColor: 0x0b0b0b,
    resolution: window.devicePixelRatio || 1,
    autoDensity: true,
});
document.getElementById('duelBoard').appendChild(app.view);

// Layout constants
const COLUMNS = 8;
const ROWS_PER_PLAYER = 2;
const GAP = 12;
const PADDING = 24;

// Zone order (matches your HTML grid)
const ROW_ORDER = [
    ["Field","M1","M2","M3","M4","M5","GY","Banished"], // row1
    ["Extra","S1","S2","S3","S4","S5","Deck", null]     // row2 (col8 empty)
];

// Store zones and cards
const zonesStore = { opponent: {}, self: {} };
const cardSprites = [];

// Containers for players
const opponentContainer = new PIXI.Container();
const selfContainer = new PIXI.Container();
app.stage.addChild(opponentContainer);
app.stage.addChild(selfContainer);

// Create zone graphics with label
function createZoneGraphics(name, w, h) {
    const cont = new PIXI.Container();
    const bg = new PIXI.Graphics();
    bg.lineStyle(2, 0xffffff, 0.12);
    bg.beginFill(0x000000, 0.28);
    bg.drawRoundedRect(0, 0, w, h, 8);
    bg.endFill();
    cont.addChild(bg);

    if (name) {
        const text = new PIXI.Text(name, { fontSize: Math.max(12, Math.floor(w*0.12)), fill: 0xffffff });
        text.anchor.set(0.5);
        text.x = w/2;
        text.y = h/2;
        cont.addChild(text);
    }
    return cont;
}

// Layout the board
function layoutBoard() {
    opponentContainer.removeChildren();
    selfContainer.removeChildren();

    const bw = app.renderer.width;
    const bh = app.renderer.height;

    // Compute zone width & height
    const totalGaps = GAP * (COLUMNS - 1);
    const usableWidth = bw - PADDING*2;
    const zoneW = Math.floor((usableWidth - totalGaps)/COLUMNS);
    const zoneH = Math.floor(zoneW * 7/5); // 5:7 ratio

    // Player area height
    const playerAreaHeight = ROWS_PER_PLAYER*zoneH + GAP;
    const totalRequiredHeight = playerAreaHeight*2 + GAP;
    let scale = 1;
    if (totalRequiredHeight + PADDING*2 > bh) {
        scale = (bh - PADDING*2) / totalRequiredHeight;
    }

    const finalZoneW = Math.max(32, Math.floor(zoneW*scale));
    const finalZoneH = Math.max(44, Math.floor(zoneH*scale));
    const horizontalOffset = Math.floor((bw - (finalZoneW*COLUMNS + GAP*(COLUMNS-1)))/2);

    // Y positions
    const opponentYStart = PADDING;
    const selfYStart = Math.floor(bh - PADDING - playerAreaHeight*scale);

    // Helper to place zones
    function placeZone(container, zonesMap, playerKey, colIndex, rowIndex, name) {
        if (!name) return;
        const x = horizontalOffset + colIndex*(finalZoneW+GAP);
        const y = (playerKey==="opponent"? opponentYStart : selfYStart) + rowIndex*(finalZoneH+GAP);
        const gfx = createZoneGraphics(name, finalZoneW, finalZoneH);
        gfx.x = x;
        gfx.y = y;
        container.addChild(gfx);

        zonesMap[name] = { container: gfx, rect: new PIXI.Rectangle(x, y, finalZoneW, finalZoneH) };
    }

    // Build zones
    for (let r=0; r<ROW_ORDER.length; r++) {
        for (let c=0; c<ROW_ORDER[r].length; c++) {
            placeZone(opponentContainer, zonesStore.opponent, "opponent", c, r, ROW_ORDER[r][c]);
            placeZone(selfContainer, zonesStore.self, "self", c, r, ROW_ORDER[r][c]);
        }
    }

    // Reposition cards
    for (const cd of cardSprites) {
        const zoneMap = zonesStore[cd.player];
        const zoneInfo = zoneMap[cd.zoneName];
        if (!zoneInfo) {
            cd.sprite.visible = false;
            continue;
        }
        cd.sprite.visible = true;
        const w = Math.max(6, Math.floor(zoneInfo.rect.width-10));
        const h = Math.max(8, Math.floor(zoneInfo.rect.height-10));
        cd.sprite.width = w;
        cd.sprite.height = h;
        cd.sprite.x = zoneInfo.rect.x + 5;
        cd.sprite.y = zoneInfo.rect.y + 5;
    }
}

// Add a card
function addCardToZone(zoneName, player="self", imgPath="/static/images/default_card.png", id=null) {
    const tex = PIXI.Texture.from(imgPath);
    const sprite = new PIXI.Sprite(tex);
    sprite.interactive = true;
    sprite.buttonMode = true;
    sprite.on("pointerdown", ()=>console.log("Card clicked:", player, zoneName, id ?? ""));
    app.stage.addChild(sprite);

    const record = { sprite, player, zoneName, imgPath, id };
    cardSprites.push(record);

    const zoneMap = zonesStore[player];
    const zoneInfo = zoneMap[zoneName];
    if (zoneInfo) {
        sprite.visible = true;
        sprite.width = Math.max(6, Math.floor(zoneInfo.rect.width-10));
        sprite.height = Math.max(8, Math.floor(zoneInfo.rect.height-10));
        sprite.x = zoneInfo.rect.x + 5;
        sprite.y = zoneInfo.rect.y + 5;
    } else {
        sprite.visible = false;
    }
    return sprite;
}

// Remove all cards
function clearAllCards() {
    while(cardSprites.length){
        const rec = cardSprites.pop();
        app.stage.removeChild(rec.sprite);
        rec.sprite.destroy();
    }
}

// Initial layout
layoutBoard();

// Example card
addCardToZone("M1","self");

// Responsive resize
function onResize(){
    app.renderer.resize(Math.floor(window.innerWidth*0.95), Math.floor(window.innerHeight*0.8));
    layoutBoard();
}
window.addEventListener("resize", onResize);

// Expose helpers
window.PIXI_BOARD = {
    addCardToZone,
    clearAllCards,
    zonesStore,
    layoutBoard,
    app
};
