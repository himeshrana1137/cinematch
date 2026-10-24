export function formatTitle(title) {
  if (!title) return '';
  const match = title.match(/^(.*),\s*(The|A|An)$/i);
  if (match) {
    return `${match[2]} ${match[1]}`;
  }
  return title;
}

export function formatRuntime(mins) {
  if (!mins) return null;
  const h = Math.floor(mins / 60);
  const m = mins % 60;
  return h > 0 ? `${h}h ${m}m` : `${m}m`;
}
