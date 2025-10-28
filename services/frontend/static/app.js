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

async function loadDailyTrend() {
  try {
    const param = 'pm25';
    const days = 7;
    const data = await fetchJSON(`/api/stats/param-trend?parameter=${encodeURIComponent(param)}&days=${days}`);
    const labels = (data.items || []).map(r => new Date(r.day).toISOString().slice(0, 10));
    const values = (data.items || []).map(r => r.count || 0);
    const ctx = document.getElementById('paramChart');
    if (window._chart) window._chart.destroy();
    window._chart = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [{ label: `Daily count (${param})`, data: values }],
      },
      options: {
        responsive: true,
        scales: {
          y: { beginAtZero: true },
        },
      },
    });
  } catch (e) {
    console.error(e);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('refresh').addEventListener('click', () => {
    loadIngestions();
    loadDailyTrend();
  });
  loadIngestions();
  loadDailyTrend();
});
