/* jshint esversion: 11 */

/* ============================================================
  script.js — Portfolio JavaScript
  ============================================================ */

// ── Theme Toggle ─────────────────────────────────────────────
(function initTheme() {
  const saved = localStorage.getItem('theme') || 'dark';
  document.documentElement.setAttribute('data-theme', saved);
})();

function toggleTheme() {
  const root = document.documentElement;
  const current = root.getAttribute('data-theme') || 'dark';
  const next = current === 'dark' ? 'light' : 'dark';
  root.setAttribute('data-theme', next);
  localStorage.setItem('theme', next);
  updateThemeIcon(next);
}

function updateThemeIcon(theme) {
  const btn = document.getElementById('theme-toggle');
  if (!btn) return;
  const sunIcon  = btn.querySelector('.icon-sun');
  const moonIcon = btn.querySelector('.icon-moon');
  if (!sunIcon || !moonIcon) return;
  if (theme === 'dark') {
    sunIcon.style.display  = 'block';
    moonIcon.style.display = 'none';
  } else {
    sunIcon.style.display  = 'none';
    moonIcon.style.display = 'block';
  }
}

// ── Mobile Navigation ─────────────────────────────────────────
function initMobileNav() {
  const hamburger = document.querySelector('.nav__hamburger');
  const drawer    = document.querySelector('.nav__mobile');
  if (!hamburger || !drawer) return;

  hamburger.addEventListener('click', () => {
    const open = hamburger.classList.toggle('open');
    drawer.classList.toggle('open', open);
    document.body.style.overflow = open ? 'hidden' : '';
  });

  // Close on link click
  drawer.querySelectorAll('.nav__link').forEach(link => {
    link.addEventListener('click', () => {
      hamburger.classList.remove('open');
      drawer.classList.remove('open');
      document.body.style.overflow = '';
    });
  });
}

// ── Scroll Reveal ─────────────────────────────────────────────
function initScrollReveal() {
  const items = document.querySelectorAll('.fade-in');
  if (!items.length) return;

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        observer.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  items.forEach(el => observer.observe(el));
}

// ── Active Nav Link ───────────────────────────────────────────
function initActiveNav() {
  const path = window.location.pathname;
  const isProjectsSection = /\/projects\/(rotoscoping|solar-system)\.html$/.test(path) || path.endsWith('projects.html');
  document.querySelectorAll('.nav__link').forEach(link => {
    const href = link.getAttribute('href');
    if (!href) return;
    if (
      (path.endsWith(href)) ||
      (path.includes(href) && href !== '/' && href !== 'index.html')
    ) {
      link.classList.add('active');
    }
    if (isProjectsSection && href.includes('projects.html')) {
      link.classList.add('active');
    }
    // Index page
    if ((path === '/' || path.endsWith('index.html') || path.endsWith('/')) && (href === 'index.html' || href === './index.html')) {
      link.classList.add('active');
    }
  });
}

