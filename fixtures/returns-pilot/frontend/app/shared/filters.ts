export async function buildReturnsFilters(): Promise<string[]> {
  const response = await fetch("/api/returns/filters");
  if (!response.ok) {
    return [];
  }
  const payload = (await response.json()) as { filters: string[] };
  return payload.filters;
}
