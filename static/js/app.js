/* Remote JobFinder — Main Application JS */

// Translations
const TRANSLATIONS = {
    en: {
        title: 'Remote <span class="accent">JobFinder</span>',
        totalJobs: 'Total Jobs',
        highScore: 'High Score',
        avgScore: 'Avg Score',
        sources: 'Sources',
        search: 'Search jobs...',
        source: 'Source',
        category: 'Category',
        type: 'Type',
        minScore: 'Min Score',
        all: 'All',
        scrapeNow: 'Scan Now',
        scraping: 'Scanning...',
        loading: 'Loading jobs...',
        noJobs: 'No jobs found',
        noJobsSub: 'Try adjusting your filters or wait for the next scan.',
        newBadge: 'NEW',
        remote: 'Remote',
        footer: 'Remote JobFinder — Auto-scans every 6 hours',
        aiMl: 'AI/ML',
        automation: 'Automation',
        development: 'Development',
        integration: 'Integration',
        general: 'General',
        fullTime: 'Full-time',
        partTime: 'Part-time',
        contract: 'Contract',
        freelance: 'Freelance',
    },
    nl: {
        title: 'Remote <span class="accent">JobFinder</span>',
        totalJobs: 'Totaal',
        highScore: 'Hoge Score',
        avgScore: 'Gem. Score',
        sources: 'Bronnen',
        search: 'Zoek opdrachten...',
        source: 'Bron',
        category: 'Categorie',
        type: 'Type',
        minScore: 'Min Score',
        all: 'Alle',
        scrapeNow: 'Nu Scannen',
        scraping: 'Bezig...',
        loading: 'Opdrachten laden...',
        noJobs: 'Geen opdrachten gevonden',
        noJobsSub: 'Pas je filters aan of wacht op de volgende scan.',
        newBadge: 'NIEUW',
        remote: 'Remote',
        footer: 'Remote JobFinder — Scant automatisch elke 6 uur',
        aiMl: 'AI/ML',
        automation: 'Automatisering',
        development: 'Ontwikkeling',
        integration: 'Integratie',
        general: 'Algemeen',
        fullTime: 'Fulltime',
        partTime: 'Parttime',
        contract: 'Contract',
        freelance: 'Freelance',
    }
};

