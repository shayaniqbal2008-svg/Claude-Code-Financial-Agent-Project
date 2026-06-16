async function loadReportDates() {
  try {
    const res = await fetch('/api/reports');
    if (!res.ok) {
      document.getElementById('report-content').innerHTML = '<p style="color:var(--red)">Failed to load reports.</p>';
      return;
    }
    const dates = await res.json();
    const sel = document.getElementById('date-select');
    sel.innerHTML = dates.map(d => `<option value="${d}">${d}</option>`).join('');
    if (dates.length) loadReport(dates[0]);
    else document.getElementById('report-content').innerHTML =
      '<p class="empty-state">No reports yet. Run the agent to generate your first report.</p>';
  } catch (e) {
    console.error('Failed to load report dates:', e);
  }
}

async function loadReport(date) {
  try {
    const res = await fetch(`/api/report/${date}`);
    if (!res.ok) {
      document.getElementById('report-content').innerHTML =
        '<p class="empty-state">No report for this date.</p>';
      return;
    }
    const report = await res.json();
    renderReport(report);
    updateStatusDot(report);
    document.getElementById('report-date').textContent = report.date;
  } catch (e) {
    console.error('Failed to load report:', e);
  }
}

function updateStatusDot(report) {
  const dot = document.getElementById('status-dot');
  const today = new Date().toLocaleDateString('en-CA');
  dot.className = 'status-dot ' + (report.date === today ? 'fresh' : 'stale');
}

function esc(str) {
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function badge(urgency) {
  return `<span class="urgency-badge ${esc(urgency.toLowerCase())}">${esc(urgency.toUpperCase())}</span>`;
}

function section(title, count, body, openByDefault = false) {
  const openClass = openByDefault ? ' open' : '';
  return `<div class="section">
    <div class="section-header${openClass}" onclick="toggleSection(this)">
      <h2>${esc(title)}</h2>
      <span class="count">${count}</span>
      <i class="chevron">›</i>
    </div>
    <div class="section-body${openClass}">${body}</div>
  </div>`;
}

function toggleSection(header) {
  header.classList.toggle('open');
  header.nextElementSibling.classList.toggle('open');
}

function renderReport(report) {
  const sell = report.sell_alerts || [];
  const buy = report.buy_candidates || [];
  const portfolio = report.portfolio_review || [];
  const news = report.news_briefing || [];
  const alerts = report.market_political_alerts || [];

  const sellHtml = sell.length
    ? sell.map(a => `<div class="alert-card ${esc(a.urgency)}">
        <div style="display:flex;align-items:center;gap:8px">
          <span class="ticker">${esc(a.ticker)}</span>
          ${badge(a.urgency)}
        </div>
        <div class="reason">${esc(a.reason)}</div>
      </div>`).join('')
    : '<p class="empty-state">No sell alerts today.</p>';

  const buyHtml = buy.length
    ? buy.map(c => `<div class="candidate-card">
        <span class="ticker">${esc(c.ticker)}</span>
        <div class="reason">${esc(c.rationale)}</div>
      </div>`).join('')
    : '<p class="empty-state">No qualifying candidates today.</p>';

  const portfolioHtml = portfolio.length
    ? `<table class="portfolio-table">
        <tr><th>Ticker</th><th>Grade</th><th>Summary</th></tr>
        ${portfolio.map(h => `<tr>
          <td class="ticker">${esc(h.ticker)}</td>
          <td class="grade-${esc(h.grade)}">${esc(h.grade)}</td>
          <td style="font-size:.85rem;color:var(--text-muted)">${esc(h.summary || '')}</td>
        </tr>`).join('')}
      </table>`
    : '<p class="empty-state">No holdings reviewed.</p>';

  const newsHtml = news.length
    ? news.map(n => `<div class="news-card">
        <strong>${esc(n.headline)}</strong>
        <div class="reason">${esc(n.impact)}</div>
        <div style="font-size:.8rem;color:var(--text-muted);margin-top:4px">
          ${(n.tickers_affected || []).map(esc).join(', ')}
        </div>
      </div>`).join('')
    : '<p class="empty-state">No significant news.</p>';

  const alertsHtml = alerts.length
    ? alerts.map(a => `<div class="alert-card ${esc(a.urgency)}">
        <div style="display:flex;align-items:center;gap:8px">
          ${badge(a.urgency)}
          <strong>${esc(a.event)}</strong>
        </div>
        <div class="reason">${esc(a.market_impact)}</div>
      </div>`).join('')
    : '<p class="empty-state">No significant alerts.</p>';

  document.getElementById('report-content').innerHTML = [
    section('⚠ Sell Alerts', sell.length, sellHtml, true),
    section('✓ Buy Candidates', buy.length, buyHtml, true),
    section('Portfolio Review', portfolio.length, portfolioHtml, false),
    section('News Briefing', news.length, newsHtml, false),
    section('Market & Political Alerts', alerts.length, alertsHtml, false),
  ].join('');
}

async function refreshPortfolio() {
  try {
    const res = await fetch('/api/portfolio/live');
    if (!res.ok) return;
    const data = await res.json();

    const tbody = document.getElementById('portfolio-rows');
    tbody.innerHTML = (data.holdings || []).map(h => `
      <tr>
        <td class="ticker">${esc(h.ticker)}</td>
        <td class="grade-${esc(h.grade || '')}">${esc(h.grade || '?')}</td>
        <td>${h.current_price != null ? '$' + Number(h.current_price).toFixed(2) : '—'}</td>
      </tr>
    `).join('');

    const idx = data.indices || {};
    document.getElementById('sp500').textContent =
      idx['S&P 500'] != null ? idx['S&P 500'] : '—';
    document.getElementById('nasdaq').textContent =
      idx['NASDAQ'] != null ? idx['NASDAQ'] : '—';
    document.getElementById('vix').textContent =
      idx['VIX'] != null ? idx['VIX'] : '—';
    document.getElementById('last-refresh').textContent =
      'Updated ' + new Date().toLocaleTimeString();
  } catch (e) {
    console.error('Portfolio refresh failed:', e);
  }
}

document.getElementById('date-select').addEventListener('change', e => loadReport(e.target.value));

loadReportDates();
refreshPortfolio();
setInterval(refreshPortfolio, 60000);
