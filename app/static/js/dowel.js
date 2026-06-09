/* Dowel — vanilla JS */

// ── Countdown timers ──────────────────────────────────────────────────────────

function formatCountdown(dueAt) {
  const now = new Date();
  const due = new Date(dueAt + 'Z'); // treat stored value as UTC
  const diffMs = due - now;
  const diffSec = Math.floor(diffMs / 1000);

  if (diffSec <= 0) {
    const overdueSec = Math.abs(diffSec);
    const days = Math.floor(overdueSec / 86400);
    const hours = Math.floor((overdueSec % 86400) / 3600);
    if (days > 0) return { text: `OVERDUE by ${days}d ${hours}h`, overdue: true };
    return { text: `OVERDUE by ${hours}h`, overdue: true };
  }

  const days = Math.floor(diffSec / 86400);
  const hours = Math.floor((diffSec % 86400) / 3600);
  const mins = Math.floor((diffSec % 3600) / 60);

  if (days > 0) return { text: `Due in ${days}d ${hours}h`, overdue: false };
  if (hours > 0) return { text: `Due in ${hours}h ${mins}m`, overdue: false };
  return { text: `Due in ${mins}m`, overdue: false };
}

function updateCountdowns() {
  document.querySelectorAll('[data-due-at]').forEach(el => {
    const dueAt = el.getAttribute('data-due-at');
    if (!dueAt) return;
    const result = formatCountdown(dueAt);
    el.textContent = result.text;
    if (result.overdue) {
      el.classList.remove('bg-warning', 'text-dark');
      el.classList.add('bg-danger', 'text-white', 'countdown-overdue');
      // Also update parent alert if present
      const alert = document.getElementById('checkoutAlert');
      if (alert) {
        alert.classList.remove('alert-warning');
        alert.classList.add('alert-danger', 'overdue');
      }
    } else {
      el.classList.remove('bg-danger', 'text-white', 'countdown-overdue');
      el.classList.add('bg-warning', 'text-dark');
    }
  });
}

// Run immediately and then every 60 seconds
updateCountdowns();
setInterval(updateCountdowns, 60000);


// ── Inventory search/filter ──────────────────────────────────────────────────

(function () {
  const searchInput = document.getElementById('searchInput');
  const categoryPills = document.getElementById('categoryPills');
  const availFilter = document.getElementById('availabilityFilter');
  const toolGrid = document.getElementById('toolGrid');
  const noResults = document.getElementById('noResults');

  if (!toolGrid) return;

  let activeCategory = 'all';
  let activeAvail = 'all';
  let searchText = '';

  function applyFilters() {
    const cards = toolGrid.querySelectorAll('.tool-card');
    let visible = 0;

    cards.forEach(card => {
      const name = card.getAttribute('data-name') || '';
      const cat = card.getAttribute('data-category') || '';
      const avail = card.getAttribute('data-available');

      const matchSearch = !searchText || name.includes(searchText.toLowerCase());
      const matchCat = activeCategory === 'all' || cat === activeCategory;
      const matchAvail =
        activeAvail === 'all' ||
        (activeAvail === 'available' && avail === 'true') ||
        (activeAvail === 'checkedout' && avail === 'false');

      const show = matchSearch && matchCat && matchAvail;
      card.style.display = show ? '' : 'none';
      if (show) visible++;
    });

    if (noResults) noResults.style.display = visible === 0 ? '' : 'none';
  }

  if (searchInput) {
    searchInput.addEventListener('input', function () {
      searchText = this.value.trim();
      applyFilters();
    });
  }

  if (categoryPills) {
    categoryPills.addEventListener('click', function (e) {
      const btn = e.target.closest('[data-category]');
      if (!btn) return;
      categoryPills.querySelectorAll('button').forEach(b => {
        b.classList.remove('btn-dark', 'active');
        b.classList.add('btn-outline-secondary');
      });
      btn.classList.remove('btn-outline-secondary');
      btn.classList.add('btn-dark', 'active');
      activeCategory = btn.getAttribute('data-category');
      applyFilters();
    });
  }

  if (availFilter) {
    availFilter.addEventListener('click', function (e) {
      const btn = e.target.closest('[data-avail]');
      if (!btn) return;
      availFilter.querySelectorAll('button').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      activeAvail = btn.getAttribute('data-avail');
      applyFilters();
    });
  }
})();


// ── Dynamic spec rows ─────────────────────────────────────────────────────────

(function () {
  const addBtn = document.getElementById('addSpecBtn');
  const container = document.getElementById('specsContainer');
  if (!addBtn || !container) return;

  function addSpecRow(key, val) {
    const row = document.createElement('div');
    row.className = 'row g-2 mb-2 spec-row';
    row.innerHTML = `
      <div class="col-5"><input type="text" name="spec_key" class="form-control form-control-sm" placeholder="Key" value="${key || ''}"></div>
      <div class="col-5"><input type="text" name="spec_val" class="form-control form-control-sm" placeholder="Value" value="${val || ''}"></div>
      <div class="col-2"><button type="button" class="btn btn-outline-danger btn-sm remove-spec"><i class="bi bi-x"></i></button></div>
    `;
    container.appendChild(row);
    row.querySelector('.remove-spec').addEventListener('click', () => row.remove());
  }

  // Wire up any existing remove buttons
  container.querySelectorAll('.remove-spec').forEach(btn => {
    btn.addEventListener('click', () => btn.closest('.spec-row').remove());
  });

  addBtn.addEventListener('click', () => addSpecRow());
})();
