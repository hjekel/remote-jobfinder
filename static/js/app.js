/* OpportunityFinder — Main Application JS */

// Translations
const TRANSLATIONS = {
    en: {
        title: 'Opportunity<span class="accent">Finder</span>',
        totalJobs: 'Total Jobs',
        highScore: 'High Score',
        avgScore: 'Avg Score',
        sources: 'Sources',
        search: 'Search opportunities...',
        source: 'Source',
        category: 'Category',
        location: 'Location',
        contract: 'Contract',
        region: 'Region',
        minScore: 'Min Score',
        sortScore: 'Score',
        sortSalary: 'Salary',
        sortDate: 'Newest',
        all: 'All',
        scrapeNow: 'Scan Now',
        scraping: 'Scanning...',
        loading: 'Loading opportunities...',
        noJobs: 'No opportunities found',
        noJobsSub: 'Try adjusting your filters or wait for the next scan.',
        newBadge: 'NEW',
        remote: 'Remote',
        footer: 'OpportunityFinder — Auto-scans every 6 hours',
        tabJobs: 'Opportunities',
        tabKanban: 'Kanban Board',
        scoreTitle: 'Score Explanation',
        scoreIntro: 'Each opportunity gets a relevance score of 0-100 based on keywords in the title and description:',
        scoreMax: 'Maximum score: 100 (capped)',
        legendHigh: '50+ = Highly relevant',
        legendMid: '25-49 = Relevant',
        legendLow: '<25 = Less relevant',
        colInterested: '⭐ Interested',
        colApplied: '📨 Applied',
        colInterview: '💬 Interview',
        colOffer: '🎯 Offer',
        colRejected: '❌ Rejected',
        addToBoard: 'Add to board',
        moveBtn: 'Move',
        deleteBtn: 'Remove',
        notesPlaceholder: 'Add notes...',
        kanbanEmpty: 'No cards yet. Click + on a job to add it here.',
    },
    nl: {
        title: 'Opportunity<span class="accent">Finder</span>',
        totalJobs: 'Totaal',
        highScore: 'Hoge Score',
        avgScore: 'Gem. Score',
        sources: 'Bronnen',
        search: 'Zoek opdrachten...',
        source: 'Bron',
        category: 'Categorie',
        location: 'Locatie',
        contract: 'Contract',
        region: 'Regio',
        minScore: 'Min Score',
        sortScore: 'Score',
        sortSalary: 'Salaris',
        sortDate: 'Nieuwste',
        all: 'Alle',
        scrapeNow: 'Nu Scannen',
        scraping: 'Bezig...',
        loading: 'Opdrachten laden...',
        noJobs: 'Geen opdrachten gevonden',
        noJobsSub: 'Pas je filters aan of wacht op de volgende scan.',
        newBadge: 'NIEUW',
        remote: 'Remote',
        footer: 'OpportunityFinder — Scant automatisch elke 6 uur',
        tabJobs: 'Opdrachten',
        tabKanban: 'Kanban Board',
        scoreTitle: 'Score Uitleg',
        scoreIntro: 'Elke opdracht krijgt een relevantie-score van 0-100 op basis van keywords in de titel en beschrijving:',
        scoreMax: 'Maximum score: 100 (afgekapt)',
        legendHigh: '50+ = Zeer relevant',
        legendMid: '25-49 = Relevant',
        legendLow: '<25 = Minder relevant',
        colInterested: '⭐ Interessant',
        colApplied: '📨 Gesolliciteerd',
        colInterview: '💬 Gesprek',
        colOffer: '🎯 Aanbod',
        colRejected: '❌ Afgewezen',
        addToBoard: 'Toevoegen aan board',
        moveBtn: 'Verplaats',
        deleteBtn: 'Verwijder',
        notesPlaceholder: 'Notities toevoegen...',
        kanbanEmpty: 'Nog geen kaarten. Klik + op een opdracht om hem hier toe te voegen.',
    }
};

// Kanban column order
const KANBAN_COLUMNS = ['interested', 'applied', 'interview', 'offer', 'rejected'];

// State
let currentLang = localStorage.getItem('lang') || 'nl';
let currentTheme = localStorage.getItem('theme') || 'light';
let currentView = 'jobs';
let currentSort = 'score';
let jobs = [];
let stats = {};
let kanbanCards = [];
let kanbanJobIds = new Set();

