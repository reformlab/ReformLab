/** Generic single-select card grid (Story 18.3, AC-3). */

import type { ReactNode } from "react";

interface SelectionGridProps<T> {
  items: T[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  getId: (item: T) => string;
  renderCard: (item: T, selected: boolean) => ReactNode;
  className?: string;
}

export function SelectionGrid<T>({
  items,
  selectedId,
  onSelect,
  getId,
  renderCard,
  className,
}: SelectionGridProps<T>) {
  return (
    <section className={className ?? "grid gap-2 xl:grid-cols-2"}>
      {items.map((item) => {
        const id = getId(item);
        const selected = id === selectedId;
        return (
          <button
            type="button"
            key={id}
            aria-pressed={selected}
            onClick={() => onSelect(id)}
            className="text-left"
          >
            {renderCard(item, selected)}
          </button>
        );
      })}
    </section>
  );
}
