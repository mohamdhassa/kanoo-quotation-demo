(() => {
  const d = window.dashboardData || {};
  const s = window.statusData || { approved: 0, rejected: 0 };
  const common = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    plugins: { legend: { position: 'bottom' } }
  };
  const make = (id, config) => {
    const el = document.getElementById(id);
    if (el && window.Chart) new Chart(el, config);
  };

  make('advisorChart', { type: 'bar', data: { labels: d.advisor_labels || [], datasets: [
    { label: 'Total', data: d.advisor_totals || [] },
    { label: 'Approved', data: d.advisor_approved || [] }
  ] }, options: common });

  make('advisorRateChart', { type: 'bar', data: { labels: d.advisor_labels || [], datasets: [
    { label: 'Approval %', data: d.advisor_rates || [] }
  ] }, options: { ...common, scales: { y: { beginAtZero: true, max: 100 } } } });

  make('advisorValueChart', { type: 'bar', data: { labels: d.advisor_labels || [], datasets: [
    { label: 'Quoted BHD', data: d.advisor_quoted_values || [] },
    { label: 'Approved BHD', data: d.advisor_approved_values || [] }
  ] }, options: common });

  make('statusChart', { type: 'doughnut', data: { labels: ['Approved', 'Rejected'], datasets: [{ data: [s.approved, s.rejected] }] }, options: common });
  make('vehicleChart', { type: 'bar', data: { labels: d.vehicle_labels || [], datasets: [{ label: 'Quotations', data: d.vehicle_values || [] }] }, options: { ...common, indexAxis: 'y' } });
  make('serviceChart', { type: 'bar', data: { labels: d.service_labels || [], datasets: [{ label: 'Quotations', data: d.service_values || [] }] }, options: { ...common, indexAxis: 'y' } });
  make('damageChart', { type: 'bar', data: { labels: d.damage_labels || [], datasets: [{ label: 'Quotations', data: d.damage_values || [] }] }, options: { ...common, indexAxis: 'y' } });
  make('refusalChart', { type: 'bar', data: { labels: d.refusal_labels || [], datasets: [{ label: 'Rejected', data: d.refusal_values || [] }] }, options: { ...common, indexAxis: 'y' } });
  make('timeSeriesChart', { type: 'line', data: { labels: d.daily_labels || [], datasets: [
    { label: 'Total', data: d.daily_totals || [], tension: 0.2, fill: false },
    { label: 'Approved', data: d.daily_approved || [], tension: 0.2, fill: false },
    { label: 'Rejected', data: d.daily_rejected || [], tension: 0.2, fill: false }
  ] }, options: { ...common, scales: { y: { beginAtZero: true, ticks: { precision: 0 } } } } });

  make('trendChart', { type: 'line', data: { labels: d.month_labels || [], datasets: [{ label: 'Quotations', data: d.month_values || [], tension: 0.25, fill: false }] }, options: common });
  make('hourChart', { type: 'line', data: { labels: d.hour_labels || [], datasets: [{ label: 'Quotations', data: d.hour_values || [], tension: 0.25 }] }, options: common });
  make('weekdayChart', { type: 'bar', data: { labels: d.weekday_labels || [], datasets: [{ label: 'Quotations', data: d.weekday_values || [] }] }, options: common });
})();

// Keep the manager view current without requiring manual refresh.
setInterval(() => {
  if (document.visibilityState === 'visible' && !document.querySelector('input:focus, select:focus')) {
    window.location.reload();
  }
}, 60000);