// Initialise
document.addEventListener('DOMContentLoaded', () => {
    applyTheme(currentTheme);
    applyLang(currentLang);
    loadStats();
    loadJobs();

    // Event listeners
    document.getElementById('themeToggle').addEventListener('click', toggleTheme);
    document.getElementById('langToggle').addEventListener('click', toggleLang);
    document.getElementById('btnScrape').addEventListener('click', triggerScrape);
    document.getElementById('btnScoreHelp').addEventListener('click', () => toggleModal(true));
    document.getElementById('closeScoreModal').addEventListener('click', () => toggleModal(false));
    document.getElementById('scoreModal').addEventListener('click', (e) => {
        if (e.target === e.currentTarget) toggleModal(false);
    });

    // Filters
    document.getElementById('searchInput').addEventListener('input', debounce(loadJobs, 400));
    document.getElementById('filterSource').addEventListener('change', loadJobs);
    document.getElementById('filterCategory').addEventListener('change', loadJobs);
    document.getElementById('filterLocation').addEventListener('change', loadJobs);
    document.getElementById('filterContract').addEventListener('change', loadJobs);
    document.getElementById('filterRegion').addEventListener('change', loadJobs);

    const scoreDebounced = debounce(loadJobs, 300);
    document.getElementById('scoreRange').addEventListener('input', (e) => {
        document.getElementById('scoreValue').textContent = e.target.value;
        scoreDebounced();
    });

    // Sort buttons
    document.querySelectorAll('.sort-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            currentSort = btn.dataset.sort;
            document.querySelectorAll('.sort-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            loadJobs();
        });
    });

    // Nav tabs
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', () => switchView(tab.dataset.view));
    });
});

// Theme
function toggleTheme() {
    currentTheme = currentTheme === 'light' ? 'dark' : 'light';
    applyTheme(currentTheme);
    localStorage.setItem('theme', currentTheme);
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    const btn = document.getElementById('themeToggle');
    btn.textContent = theme === 'light' ? '\u{263E}' : '\u{2600}';
}

// Language
function toggleLang() {
    currentLang = currentLang === 'en' ? 'nl' : 'en';
    applyLang(currentLang);
    localStorage.setItem('lang', currentLang);
}

function applyLang(lang) {
    const tr = TRANSLATIONS[lang];
    const btn = document.getElementById('langToggle');
    btn.innerHTML = lang === 'nl'
        ? '<svg width="20" height="14" viewBox="0 0 9 6"><rect width="9" height="2" fill="#AE1C28"/><rect y="2" width="9" height="2" fill="#fff"/><rect y="4" width="9" height="2" fill="#21468B"/></svg>'
        : '<svg width="20" height="14" viewBox="0 0 60 30"><clipPath id="s"><rect width="60" height="30"/></clipPath><g clip-path="url(#s)"><rect width="60" height="30" fill="#012169"/><path d="M0 0L60 30M60 0L0 30" stroke="#fff" stroke-width="6"/><path d="M0 0L60 30M60 0L0 30" stroke="#C8102E" stroke-width="4" clip-path="url(#s)"/><path d="M30 0V30M0 15H60" stroke="#fff" stroke-width="10"/><path d="M30 0V30M0 15H60" stroke="#C8102E" stroke-width="6"/></g></svg>';

    document.getElementById('headerTitle').innerHTML = tr.title;
    document.getElementById('labelTotal').textContent = tr.totalJobs;
    document.getElementById('labelHigh').textContent = tr.highScore;
    document.getElementById('labelAvg').textContent = tr.avgScore;
    document.getElementById('labelSources').textContent = tr.sources;
    document.getElementById('searchInput').placeholder = tr.search;
    document.getElementById('labelSource').textContent = tr.source;
    document.getElementById('labelCategory').textContent = tr.category;
    document.getElementById('labelLocation').textContent = tr.location;
    document.getElementById('labelContract').textContent = tr.contract;
    document.getElementById('labelRegion').textContent = tr.region;
    document.getElementById('labelMinScore').textContent = tr.minScore;
    document.getElementById('sortScoreText').textContent = tr.sortScore;
    document.getElementById('sortSalaryText').textContent = tr.sortSalary;
    document.getElementById('sortDateText').textContent = tr.sortDate;
    document.getElementById('btnScrapeText').textContent = tr.scrapeNow;
    document.getElementById('footerText').textContent = tr.footer;
    document.getElementById('tabJobsText').textContent = tr.tabJobs;
    document.getElementById('tabKanbanText').textContent = tr.tabKanban;

    // Modal
    document.getElementById('modalTitle').textContent = tr.scoreTitle;
    document.getElementById('scoreIntro').textContent = tr.scoreIntro;
    document.getElementById('scoreMax').textContent = tr.scoreMax;
    document.getElementById('legendHigh').textContent = tr.legendHigh;
    document.getElementById('legendMid').textContent = tr.legendMid;
    document.getElementById('legendLow').innerHTML = tr.legendLow;

    // Kanban columns
    document.getElementById('colInterested').textContent = tr.colInterested;
    document.getElementById('colApplied').textContent = tr.colApplied;
    document.getElementById('colInterview').textContent = tr.colInterview;
    document.getElementById('colOffer').textContent = tr.colOffer;
    document.getElementById('colRejected').textContent = tr.colRejected;

    // Update "All" options
    document.querySelectorAll('.opt-all').forEach(el => el.textContent = tr.all);
}

