// assets.js
export const ASSETS = {
    mat: '/static/images/mats/scapegoat.png',
    defaultCard: '/static/images/card_back.png',
    cardBack: '/static/images/card_back.png'
};

const imageCache = new Map();

export function loadImage(url) {
    if (imageCache.has(url)) {
        const el = imageCache.get(url);
        if (el.complete) return Promise.resolve(el);
        return new Promise(res => el.addEventListener('load', () => res(el)));
    }
    const img = new Image();
    img.src = url;
    imageCache.set(img.src, img);
    return new Promise(res => {
        if (img.complete) return res(img);
        img.addEventListener('load', () => res(img));
        img.addEventListener('error', () => {
            const fallback = document.createElement('canvas');
            fallback.width = fallback.height = 1;
            imageCache.set(url, fallback);
            res(fallback);
        });
    });
}

export function preloadAssets() {
    return Promise.all([
        loadImage(ASSETS.mat),
        loadImage(ASSETS.defaultCard),
        loadImage(ASSETS.cardBack)
    ]);
}

export { imageCache };