// State
let currentLang = localStorage.getItem('lang') || 'nl';
let currentTheme = localStorage.getItem('theme') || 'light';
let jobs = [];
let stats = {};

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
    document.getElementById('searchInput').addEventListener('input', debounce(loadJobs, 400));
    document.getElementById('filterSource').addEventListener('change', loadJobs);
    document.getElementById('filterCategory').addEventListener('change', loadJobs);
    document.getElementById('filterType').addEventListener('change', loadJobs);
    document.getElementById('scoreRange').addEventListener('input', (e) => {
        document.getElementById('scoreValue').textContent = e.target.value;
        debounce(loadJobs, 300)();
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
    const t = TRANSLATIONS[lang];
    const btn = document.getElementById('langToggle');
    // Show flag of current language
    btn.innerHTML = lang === 'nl'
        ? '<svg width="20" height="14" viewBox="0 0 9 6"><rect width="9" height="2" fill="#AE1C28"/><rect y="2" width="9" height="2" fill="#fff"/><rect y="4" width="9" height="2" fill="#21468B"/></svg>'
        : '<svg width="20" height="14" viewBox="0 0 60 30"><clipPath id="s"><rect width="60" height="30"/></clipPath><g clip-path="url(#s)"><rect width="60" height="30" fill="#012169"/><path d="M0 0L60 30M60 0L0 30" stroke="#fff" stroke-width="6"/><path d="M0 0L60 30M60 0L0 30" stroke="#C8102E" stroke-width="4" clip-path="url(#s)"/><path d="M30 0V30M0 15H60" stroke="#fff" stroke-width="10"/><path d="M30 0V30M0 15H60" stroke="#C8102E" stroke-width="6"/></g></svg>';

    document.getElementById('headerTitle').innerHTML = t.title;
    document.getElementById('labelTotal').textContent = t.totalJobs;
    document.getElementById('labelHigh').textContent = t.highScore;
    document.getElementById('labelAvg').textContent = t.avgScore;
    document.getElementById('labelSources').textContent = t.sources;
    document.getElementById('searchInput').placeholder = t.search;
    document.getElementById('labelSource').textContent = t.source;
    document.getElementById('labelCategory').textContent = t.category;
    document.getElementById('labelType').textContent = t.type;
    document.getElementById('labelMinScore').textContent = t.minScore;
    document.getElementById('btnScrapeText').textContent = t.scrapeNow;
    document.getElementById('footerText').textContent = t.footer;

    // Update "All" options
    document.querySelectorAll('.opt-all').forEach(el => el.textContent = t.all);
}

function t(key) {
    return TRANSLATIONS[currentLang][key] || key;
}

// API calls
async function loadJobs() {
    const container = document.getElementById('jobList');
    container.innerHTML = `<div class="loading"><div class="spinner"></div><p>${t('loading')}</p></div>`;

    const params = new URLSearchParams();
    const source = document.getElementById('filterSource').value;
    const category = document.getElementById('filterCategory').value;
    const jobType = document.getElementById('filterType').value;
    const minScore = document.getElementById('scoreRange').value;
    const search = document.getElementById('searchInput').value;

    if (source) params.append('source', source);
    if (category) params.append('category', category);
    if (jobType) params.append('job_type', jobType);
    if (minScore > 0) params.append('min_score', minScore);
    if (search) params.append('search', search);

    try {
        const resp = await fetch(`/api/jobs?${params}`);
        const data = await resp.json();
        jobs = data.jobs;
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
        // Wait a bit then refresh
        setTimeout(() => {
            loadJobs();
            loadStats();
            btn.disabled = false;
            textEl.textContent = t('scrapeNow');
        }, 5000);
    } catch (err) {
        btn.disabled = false;
        textEl.textContent = t('scrapeNow');
    }
}

// Render
function renderJobs() {
    const container = document.getElementById('jobList');

    if (!jobs.length) {
        container.innerHTML = `<div class="empty-state"><p>${t('noJobs')}</p><p>${t('noJobsSub')}</p></div>`;
        return;
    }

    container.innerHTML = jobs.map(job => {
        const scoreClass = job.score >= 50 ? 'high' : job.score >= 25 ? 'mid' : 'low';
        const cardClass = job.score >= 50 ? 'high-score' : job.score >= 25 ? 'mid-score' : 'low-score';

        return `
            <a href="${escapeHtml(job.url)}" target="_blank" rel="noopener" class="job-card ${cardClass}">
                <div class="score-badge ${scoreClass}">${job.score}</div>
                <div class="job-info">
                    <div class="job-title">${escapeHtml(job.title)}</div>
                    <div class="job-meta">
                        ${job.company ? `<span>\u{1F3E2} ${escapeHtml(job.company)}</span>` : ''}
                        <span>\u{1F4CD} ${escapeHtml(job.location || 'Remote')}</span>
                        ${job.posted_at ? `<span>\u{1F4C5} ${formatDate(job.posted_at)}</span>` : ''}
                    </div>
                </div>
                <div class="job-tags">
                    <span class="tag tag-source">${escapeHtml(job.source)}</span>
                    <span class="tag tag-category">${escapeHtml(job.category || 'General')}</span>
                    ${job.is_new ? `<span class="tag tag-new">${t('newBadge')}</span>` : ''}
                </div>
            </a>`;
    }).join('');
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

function debounce(fn, delay) {
    let timer;
    return (...args) => {
        clearTimeout(timer);
        timer = setTimeout(() => fn(...args), delay);
    };
}