// ── Stars Canvas (Solar System Page) ─────────────────────────
function initStars() {
  const canvas = document.getElementById('stars-canvas');
  if (!canvas) return;

  const ctx = canvas.getContext('2d');
  let stars = [];
  let currentPointer = { x: 0, y: 0 };
  let targetPointer = { x: 0, y: 0 };

  function resize() {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    currentPointer = { x: canvas.width / 2, y: canvas.height / 2 };
    targetPointer = { x: canvas.width / 2, y: canvas.height / 2 };
    generateStars();
  }

  function generateStars() {
    stars = [];
    const count = Math.floor((canvas.width * canvas.height) / 4000);
    for (let i = 0; i < count; i++) {
      stars.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        r: Math.random() * 1.2 + 0.2,
        o: Math.random() * 0.6 + 0.2,
        speed: Math.random() * 0.3 + 0.05,
        phase: Math.random() * Math.PI * 2,
        depth: Math.random() * 0.85 + 0.15,
      });
    }
  }

  function setPointerFromEvent(event) {
    targetPointer = {
      x: event.clientX,
      y: event.clientY,
    };
  }

  function getStarColor() {
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
    return isDark ? 'rgba(232, 228, 220' : 'rgba(40, 40, 60';
  }

  function drawStars(t) {
    const driftX = ((currentPointer.x - canvas.width / 2) / canvas.width) * 70;
    const driftY = ((currentPointer.y - canvas.height / 2) / canvas.height) * 70;
    const starColor = getStarColor();

    ctx.clearRect(0, 0, canvas.width, canvas.height);
    stars.forEach((s) => {
      const flicker = s.o + Math.sin(t * s.speed + s.phase) * 0.15;
      const x = (s.x + driftX * s.depth + canvas.width) % canvas.width;
      const y = (s.y + driftY * s.depth + canvas.height) % canvas.height;

      ctx.beginPath();
      ctx.arc(x, y, s.r, 0, Math.PI * 2);
      ctx.fillStyle = `${starColor}, ${Math.max(0, Math.min(1, flicker))})`;
      ctx.fill();
    });
  }

  function animate(t) {
    currentPointer.x += (targetPointer.x - currentPointer.x) * 0.08;
    currentPointer.y += (targetPointer.y - currentPointer.y) * 0.08;
    drawStars(t * 0.001);
    requestAnimationFrame(animate);
  }

  resize();
  window.addEventListener('resize', resize);
  window.addEventListener('mousemove', setPointerFromEvent);
  window.addEventListener('pointerleave', () => {
    targetPointer = { x: canvas.width / 2, y: canvas.height / 2 };
  });
  
  // Update stars when theme changes
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      // Regenerate stars to update their colors for new theme
      setTimeout(generateStars, 10);
    });
  }
  
  animate(0);
}

// ── Age Calculator (Solar System Page) ───────────────────────
const ORBITAL_PERIODS = {
  Mercury: 0.2408467,
  Venus:   0.6151973,
  Earth:   1.0,
  Mars:    1.8808476,
  Jupiter: 11.862615,
  Saturn:  29.447498,
  Uranus:  84.016846,
  Neptune: 164.79132,
  Pluto:   247.92065,
};

function computePlanetAges(earthYears) {
  const result = {};
  for (const [planet, period] of Object.entries(ORBITAL_PERIODS)) {
    result[planet] = (earthYears / period).toFixed(2);
  }
  return result;
}