function t(key) {
    return TRANSLATIONS[currentLang][key] || key;
}

// View switching
function switchView(view) {
    currentView = view;
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.toggle('active', tab.dataset.view === view);
    });

    const jobsView = document.getElementById('jobList');
    const kanbanView = document.getElementById('kanbanView');
    const statsSection = document.getElementById('statsSection');
    const filtersSection = document.getElementById('filtersSection');

    if (view === 'jobs') {
        jobsView.style.display = '';
        kanbanView.style.display = 'none';
        statsSection.style.display = '';
        filtersSection.style.display = '';
    } else {
        jobsView.style.display = 'none';
        kanbanView.style.display = '';
        statsSection.style.display = 'none';
        filtersSection.style.display = 'none';
        loadKanban();
    }
}

// Score help modal
function toggleModal(show) {
    document.getElementById('scoreModal').style.display = show ? 'flex' : 'none';
}

// API calls
async function loadJobs() {
    const container = document.getElementById('jobList');
    container.innerHTML = `<div class="loading"><div class="spinner"></div><p>${t('loading')}</p></div>`;

    const params = new URLSearchParams();
    const source = document.getElementById('filterSource').value;
    const category = document.getElementById('filterCategory').value;
    const locType = document.getElementById('filterLocation').value;
    const contractType = document.getElementById('filterContract').value;
    const region = document.getElementById('filterRegion').value;
    const minScore = document.getElementById('scoreRange').value;
    const search = document.getElementById('searchInput').value;

    if (source) params.append('source', source);
    if (category) params.append('category', category);
    if (locType) params.append('location_type', locType);
    if (contractType) params.append('contract_type', contractType);
    if (region) params.append('region', region);
    if (currentSort !== 'score') params.append('sort_by', currentSort);
    if (minScore > 0) params.append('min_score', minScore);
    if (search) params.append('search', search);

    try {
        const resp = await fetch(`/api/jobs?${params}`);
        const data = await resp.json();
        jobs = data.jobs;

        // Also load kanban to know which jobs are on the board
        await loadKanbanIds();

        renderJobs();
    } catch (err) {
        container.innerHTML = `<div class="empty-state"><p>${t('noJobs')}</p><p>${t('noJobsSub')}</p></div>`;
    }
}

async function loadStats() {
    try {
        const resp = await fetch('/api/stats');
        stats = await resp.json();
        document.getElementById('statTotal').textContent = stats.total_jobs || 0;
        document.getElementById('statHigh').textContent = stats.high_score_jobs || 0;
        document.getElementById('statAvg').textContent = stats.avg_score || 0;
        document.getElementById('statSources').textContent = Object.keys(stats.by_source || {}).length;
    } catch (err) {
        console.error('Failed to load stats:', err);
    }
}

async function triggerScrape() {
    const btn = document.getElementById('btnScrape');
    const textEl = document.getElementById('btnScrapeText');
    btn.disabled = true;
    textEl.textContent = t('scraping');

    try {
        await fetch('/api/scrape', { method: 'POST' });
        setTimeout(() => {
            loadJobs();
            loadStats();
            btn.disabled = false;
            textEl.textContent = t('scrapeNow');
        }, 8000);
    } catch (err) {
        btn.disabled = false;
        textEl.textContent = t('scrapeNow');
    }
}

// Kanban
async function loadKanbanIds() {
    try {
        const resp = await fetch('/api/kanban');
        const data = await resp.json();
        kanbanCards = data.cards;
        kanbanJobIds = new Set(kanbanCards.map(c => c.job_id));
    } catch (err) {
        console.error('Failed to load kanban:', err);
    }
}

async function loadKanban() {
    await loadKanbanIds();
    renderKanban();
}

