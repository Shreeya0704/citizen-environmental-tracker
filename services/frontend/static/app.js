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
      li.innerHTML = `<span class="badge">S3</span>
        <span>${item.last_modified}</span>
        <span class="meta">·</span>
        <span>${item.key}</span>
        <span class="meta">(${item.records ?? 'n/a'} recs)</span>`;
      ul.appendChild(li);
    });
  } catch (e) { console.error(e); }
}

async function loadTrend() {
  try {
    const param = 'pm25';
    const days = 7;
    const data = await fetchJSON(`/api/stats/param-trend?parameter=${encodeURIComponent(param)}&days=${days}`);
    const labels = (data.items || []).map(r => new Date(r.day).toISOString().slice(0,10));
    const values = (data.items || []).map(r => r.count || 0);
    const ctx = document.getElementById('paramChart');
    if (window._chart) window._chart.destroy();
    window._chart = new Chart(ctx, {
      type: 'line',
      data: { labels, datasets: [{ label: `Daily count: ${param}`, data: values }] },
      options: { responsive: true, scales: { y: { beginAtZero: true } } }
    });
  } catch (e) { console.error(e); }
}

async function loadObservations() {
  const days = document.getElementById('obsDays').value || 7;
  const country = document.getElementById('obsCountry').value.trim();
  const qs = new URLSearchParams({ days, limit: 10 });
  if (country) qs.set('country', country);
  try {
    const data = await fetchJSON(`/api/observations?${qs.toString()}`);
    const ul = document.getElementById('observations');
    ul.innerHTML = '';
    (data.items || []).forEach(o => {
      const when = o.observed_at ? new Date(o.observed_at).toISOString() : 'unknown time';
      const li = document.createElement('li');
      li.innerHTML = `
        <span class="badge">${o.quality_grade || 'obs'}</span>
        <strong>${o.common_name || o.scientific_name || '(unknown)'}</strong>
        <span class="meta">— ${o.place_city || ''} ${o.place_country ? '('+o.place_country+')' : ''}</span>
        <span class="meta">· ${when}</span>`;
      ul.appendChild(li);
    });
  } catch (e) { console.error(e); }
}

document.addEventListener('DOMContentLoaded', () => {
  document.getElementById('refresh').addEventListener('click', () => { loadIngestions(); loadTrend(); });
  document.getElementById('obsRefresh').addEventListener('click', () => { loadObservations(); });
  loadIngestions(); loadTrend(); loadObservations();
});
