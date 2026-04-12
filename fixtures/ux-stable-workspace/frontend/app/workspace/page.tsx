const loadingMessage = "Loading returns workspace...";
const emptyMessage = "No items to review.";
const errorMessage = "Something went wrong. Try again.";

export function WorkspacePage(): string {
  return `
    <main>
      <nav aria-label="Breadcrumb">Returns / Workspace</nav>
      <h1>Returns Workspace</h1>
      <button type="button">Review next item</button>
      <section>${loadingMessage}</section>
      <section>${emptyMessage}</section>
      <section>${errorMessage}</section>
    </main>
  `;
}
