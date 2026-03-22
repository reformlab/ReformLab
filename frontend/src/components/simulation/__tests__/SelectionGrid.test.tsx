import { fireEvent, render, screen } from "@testing-library/react";

import { SelectionGrid } from "@/components/simulation/SelectionGrid";

interface Item {
  id: string;
  name: string;
}

const items: Item[] = [
  { id: "a", name: "Alpha" },
  { id: "b", name: "Beta" },
  { id: "c", name: "Gamma" },
];

describe("SelectionGrid", () => {
  it("renders all items", () => {
    render(
      <SelectionGrid
        items={items}
        selectedId={null}
        onSelect={vi.fn()}
        getId={(item) => item.id}
        renderCard={(item) => <span>{item.name}</span>}
      />,
    );
    expect(screen.getByText("Alpha")).toBeInTheDocument();
    expect(screen.getByText("Beta")).toBeInTheDocument();
    expect(screen.getByText("Gamma")).toBeInTheDocument();
  });

  it("calls onSelect with the id when an item is clicked", () => {
    const onSelect = vi.fn();
    render(
      <SelectionGrid
        items={items}
        selectedId={null}
        onSelect={onSelect}
        getId={(item) => item.id}
        renderCard={(item) => <span>{item.name}</span>}
      />,
    );
    fireEvent.click(screen.getByText("Beta"));
    expect(onSelect).toHaveBeenCalledWith("b");
  });

  it("passes selected=true to renderCard for the selected item", () => {
    render(
      <SelectionGrid
        items={items}
        selectedId="a"
        onSelect={vi.fn()}
        getId={(item) => item.id}
        renderCard={(item, selected) => (
          <span data-testid={`card-${item.id}`} data-selected={String(selected)}>
            {item.name}
          </span>
        )}
      />,
    );
    expect(screen.getByTestId("card-a")).toHaveAttribute("data-selected", "true");
    expect(screen.getByTestId("card-b")).toHaveAttribute("data-selected", "false");
    expect(screen.getByTestId("card-c")).toHaveAttribute("data-selected", "false");
  });

  it("uses a custom className on the section when provided", () => {
    const { container } = render(
      <SelectionGrid
        items={items}
        selectedId={null}
        onSelect={vi.fn()}
        getId={(item) => item.id}
        renderCard={(item) => <span>{item.name}</span>}
        className="custom-class"
      />,
    );
    expect(container.querySelector("section")).toHaveClass("custom-class");
  });
});