function initAgeCalculator() {
  const form = document.getElementById('age-calc-form');
  if (!form) return;

  const ageInput  = document.getElementById('calc-age');
  const bdayInput = document.getElementById('calc-bday');
  const modeAgeBtn = document.getElementById('mode-age-btn');
  const modeBdayBtn = document.getElementById('mode-bday-btn');
  const ageError = document.getElementById('calc-age-error');
  const bdayError = document.getElementById('calc-bday-error');

  if (!ageInput || !bdayInput) return;

  const today = new Date();
  const maxBirthdate = today.toISOString().split('T')[0];
  const oldest = new Date(today);
  oldest.setFullYear(today.getFullYear() - 150);
  const minBirthdate = oldest.toISOString().split('T')[0];

  bdayInput.setAttribute('max', maxBirthdate);
  bdayInput.setAttribute('min', minBirthdate);

  const setFieldState = (inputEl, errorEl, message) => {
    inputEl.setCustomValidity(message || '');
    inputEl.setAttribute('aria-invalid', message ? 'true' : 'false');
    if (errorEl) errorEl.textContent = message || '';
  };

  const clearAllErrors = () => {
    setFieldState(ageInput, ageError, '');
    setFieldState(bdayInput, bdayError, '');
  };

  const activeMode = () => (modeBdayBtn && modeBdayBtn.classList.contains('active') ? 'bday' : 'age');

  const validateAge = () => {
    const raw = ageInput.value.trim();
    if (!raw) {
      setFieldState(ageInput, ageError, 'Please enter your age in Earth years.');
      return null;
    }

    const value = Number(raw);
    if (!Number.isFinite(value)) {
      setFieldState(ageInput, ageError, 'Age must be a valid number.');
      return null;
    }
    if (value < 1 || value > 150) {
      setFieldState(ageInput, ageError, 'Age must be between 1 and 150 years.');
      return null;
    }

    setFieldState(ageInput, ageError, '');
    return value;
  };

  const validateBirthdate = () => {
    const raw = bdayInput.value;
    if (!raw) {
      setFieldState(bdayInput, bdayError, 'Please select your birthdate.');
      return null;
    }

    const dob = new Date(raw);
    if (Number.isNaN(dob.getTime())) {
      setFieldState(bdayInput, bdayError, 'Please enter a valid birthdate.');
      return null;
    }

    if (dob > today) {
      setFieldState(bdayInput, bdayError, 'Birthdate cannot be in the future.');
      return null;
    }

    const earthYears = (today - dob) / (1000 * 60 * 60 * 24 * 365.25);
    if (earthYears <= 0 || earthYears > 150) {
      setFieldState(bdayInput, bdayError, 'Birthdate must represent an age between 1 and 150 years.');
      return null;
    }

    setFieldState(bdayInput, bdayError, '');
    return earthYears;
  };

  const syncModeValidation = () => {
    const mode = activeMode();
    const isAgeMode = mode === 'age';
    ageInput.required = isAgeMode;
    bdayInput.required = !isAgeMode;

    if (isAgeMode) {
      bdayInput.value = '';
      setFieldState(bdayInput, bdayError, '');
    } else {
      ageInput.value = '';
      setFieldState(ageInput, ageError, '');
    }
  };

  if (modeAgeBtn) modeAgeBtn.addEventListener('click', syncModeValidation);
  if (modeBdayBtn) modeBdayBtn.addEventListener('click', syncModeValidation);

  ageInput.addEventListener('input', () => {
    if (!ageInput.value.trim()) {
      setFieldState(ageInput, ageError, '');
      return;
    }
    validateAge();
  });

  bdayInput.addEventListener('change', () => {
    if (!bdayInput.value) {
      setFieldState(bdayInput, bdayError, '');
      return;
    }
    validateBirthdate();
  });

  form.addEventListener('submit', (event) => {
    event.preventDefault();
    clearAllErrors();

    let earthYears;
    if (activeMode() === 'bday') {
      earthYears = validateBirthdate();
      if (!earthYears) {
        bdayInput.focus();
        return;
      }
      window.lastCalcMode = 'bday';
      window.lastCalcValue = bdayInput.value;
    } else {
      earthYears = validateAge();
      if (!earthYears) {
        ageInput.focus();
        return;
      }
      window.lastCalcMode = 'age';
      window.lastCalcValue = ageInput.value;
    }

    const ages = computePlanetAges(earthYears);
    updatePlanetCards(ages, earthYears);

    const planetDataSection = document.getElementById('planet-data');
    if (planetDataSection) {
      const nav = document.querySelector('.nav');
      const navHeight = nav ? nav.offsetHeight : 0;
      const top = planetDataSection.getBoundingClientRect().top + window.scrollY - navHeight - 8;
      const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

      window.scrollTo({
        top,
        behavior: prefersReducedMotion ? 'auto' : 'smooth',
      });
    }
  });

  syncModeValidation();
}

// ── Hero Scroll CTA (Index Page) ────────────────────────────
function initHeroScrollCta() {
  const scrollCta = document.querySelector('.hero__scroll[data-scroll-target]');
  if (!scrollCta) return;

  scrollCta.addEventListener('click', () => {
    const selector = scrollCta.getAttribute('data-scroll-target');
    const target = selector ? document.querySelector(selector) : null;
    if (!target) return;

    const nav = document.querySelector('.nav');
    const navHeight = nav ? nav.offsetHeight : 0;
    const top = target.getBoundingClientRect().top + window.scrollY - navHeight - 8;
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    window.scrollTo({
      top,
      behavior: prefersReducedMotion ? 'auto' : 'smooth',
    });
  });
}

