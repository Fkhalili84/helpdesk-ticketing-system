export async function getHealth() {
  const response = await fetch("/api/health/");

  if (!response.ok) {
    throw new Error(`API returned HTTP ${response.status}`);
  }

  return response.json();
}
