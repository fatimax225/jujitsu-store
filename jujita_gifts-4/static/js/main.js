// ── Mobile Menu ──
const mobileMenuBtn = document.getElementById('mobileMenuBtn');
const mobileMenu = document.getElementById('mobileMenu');
if (mobileMenuBtn && mobileMenu) {
    mobileMenuBtn.addEventListener('click', () => {
        mobileMenu.classList.toggle('open');
        const spans = mobileMenuBtn.querySelectorAll('span');
        mobileMenu.classList.contains('open')
            ? spans.forEach((s, i) => {
                if (i === 0) s.style.transform = 'rotate(45deg) translate(5px, 5px)';
                if (i === 1) s.style.opacity = '0';
                if (i === 2) s.style.transform = 'rotate(-45deg) translate(5px, -5px)';
              })
            : spans.forEach(s => { s.style.transform = ''; s.style.opacity = ''; });
    });
}

// ── Auto-dismiss Flashes ──
setTimeout(() => {
    document.querySelectorAll('.flash').forEach(f => {
        f.style.animation = 'slideIn 0.3s reverse';
        setTimeout(() => f.remove(), 280);
    });
}, 4000);

// ── Product Options ──
document.querySelectorAll('.option-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const group = btn.closest('.options-grid');
        group.querySelectorAll('.option-btn').forEach(b => b.classList.remove('selected'));
        btn.classList.add('selected');
        const hiddenInput = document.getElementById('selected-option');
        if (hiddenInput) hiddenInput.value = btn.dataset.value;
    });
});

// ── Quantity Controls ──
function changeQty(delta) {
    const input = document.getElementById('qty-input');
    if (!input) return;
    let val = parseInt(input.value) + delta;
    if (val < 1) val = 1;
    if (val > 99) val = 99;
    input.value = val;
}

// ── Rating Stars ──
document.querySelectorAll('.star-input').forEach(star => {
    star.addEventListener('click', () => {
        const rating = star.dataset.rating;
        document.getElementById('rating-value').value = rating;
        document.querySelectorAll('.star-input').forEach((s, i) => {
            s.style.color = i < rating ? '#C8A96E' : '#ddd';
        });
    });
    star.addEventListener('mouseover', () => {
        const r = parseInt(star.dataset.rating);
        document.querySelectorAll('.star-input').forEach((s, i) => {
            s.style.color = i < r ? '#C8A96E' : '#ddd';
        });
    });
});

// ── Scroll Reveal ──
const observerOpts = { threshold: 0.1, rootMargin: '0px 0px -40px 0px' };
const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = '1';
            entry.target.style.transform = 'translateY(0)';
            observer.unobserve(entry.target);
        }
    });
}, observerOpts);

document.querySelectorAll('.product-card, .stat-card, .review-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(20px)';
    el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
    observer.observe(el);
});

// ── Image Preview on Admin Upload ──
const imageInput = document.getElementById('product-image-input');
const imagePreview = document.getElementById('image-preview');
if (imageInput && imagePreview) {
    imageInput.addEventListener('change', () => {
        const file = imageInput.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = e => {
                imagePreview.src = e.target.result;
                imagePreview.style.display = 'block';
            };
            reader.readAsDataURL(file);
        }
    });
}

// ── Payment proof upload preview ──
const proofInput = document.getElementById('proof-input');
if (proofInput) {
    proofInput.addEventListener('change', () => {
        const label = document.getElementById('proof-label');
        if (label && proofInput.files[0]) {
            label.textContent = proofInput.files[0].name;
        }
    });
}
