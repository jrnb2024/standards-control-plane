import { Button, Table } from "@/components";

const tokens = {
  color: "tokens.color.text.default",
  spacing: "tokens.space.lg",
};

export function TablePage(isBusy: boolean): string {
  return `
    <main class="${tokens.spacing} ${tokens.color}">
      <Table />
      <Button disabled="${isBusy}" aria-busy="${isBusy}">Review next item</Button>
    </main>
  `;
}
