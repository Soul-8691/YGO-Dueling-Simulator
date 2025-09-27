import * as PIXI from './pixi.mjs';

export let app;

export function initCanvas() {
    app = new PIXI.Application({
        width: window.innerWidth,
        height: window.innerHeight,
        backgroundColor: 0x081016,
        resolution: window.devicePixelRatio || 1,
        autoDensity: true
    });

    // Add Pixi canvas to the DOM
    document.body.appendChild(app.view);

    // Handle window resize
    window.addEventListener('resize', () => {
        if (app && app.renderer) {
            app.renderer.resize(window.innerWidth, window.innerHeight);
            app.stage.scale.set(1);
        }
    });
}

export function resizeCanvas() {
    if (!app) return;

    const width = window.innerWidth;
    const height = window.innerHeight;

    app.renderer.resize(width, height);
    app.stage.scale.set(1);
}