async function addToKanban(jobId) {
    try {
        await fetch('/api/kanban', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ job_id: jobId, column: 'interested' })
        });
        kanbanJobIds.add(jobId);

        // Update the button in job list
        const btn = document.querySelector(`[data-kanban-job="${jobId}"]`);
        if (btn) {
            btn.classList.add('added');
            btn.textContent = '\u{2714}';
        }

        // Reload kanban data
        await loadKanbanIds();
    } catch (err) {
        console.error('Failed to add to kanban:', err);
    }
}

async function moveKanbanCard(cardId, newColumn) {
    try {
        await fetch(`/api/kanban/${cardId}/move`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ column: newColumn })
        });
        await loadKanban();
    } catch (err) {
        console.error('Failed to move card:', err);
    }
}

async function saveKanbanNotes(cardId, notes) {
    try {
        await fetch(`/api/kanban/${cardId}/notes`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes })
        });
    } catch (err) {
        console.error('Failed to save notes:', err);
    }
}

async function deleteKanbanCard(cardId) {
    try {
        await fetch(`/api/kanban/${cardId}`, { method: 'DELETE' });
        await loadKanban();
        // Also refresh job list buttons
        await loadKanbanIds();
        renderJobs();
    } catch (err) {
        console.error('Failed to delete card:', err);
    }
}

// Render jobs
function renderJobs() {
    const container = document.getElementById('jobList');

    if (!jobs.length) {
        container.innerHTML = `<div class="empty-state"><p>${t('noJobs')}</p><p>${t('noJobsSub')}</p></div>`;
        return;
    }

    container.innerHTML = jobs.map(job => {
        const scoreClass = job.score >= 50 ? 'high' : job.score >= 25 ? 'mid' : 'low';
        const cardClass = job.score >= 50 ? 'high-score' : job.score >= 25 ? 'mid-score' : 'low-score';
        const onBoard = kanbanJobIds.has(job.id);
        const contractLabel = job.contract_type && job.contract_type !== 'unknown' ? job.contract_type : '';
        const locLabel = job.location_type && job.location_type !== 'remote' ? job.location_type : '';
        const regionLabel = job.region && job.region !== 'international' ? job.region : '';
        const salaryStr = formatSalary(job.salary_min, job.salary_max);
        const techTags = (job.tags || '').split(',').map(t => t.trim()).filter(t => t).slice(0, 4);

        return `
            <div class="job-card ${cardClass}">
                <div class="score-badge ${scoreClass}">${job.score}</div>
                <a href="${escapeHtml(job.url)}" target="_blank" rel="noopener" class="job-info">
                    <div class="job-title">${escapeHtml(job.title)}</div>
                    <div class="job-meta">
                        ${job.company ? `<span>\u{1F3E2} ${escapeHtml(job.company)}</span>` : ''}
                        ${salaryStr ? `<span class="salary-label">\u{1F525} ${salaryStr}</span>` : ''}
                        ${job.posted_at ? `<span>\u{1F4C5} ${formatRelativeDate(job.posted_at)}</span>` : ''}
                    </div>
                </a>
                <div class="job-tags">
                    <span class="tag tag-source">${escapeHtml(job.source)}</span>
                    <span class="tag tag-category">${escapeHtml(job.category || 'General')}</span>
                    ${contractLabel ? `<span class="tag tag-contract">${escapeHtml(contractLabel)}</span>` : ''}
                    ${locLabel ? `<span class="tag tag-location">${escapeHtml(locLabel)}</span>` : ''}
                    ${regionLabel ? `<span class="tag tag-region">${escapeHtml(regionLabel)}</span>` : ''}
                    ${techTags.map(tag => `<span class="tag tag-tech">${escapeHtml(tag)}</span>`).join('')}
                    ${job.is_new ? `<span class="tag tag-new">${t('newBadge')}</span>` : ''}
                </div>
                <button class="btn-kanban ${onBoard ? 'added' : ''}"
                        data-kanban-job="${job.id}"
                        onclick="event.stopPropagation(); ${onBoard ? '' : `addToKanban('${job.id}')`}"
                        title="${t('addToBoard')}">
                    ${onBoard ? '\u{2714}' : '+'}
                </button>
            </div>`;
    }).join('');
}

