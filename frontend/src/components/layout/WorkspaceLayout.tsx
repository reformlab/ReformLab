// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
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
  leftCollapsed: boolean;
  rightCollapsed: boolean;
}

export function WorkspaceLayout({
  leftPanel,
  mainPanel,
  rightPanel,
  topBar,
  leftCollapsed,
  rightCollapsed,
}: WorkspaceLayoutProps) {
  return (
    <div className="flex flex-1 flex-col overflow-hidden rounded-none border border-slate-200 bg-white">
      {topBar ? <div className="shrink-0">{topBar}</div> : null}
      <div className="min-h-0 flex-1">
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
    </div>
  );
}
