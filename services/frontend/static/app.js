async function fetchJSON(url) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return await res.json();
}

async function loadIngestions() {
  try {
    const data = await fetchJSON('/api/ingestions/latest?n=5');
    const ul = document.getElementById('ingestions');
    ul.innerHTML = '';
    (data.items || []).forEach(item => {
      const li = document.createElement('li');
      li.textContent = `${item.last_modified} — ${item.key} (${item.records ?? 'n/a'} recs)`;
      ul.appendChild(li);
    });
  } catch (e) {
    console.error(e);
  }
}

async function loadChart() {
  try {
    const data = await fetchJSON('/api/measurements?limit=50');
    const counts = {};
    (data.items || []).forEach(r => {
      const p = r.parameter || 'unknown';
      counts[p] = (counts[p] || 0) + 1;
    });
    const labels = Object.keys(counts);
    const values = labels.map(l => counts[l]);

    const ctx = document.getElementById('paramChart');
    if (window._chart) window._chart.destroy();
    window._chart = new Chart(ctx, {
      type: 'bar',
      data: { labels, datasets: [{ label: 'Rows', data: values }] },
      options: { responsive: true, plugins: { legend: { display: false } } }
    });
  } catch (e) {
    console.error(e);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('refresh').addEventListener('click', () => {
    loadIngestions(); loadChart();
  });
  loadIngestions(); loadChart();
});