// ── External Link Handler ───────────────────────────────────
function initExternalLinks() {
  const links = document.querySelectorAll('a[data-external-url], a[data-mailto]');
  if (!links.length) return;

  links.forEach((link) => {
    link.addEventListener('click', (event) => {
      const externalUrl = link.getAttribute('data-external-url');
      const mailto = link.getAttribute('data-mailto');

      if (!externalUrl && !mailto) return;

      event.preventDefault();

      if (mailto) {
        window.location.href = `mailto:${mailto}`;
        return;
      }

      if (externalUrl) {
        window.open(externalUrl, '_blank', 'noopener,noreferrer');
      }
    });
  });
}

function updatePlanetCards(ages, earthYears) {
  for (const [planet, age] of Object.entries(ages)) {
    const el = document.querySelector(`[data-planet="${planet}"] .planet-card__age`);
    if (el) el.textContent = age;
  }
  // Earth card shows earth age
  const earthEl = document.querySelector('[data-planet="Earth"] .planet-card__age');
  if (earthEl) earthEl.textContent = parseFloat(earthYears).toFixed(2);
}

// ── Planet Card Modal (Solar System Page) ───────────────────
const PLANET_SCRIPT_PATHS = {
  Sun: './scripts/sun.py',
  Mercury: './scripts/mercury.py',
  Venus: './scripts/venus.py',
  Earth: './scripts/earth.py',
  Mars: './scripts/mars.py',
  Jupiter: './scripts/jupiter.py',
  Saturn: './scripts/saturn.py',
  Uranus: './scripts/uranus.py',
  Neptune: './scripts/neptune.py',
  Pluto: './scripts/pluto.py',
};

const planetScriptCache = {};

async function loadPlanetScript(planetName) {
  const path = PLANET_SCRIPT_PATHS[planetName];
  if (!path) {
    return {
      content: '# Script path not configured for this body.',
      path: '',
    };
  }

  if (planetScriptCache[path]) {
    return {
      content: planetScriptCache[path],
      path,
    };
  }

  try {
    const response = await fetch(path);
    if (!response.ok) {
      throw new Error(`Failed to load script: ${response.status}`);
    }

    const text = await response.text();
    planetScriptCache[path] = text;
    return {
      content: text,
      path,
    };
  } catch {
    return {
      content: '# Unable to load script file.\n# Open this page through a local server if you are using file://',
      path,
    };
  }
}