// Render Kanban board
function renderKanban() {
    const columnMap = {};
    KANBAN_COLUMNS.forEach(col => { columnMap[col] = []; });

    kanbanCards.forEach(card => {
        if (columnMap[card.column_name]) {
            columnMap[card.column_name].push(card);
        }
    });

    KANBAN_COLUMNS.forEach(col => {
        const container = document.getElementById('cards' + col.charAt(0).toUpperCase() + col.slice(1));
        const countEl = document.getElementById('count' + col.charAt(0).toUpperCase() + col.slice(1));
        const cards = columnMap[col];

        countEl.textContent = cards.length;

        if (!cards.length) {
            container.innerHTML = `<div class="empty-state" style="padding:1rem;font-size:0.75rem;">${t('kanbanEmpty')}</div>`;
            return;
        }

        container.innerHTML = cards.map(card => {
            const scoreClass = card.score >= 50 ? 'high' : card.score >= 25 ? 'mid' : 'low';
            const scoreColor = card.score >= 50 ? 'var(--score-high)' : card.score >= 25 ? 'var(--planbit-oranje)' : 'var(--text-muted)';
            const otherColumns = KANBAN_COLUMNS.filter(c => c !== col);

            return `
                <div class="kanban-card">
                    <div class="kanban-card-title">
                        <a href="${escapeHtml(card.url)}" target="_blank" rel="noopener">${escapeHtml(card.title)}</a>
                    </div>
                    <div class="kanban-card-meta">
                        ${card.company ? escapeHtml(card.company) + ' \u{00B7} ' : ''}${escapeHtml(card.source)}
                        ${card.contract_type && card.contract_type !== 'unknown' ? ' \u{00B7} ' + escapeHtml(card.contract_type) : ''}
                    </div>
                    <span class="kanban-card-score" style="background:${scoreColor}">${card.score}</span>
                    ${card.notes ? `<div class="kanban-card-notes">${escapeHtml(card.notes)}</div>` : ''}
                    <div class="kanban-card-actions">
                        ${otherColumns.map(c =>
                            `<button class="kanban-btn" onclick="moveKanbanCard(${card.id}, '${c}')">\u{2192} ${getColumnLabel(c)}</button>`
                        ).join('')}
                        <button class="kanban-btn" onclick="toggleNotes(${card.id})">📝</button>
                        <button class="kanban-btn delete" onclick="deleteKanbanCard(${card.id})">✕</button>
                    </div>
                    <div id="notes-${card.id}" style="display:none;">
                        <textarea class="kanban-notes-input" placeholder="${t('notesPlaceholder')}"
                                  onblur="saveKanbanNotes(${card.id}, this.value)">${escapeHtml(card.notes || '')}</textarea>
                    </div>
                </div>`;
        }).join('');
    });
}

function getColumnLabel(col) {
    const labels = {
        interested: '⭐',
        applied: '📨',
        interview: '💬',
        offer: '🎯',
        rejected: '❌'
    };
    return labels[col] || col;
}

function toggleNotes(cardId) {
    const el = document.getElementById(`notes-${cardId}`);
    el.style.display = el.style.display === 'none' ? 'block' : 'none';
    if (el.style.display === 'block') {
        el.querySelector('textarea').focus();
    }
}

// Helpers
function escapeHtml(str) {
    if (!str) return '';
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function formatDate(dateStr) {
    if (!dateStr) return '';
    try {
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return dateStr.substring(0, 10);
        return d.toLocaleDateString(currentLang === 'nl' ? 'nl-NL' : 'en-GB', {
            day: 'numeric',
            month: 'short',
        });
    } catch {
        return dateStr.substring(0, 10);
    }
}

function formatRelativeDate(dateStr) {
    if (!dateStr) return '';
    try {
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return dateStr.substring(0, 10);
        const now = new Date();
        const diffMs = now - d;
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 60) return diffMins <= 1 ? 'just now' : `${diffMins}m`;
        if (diffHours < 24) return `${diffHours}h`;
        if (diffDays < 30) return `${diffDays}d`;
        if (diffDays < 365) return `${Math.floor(diffDays / 30)}mo`;
        return `${Math.floor(diffDays / 365)}y`;
    } catch {
        return dateStr.substring(0, 10);
    }
}

function formatSalary(min, max) {
    if (!max && !min) return '';
    const fmt = (n) => {
        if (n >= 1000) return `$${Math.round(n / 1000)}k`;
        return `$${n}`;
    };
    if (min && max && min !== max) return `${fmt(min)} - ${fmt(max)}`;
    if (max) return fmt(max);
    if (min) return `${fmt(min)}+`;
    return '';
}

function debounce(fn, delay) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), delay);
    };
}
