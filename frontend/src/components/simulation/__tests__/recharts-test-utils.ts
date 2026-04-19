// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier

import { afterAll, beforeAll } from "vitest";

function resizeObserverEntry(target: Element): ResizeObserverEntry {
  return {
    target,
    contentRect: {
      x: 0,
      y: 0,
      width: 800,
      height: 300,
      top: 0,
      right: 800,
      bottom: 300,
      left: 0,
      toJSON: () => ({}),
    },
    borderBoxSize: [],
    contentBoxSize: [],
    devicePixelContentBoxSize: [],
  };
}

export function setupRechartsResponsiveContainerMock(): void {
  const originalResizeObserver = globalThis.ResizeObserver;
  const originalRequestAnimationFrame = globalThis.requestAnimationFrame;
  const originalCancelAnimationFrame = globalThis.cancelAnimationFrame;

  beforeAll(() => {
    globalThis.ResizeObserver = class {
      private readonly callback: ResizeObserverCallback;

      constructor(callback: ResizeObserverCallback) {
        this.callback = callback;
      }

      observe(target: Element) {
        this.callback([resizeObserverEntry(target)], this);
      }

      unobserve() {}
      disconnect() {}
    };
    globalThis.requestAnimationFrame = (callback) =>
      window.setTimeout(() => callback(performance.now()), 0);
    globalThis.cancelAnimationFrame = (handle) => window.clearTimeout(handle);
  });

  afterAll(() => {
    globalThis.ResizeObserver = originalResizeObserver;
    globalThis.requestAnimationFrame = originalRequestAnimationFrame;
    globalThis.cancelAnimationFrame = originalCancelAnimationFrame;
  });
}

export function renderedBarShapes(container: HTMLElement): NodeListOf<Element> {
  return container.querySelectorAll(
    "svg .recharts-bar-rectangle rect, svg .recharts-bar-rectangle path",
  );
}

export function renderedAreaPaths(container: HTMLElement): NodeListOf<Element> {
  return container.querySelectorAll("svg .recharts-area-area");
}