function initPlanetModal() {
  const cards = document.querySelectorAll('.planet-card[data-planet]');
  const modal = document.getElementById('planet-modal');
  if (!cards.length || !modal) return;

  const panel = modal.querySelector('.planet-modal__panel');
  const closeBtn = document.getElementById('planet-modal-close');
  const titleEl = document.getElementById('planet-modal-title');
  const typeEl = document.getElementById('planet-modal-type');
  const descEl = document.getElementById('planet-modal-desc');
  const statsEl = document.getElementById('planet-modal-stats');
  const videoWrap = modal.querySelector('.planet-modal__video');
  const videoEl = document.getElementById('planet-modal-video');
  const videoSourceEl = document.getElementById('planet-modal-video-source');
  const scriptEl = document.getElementById('planet-modal-script');
  const fullscreenBtn = document.getElementById('planet-modal-fullscreen');
  const downloadBtn = document.getElementById('planet-modal-download');
  const copyBtn = document.getElementById('planet-modal-copy');

  if (!panel || !closeBtn || !titleEl || !typeEl || !descEl || !statsEl || !videoWrap || !videoEl || !videoSourceEl || !scriptEl || !fullscreenBtn || !downloadBtn || !copyBtn) {
    return;
  }

  let activePlanet = '';
  let activeScriptPath = '';
  let activeScriptContent = '';

  function setCopyButtonState(text, success) {
    copyBtn.textContent = text;
    copyBtn.classList.toggle('is-success', success);
    window.setTimeout(() => {
      copyBtn.textContent = 'Copy Script';
      copyBtn.classList.remove('is-success');
    }, 1600);
  }

  function closeModal() {
    modal.classList.remove('open');
    modal.setAttribute('aria-hidden', 'true');
    document.body.style.overflow = '';
    if (document.fullscreenElement) {
      if (document.exitFullscreen) {
        document.exitFullscreen().catch(() => {});
      } else if (document.webkitExitFullscreen) {
        try { document.webkitExitFullscreen(); } catch (e) {}
      }
    }
    videoEl.pause();
    videoSourceEl.setAttribute('src', '');
    videoEl.load();
  }

  function isVideoFullscreen() {
    return document.fullscreenElement === videoWrap || document.webkitFullscreenElement === videoWrap;
  }

  function updateFullscreenButton() {
    const active = isVideoFullscreen();
    fullscreenBtn.setAttribute('aria-pressed', String(active));
    fullscreenBtn.setAttribute('aria-label', active ? 'Exit video fullscreen' : 'Open video fullscreen');
    fullscreenBtn.querySelector('span').textContent = active ? 'Exit fullscreen' : 'Fullscreen';
  }

  async function toggleFullscreen() {
    try {
      if (isVideoFullscreen()) {
        if (document.exitFullscreen) {
          await document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
          await document.webkitExitFullscreen();
        }
      } else if (videoWrap.requestFullscreen) {
        await videoWrap.requestFullscreen();
      } else if (videoWrap.webkitRequestFullscreen) {
        await videoWrap.webkitRequestFullscreen();
      }
    } catch {
      // Ignore fullscreen errors if the browser blocks the request.
    }
  }

  async function openModalFromCard(card) {
    const planetName = card.getAttribute('data-planet') || 'Planet';
    const _typeEl = card.querySelector('.planet-card__type');
    const typeText = (_typeEl && _typeEl.textContent) ? _typeEl.textContent.trim() : 'Body';
    const _descEl = card.querySelector('.planet-card__desc');
    const descText = (_descEl && _descEl.textContent) ? _descEl.textContent.trim() : '';
    const _srcEl = card.querySelector('video source');
    const src = _srcEl ? (_srcEl.getAttribute('src') || '') : '';
    const statRows = card.querySelectorAll('.planet-stat');

    activePlanet = planetName;
    titleEl.textContent = planetName;
    typeEl.textContent = typeText;
    descEl.textContent = descText;
    scriptEl.textContent = '# Loading script...';

    const ageResultEl = document.getElementById('planet-modal-age-result');
    if (ageResultEl) {
      const _ageEl = card.querySelector('.planet-card__age');
      const ageVal = (_ageEl && _ageEl.textContent) ? _ageEl.textContent.trim() : '';
      if (ageVal && ageVal !== '—' && window.lastCalcMode) {
        if (window.lastCalcMode === 'bday') {
          const d = new Date(window.lastCalcValue).toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' });
          ageResultEl.innerHTML = `If you were born on ${d}, your age on ${planetName} is <strong>${ageVal} years</strong>.`;
        } else {
          ageResultEl.innerHTML = `If you are ${window.lastCalcValue} in Earth years, your age on ${planetName} is <strong>${ageVal} years</strong>.`;
        }
        ageResultEl.style.display = 'block';
      } else {
        ageResultEl.style.display = 'none';
      }
    }

    statsEl.innerHTML = '';
    statRows.forEach((row) => {
      const _qLabel = row.querySelector('span');
      const label = (_qLabel && _qLabel.textContent) ? _qLabel.textContent.trim() : null;
      const _qValue = row.querySelector('strong');
      const value = (_qValue && _qValue.textContent) ? _qValue.textContent.trim() : null;
      if (!label || !value) return;

      const item = document.createElement('div');
      item.className = 'planet-modal__stat';

      const labelEl = document.createElement('span');
      labelEl.className = 'planet-modal__stat-label';
      labelEl.textContent = label;

      const valueEl = document.createElement('span');
      valueEl.className = 'planet-modal__stat-value';
      valueEl.textContent = value;

      item.appendChild(labelEl);
      item.appendChild(valueEl);
      statsEl.appendChild(item);
    });

    if (src) {
      videoSourceEl.setAttribute('src', src);
      videoEl.load();
      videoEl.play().catch(() => {});
    }

    const scriptData = await loadPlanetScript(planetName);
    activeScriptPath = scriptData.path;
    activeScriptContent = scriptData.content;
    scriptEl.textContent = scriptData.content;

    modal.classList.add('open');
    modal.setAttribute('aria-hidden', 'false');
    document.body.style.overflow = 'hidden';
  }

  cards.forEach((card) => {
    card.setAttribute('tabindex', '0');
    card.setAttribute('role', 'button');
    card.setAttribute('aria-label', `Open ${card.getAttribute('data-planet') || 'planet'} details`);

    card.addEventListener('click', () => openModalFromCard(card));
    card.addEventListener('keydown', (event) => {
      if (event.key === 'Enter' || event.key === ' ') {
        event.preventDefault();
        openModalFromCard(card);
      }
    });
  });

  closeBtn.addEventListener('click', closeModal);

  fullscreenBtn.addEventListener('click', toggleFullscreen);

  document.addEventListener('fullscreenchange', updateFullscreenButton);
  document.addEventListener('webkitfullscreenchange', updateFullscreenButton);

  modal.addEventListener('click', (event) => {
    if (!panel.contains(event.target)) {
      closeModal();
    }
  });

  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && modal.classList.contains('open')) {
      closeModal();
    }
  });

  downloadBtn.addEventListener('click', () => {
    const scriptContent = activeScriptContent || scriptEl.textContent || '';
    if (!scriptContent.trim()) return;

    const blob = new Blob([scriptContent], { type: 'text/x-python;charset=utf-8' });
    const blobUrl = URL.createObjectURL(blob);
    const anchor = document.createElement('a');
    const fileBase = (activePlanet || 'planet').toLowerCase().replace(/\s+/g, '-');
    const hasExtension = activeScriptPath && /\.[a-z0-9]+$/i.test(activeScriptPath);
    const suffix = hasExtension ? '' : '.py';

    anchor.href = blobUrl;
    anchor.download = `${fileBase}-script${suffix}`;
    document.body.appendChild(anchor);
    anchor.click();
    document.body.removeChild(anchor);
    URL.revokeObjectURL(blobUrl);
  });

  copyBtn.addEventListener('click', async () => {
    const scriptContent = activeScriptContent || scriptEl.textContent || '';
    if (!scriptContent.trim()) return;

    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(scriptContent);
      } else {
        const helper = document.createElement('textarea');
        helper.value = scriptContent;
        helper.setAttribute('readonly', 'true');
        helper.style.position = 'fixed';
        helper.style.opacity = '0';
        document.body.appendChild(helper);
        helper.select();
        document.execCommand('copy');
        document.body.removeChild(helper);
      }

      setCopyButtonState('Copied', true);
    } catch {
      setCopyButtonState('Copy failed', false);
    }
  });
}

// ── Init ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const theme = localStorage.getItem('theme') || 'dark';
  updateThemeIcon(theme);
  initMobileNav();
  initScrollReveal();
  initActiveNav();
  initExternalLinks();
  initHeroScrollCta();
  initStars();
  initAgeCalculator();
  initPlanetModal();

  // Theme toggle button
  const toggleBtn = document.getElementById('theme-toggle');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', toggleTheme);
  }
});
