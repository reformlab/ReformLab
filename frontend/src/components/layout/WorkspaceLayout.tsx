// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
/**
 * WorkspaceLayout — responsive three-panel layout with mobile support.
 *
 * Story 22.7 — AC-4: Mobile layouts stack vertically, hide side panels.
 * - Desktop (lg+): ResizablePanelGroup with left/main/right panels
 * - Mobile (< lg): Single column layout with main content only
 */

import type { ReactNode } from "react";

import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";

interface WorkspaceLayoutProps {
  leftPanel: ReactNode;
  mainPanel: ReactNode;
  rightPanel: ReactNode;
  topBar?: ReactNode;
  mobileStageSwitcher?: ReactNode;
  isNarrow: boolean;
  leftCollapsed: boolean;
  rightCollapsed: boolean;
}

export function WorkspaceLayout({
  leftPanel,
  mainPanel,
  rightPanel,
  topBar,
  mobileStageSwitcher,
  isNarrow,
  leftCollapsed,
  rightCollapsed,
}: WorkspaceLayoutProps) {
  return (
    <div className="flex flex-1 flex-col overflow-hidden rounded-none border border-slate-200 bg-white">
      {topBar ? <div className="shrink-0">{topBar}</div> : null}

      {isNarrow ? (
        <>
          {/* Story 22.7: Mobile layout - single column, main content only */}
          {mobileStageSwitcher}
          <div className="flex flex-col flex-1 overflow-hidden">
            <main className="flex-1 overflow-auto">
              {mainPanel}
            </main>
          </div>
        </>
      ) : (
        /* Story 22.7: Desktop layout - resizable three-panel layout */
        <div className="flex min-h-0 flex-1">
          <ResizablePanelGroup direction="horizontal" className="h-full">
            <ResizablePanel
              defaultSize={22}
              minSize={leftCollapsed ? 3 : 18}
              maxSize={leftCollapsed ? 3 : 30}
            >
              {leftPanel}
            </ResizablePanel>
            <ResizableHandle />
            <ResizablePanel defaultSize={56} minSize={40}>
              {mainPanel}
            </ResizablePanel>
            <ResizableHandle />
            <ResizablePanel
              defaultSize={22}
              minSize={rightCollapsed ? 3 : 18}
              maxSize={rightCollapsed ? 3 : 35}
            >
              {rightPanel}
            </ResizablePanel>
          </ResizablePanelGroup>
        </div>
      )}
    </div>
  );
}
