import type { ReactNode } from "react";

interface MainContentProps {
  children: ReactNode;
}

export function MainContent({ children }: MainContentProps) {
  return (
    <main className="h-full min-w-0 bg-white">
      <div className="h-full overflow-auto p-3">{children}</div>
    </main>
  );
}
