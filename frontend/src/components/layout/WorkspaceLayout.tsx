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
  leftCollapsed: boolean;
  rightCollapsed: boolean;
}

export function WorkspaceLayout({
  leftPanel,
  mainPanel,
  rightPanel,
  leftCollapsed,
  rightCollapsed,
}: WorkspaceLayoutProps) {
  return (
    <div className="h-[calc(100vh-5.5rem)] rounded-lg border border-slate-200 bg-white overflow-hidden">
      <ResizablePanelGroup direction="horizontal">
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
  );
}
