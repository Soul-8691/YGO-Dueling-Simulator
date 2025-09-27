// ---------------- ASSETS ----------------
export const ASSETS = {
    mat: '/static/images/mats/scapegoat.png',
    defaultCard: '/static/images/card_back.png',
    cardBack: '/static/images/card_back.png'
};

// ---------------- BOARD ----------------
export const BOARD = {
    spacing: 8,                 // tighter spacing between zones
    marginLeft: 80,             // less margin on sides
    marginRight: 80,
    playerAreaHeight: 240,      // smaller vertical area per player
    monsterZoneSize: { w: 90, h: 120 },   // smaller monster zones
    spellZoneSize: { w: 90, h: 50 },      // smaller spell zones
    handCardSize: { w: 60, h: 85 },       // smaller hand cards
    zoneRadius: 10,
    cardSize: { w: 60, h: 90 } // <-- define card size her
};

// ---------------- USER INFO ----------------
export const USER = window.USERNAME || null;
export const GAME_ID = window.GAME_ID || null;