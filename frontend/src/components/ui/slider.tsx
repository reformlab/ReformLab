import * as SliderPrimitive from "@radix-ui/react-slider";
import type { ComponentProps } from "react";

import { cn } from "@/lib/utils";

export function Slider({
  className,
  ...props
}: ComponentProps<typeof SliderPrimitive.Root>) {
  return (
    <SliderPrimitive.Root className={cn("relative flex w-full touch-none items-center", className)} {...props}>
      <SliderPrimitive.Track className="relative h-1.5 w-full grow bg-slate-200">
        <SliderPrimitive.Range className="absolute h-full bg-blue-500" />
      </SliderPrimitive.Track>
      <SliderPrimitive.Thumb className="block h-3 w-3 border border-blue-600 bg-white shadow-none focus:outline-none" />
    </SliderPrimitive.Root>
  );
}
