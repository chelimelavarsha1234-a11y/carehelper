document.addEventListener('DOMContentLoaded', function () {
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
        setTimeout(function () {
            alert.classList.add('fade');
            setTimeout(function () {
                alert.remove();
            }, 500);
        }, 4000);
    });

    const tips = [
        'Small check-ins can make a big difference.',
        'The best care plan is one everyone can understand.',
        'A trusted helper can turn an errand into connection.',
        'CareCircle keeps loved ones close, wherever they are.'
    ];
    const tip = document.getElementById('careTip');
    if (tip) {
        let tipIndex = 0;
        setInterval(function () {
            tip.classList.add('tip-changing');
            setTimeout(function () {
                tipIndex = (tipIndex + 1) % tips.length;
                tip.textContent = tips[tipIndex];
                tip.classList.remove('tip-changing');
            }, 250);
        }, 4200);
    }

    document.querySelectorAll('[data-count]').forEach(function (counter) {
        const target = Number(counter.dataset.count);
        let current = 0;
        const step = Math.max(1, Math.ceil(target / 30));
        const timer = setInterval(function () {
            current = Math.min(target, current + step);
            counter.textContent = current + (target === 100 ? '%' : target === 24 ? '/7' : '+');
            if (current === target) clearInterval(timer);
        }, 35);
    });

    if (!window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        const revealItems = document.querySelectorAll('.card, .summary-card, .request-card, .elder-profile-card');
        revealItems.forEach(function (item, index) {
            item.classList.add('reveal-item');
            item.style.setProperty('--reveal-delay', `${Math.min(index * 45, 360)}ms`);
        });
    }
});
