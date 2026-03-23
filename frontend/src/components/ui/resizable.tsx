// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import {
  Panel,
  PanelGroup,
  PanelResizeHandle,
  type ImperativePanelHandle,
  type PanelGroupProps,
  type PanelProps,
  type PanelResizeHandleProps,
} from "react-resizable-panels";

import { cn } from "@/lib/utils";

export {
  Panel as ResizablePanel,
  PanelGroup as ResizablePanelGroup,
  type ImperativePanelHandle,
};

export function ResizableHandle({
  className,
  ...props
}: PanelResizeHandleProps) {
  return (
    <PanelResizeHandle
      className={cn("relative w-px bg-slate-200 focus-visible:outline-none", className)}
      {...props}
    />
  );
}

export type { PanelGroupProps, PanelProps, PanelResizeHandleProps };
