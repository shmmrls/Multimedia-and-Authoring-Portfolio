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
  document.querySelectorAll('.nav__link').forEach(link => {
    const href = link.getAttribute('href');
    if (!href) return;
    // Normalize: strip leading dots and slashes for comparison
    const linkPath = href.replace(/^\.\.\//, '/').replace(/^\.\//, '/');
    if (
      (path.endsWith(href)) ||
      (path.includes(href) && href !== '/' && href !== 'index.html')
    ) {
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

  function resize() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
    generateStars();
    drawStars();
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
      });
    }
  }

  function drawStars(t) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    stars.forEach(s => {
      const flicker = s.o + Math.sin((t || 0) * s.speed + s.phase) * 0.15;
      ctx.beginPath();
      ctx.arc(s.x, s.y, s.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(232, 228, 220, ${Math.max(0, Math.min(1, flicker))})`;
      ctx.fill();
    });
  }

  let animFrame;
  function animate(t) {
    drawStars(t * 0.001);
    animFrame = requestAnimationFrame(animate);
  }

  resize();
  window.addEventListener('resize', resize);
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
  const calcBtn   = document.getElementById('calc-btn');

  calcBtn.addEventListener('click', () => {
    let earthYears = null;

    if (bdayInput && bdayInput.value) {
      const dob  = new Date(bdayInput.value);
      const now  = new Date();
      earthYears = (now - dob) / (1000 * 60 * 60 * 24 * 365.25);
    } else if (ageInput && ageInput.value) {
      earthYears = parseFloat(ageInput.value);
    }

    if (!earthYears || isNaN(earthYears) || earthYears <= 0) {
      alert('Please enter a valid age or birthdate.');
      return;
    }

    const ages = computePlanetAges(earthYears);
    updatePlanetCards(ages, earthYears);
  });

  // Sync inputs — clear one when the other is typed in
  if (ageInput && bdayInput) {
    ageInput.addEventListener('input',  () => { if (ageInput.value)  bdayInput.value = ''; });
    bdayInput.addEventListener('input', () => { if (bdayInput.value) ageInput.value  = ''; });
  }
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

// ── Init ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  const theme = localStorage.getItem('theme') || 'dark';
  updateThemeIcon(theme);
  initMobileNav();
  initScrollReveal();
  initActiveNav();
  initStars();
  initAgeCalculator();

  // Theme toggle button
  const toggleBtn = document.getElementById('theme-toggle');
  if (toggleBtn) {
    toggleBtn.addEventListener('click', toggleTheme);
  }
});
