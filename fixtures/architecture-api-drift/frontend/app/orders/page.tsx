export async function OrdersPage(): Promise<null> {
  const response = await fetch("/api/orders");
  if (!response.ok) {
    return null;
  }
  return null;
}
