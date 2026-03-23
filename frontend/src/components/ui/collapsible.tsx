// SPDX-License-Identifier: AGPL-3.0-or-later
// Copyright 2026 Lucas Vivier
import * as CollapsiblePrimitive from "@radix-ui/react-collapsible";
import type { ComponentProps } from "react";

export function Collapsible(props: ComponentProps<typeof CollapsiblePrimitive.Root>) {
  return <CollapsiblePrimitive.Root {...props} />;
}

export function CollapsibleTrigger(
  props: ComponentProps<typeof CollapsiblePrimitive.Trigger>,
) {
  return <CollapsiblePrimitive.Trigger {...props} />;
}

export function CollapsibleContent(
  props: ComponentProps<typeof CollapsiblePrimitive.Content>,
) {
  return <CollapsiblePrimitive.Content {...props} />;
}
