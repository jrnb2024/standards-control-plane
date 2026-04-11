import { resolveReturnsException } from "../../../backend/services/returns_exception_service";

async function fetchReturnsExceptions(): Promise<Array<{ id: string }>> {
  return [{ id: "ret-001" }];
}

export async function ExceptionsPage(): Promise<null> {
  const exceptions = await fetchReturnsExceptions();
  if (exceptions.length > 0) {
    await resolveReturnsException(exceptions[0].id);
  }
  return null;
}
