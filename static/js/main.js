// ==================== MINDACADEMY - JAVASCRIPT COMPLET ====================
// 心の学院 - Academia Minții

// ==================== NAVBAR - MENU MOBIL ====================
const menuToggle = document.getElementById('menuToggle');
const navMenu = document.getElementById('navMenu');

if (menuToggle && navMenu) {
    menuToggle.addEventListener('click', () => {
        navMenu.classList.toggle('active');

        // Schimbă iconița hamburger
        const icon = menuToggle.querySelector('span');
        if (navMenu.classList.contains('active')) {
            icon.textContent = '✕';
        } else {
            icon.textContent = '☰';
        }
    });

    // Închide meniul când se dă click pe un link
    const navLinks = navMenu.querySelectorAll('.nav-link, .btn-demo');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            navMenu.classList.remove('active');
            menuToggle.querySelector('span').textContent = '☰';
        });
    });

    // Închide meniul când se dă click în afara lui
    document.addEventListener('click', (e) => {
        if (!navMenu.contains(e.target) && !menuToggle.contains(e.target)) {
            navMenu.classList.remove('active');
            menuToggle.querySelector('span').textContent = '☰';
        }
    });
}

// ==================== SMOOTH SCROLL ====================
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));

        if (target) {
            const navbarHeight = document.querySelector('.navbar').offsetHeight;
            const targetPosition = target.getBoundingClientRect().top + window.pageYOffset - navbarHeight;

            window.scrollTo({
                top: targetPosition,
                behavior: 'smooth'
            });
        }
    });
});

// ==================== STICKY NAVBAR ====================
const navbar = document.querySelector('.navbar');
let lastScroll = 0;

window.addEventListener('scroll', () => {
    const currentScroll = window.pageYOffset;

    if (currentScroll > 100) {
        navbar.style.boxShadow = '0 4px 20px rgba(28, 28, 28, 0.15)';
    } else {
        navbar.style.boxShadow = '0 4px 20px rgba(28, 28, 28, 0.08)';
    }

    lastScroll = currentScroll;
});

// ==================== ANIMAȚII ON SCROLL ====================
const observerOptions = {
    threshold: 0.1,
    rootMargin: '0px 0px -50px 0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('fade-in');
        }
    });
}, observerOptions);

// Observă toate cardurile și secțiunile
document.querySelectorAll('.feature-card, .course-card, .testimonial-card, section').forEach(el => {
    observer.observe(el);
});

// ==================== FILTRARE CURSURI ====================
// Pentru pagina cursuri.html
const courseFilters = document.getElementById('courseFilters');
if (courseFilters) {
    const levelFilter = document.getElementById('levelFilter');
    const priceFilter = document.getElementById('priceFilter');
    const availabilityFilter = document.getElementById('availabilityFilter');
    const courseCards = document.querySelectorAll('.course-card');

    function filterCourses() {
        const level = levelFilter.value;
        const maxPrice = priceFilter.value;
        const availability = availabilityFilter.value;

        courseCards.forEach(card => {
            const cardLevel = card.dataset.level;
            const cardPrice = parseInt(card.dataset.price);
            const cardAvailability = card.dataset.availability;

            let showCard = true;

            if (level !== 'toate' && cardLevel !== level) {
                showCard = false;
            }

            if (maxPrice !== 'toate' && cardPrice > parseInt(maxPrice)) {
                showCard = false;
            }

            if (availability !== 'toate' && cardAvailability !== availability) {
                showCard = false;
            }

            card.style.display = showCard ? 'block' : 'none';
        });

        // Verifică dacă există rezultate
        const visibleCards = Array.from(courseCards).filter(card => card.style.display !== 'none');
        const noResults = document.getElementById('noResults');

        if (noResults) {
            noResults.style.display = visibleCards.length === 0 ? 'block' : 'none';
        }
    }

    if (levelFilter && priceFilter && availabilityFilter) {
        levelFilter.addEventListener('change', filterCourses);
        priceFilter.addEventListener('change', filterCourses);
        availabilityFilter.addEventListener('change', filterCourses);
    }
}

// ==================== VALIDARE FORMULARE ====================
const forms = document.querySelectorAll('form');

forms.forEach(form => {
    form.addEventListener('submit', (e) => {
        e.preventDefault();

        let isValid = true;
        const requiredFields = form.querySelectorAll('[required]');

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                field.style.borderColor = 'var(--vermillion)';

                // Elimină border roșu după 3 secunde
                setTimeout(() => {
                    field.style.borderColor = '';
                }, 3000);
            }
        });

        if (isValid) {
            // Validare email
            const emailField = form.querySelector('input[type="email"]');
            if (emailField) {
                const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                if (!emailRegex.test(emailField.value)) {
                    isValid = false;
                    emailField.style.borderColor = 'var(--vermillion)';
                    alert('Te rugăm să introduci o adresă de email validă.');
                    return;
                }
            }

            // Validare telefon
            const phoneField = form.querySelector('input[type="tel"]');
            if (phoneField) {
                const phoneRegex = /^[0-9]{10}$/;
                const cleanPhone = phoneField.value.replace(/\s/g, '');
                if (!phoneRegex.test(cleanPhone)) {
                    isValid = false;
                    phoneField.style.borderColor = 'var(--vermillion)';
                    alert('Te rugăm să introduci un număr de telefon valid (10 cifre).');
                    return;
                }
            }

            // Succes - afișează mesaj
            showSuccessMessage(form);
            form.reset();
        } else {
            alert('Te rugăm să completezi toate câmpurile obligatorii.');
        }
    });

    // Elimină border-ul roșu când utilizatorul începe să scrie
    const inputs = form.querySelectorAll('input, textarea, select');
    inputs.forEach(input => {
        input.addEventListener('input', () => {
            input.style.borderColor = '';
        });
    });
});

function showSuccessMessage(form) {
    const successDiv = document.createElement('div');
    successDiv.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: var(--bamboo-green);
        color: white;
        padding: 2rem 3rem;
        border-radius: var(--border-radius);
        box-shadow: var(--shadow-hover);
        z-index: 10000;
        text-align: center;
        border: 3px solid var(--gold-leaf);
    `;
    successDiv.innerHTML = `
        <div style="font-size: 3rem; margin-bottom: 1rem;">✅</div>
        <h3 style="color: white; margin-bottom: 0.5rem;">Mulțumim!</h3>
        <p style="color: white;">Mesajul tău a fost trimis cu succes. Te vom contacta în cel mai scurt timp!</p>
    `;

    document.body.appendChild(successDiv);

    setTimeout(() => {
        successDiv.style.opacity = '0';
        successDiv.style.transition = 'opacity 0.3s ease';
        setTimeout(() => successDiv.remove(), 300);
    }, 3000);
}

// ==================== COUNTER ANIMATION ====================
const counters = document.querySelectorAll('.counter');

counters.forEach(counter => {
    const target = +counter.getAttribute('data-target');
    const increment = target / 200;

    const updateCounter = () => {
        const current = +counter.innerText;

        if (current < target) {
            counter.innerText = Math.ceil(current + increment);
            setTimeout(updateCounter, 10);
        } else {
            counter.innerText = target;
        }
    };

    // Pornește animația când elementul devine vizibil
    const counterObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                updateCounter();
                counterObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    counterObserver.observe(counter);
});

// ==================== TESTIMONIALS CAROUSEL (OPȚIONAL) ====================
const testimonialCards = document.querySelectorAll('.testimonial-card');
let currentTestimonial = 0;

function rotateTestimonials() {
    if (testimonialCards.length > 3) {
        testimonialCards.forEach((card, index) => {
            card.style.display = 'none';
        });

        for (let i = 0; i < 3; i++) {
            const index = (currentTestimonial + i) % testimonialCards.length;
            testimonialCards[index].style.display = 'block';
        }

        currentTestimonial = (currentTestimonial + 1) % testimonialCards.length;
    }
}

// Activează doar pe mobile
if (window.innerWidth <= 768 && testimonialCards.length > 1) {
    setInterval(rotateTestimonials, 5000);
}

// ==================== LAZY LOADING IMAGES ====================
const images = document.querySelectorAll('img[data-src]');

const imageObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const img = entry.target;
            img.src = img.dataset.src;
            img.removeAttribute('data-src');
            imageObserver.unobserve(img);
        }
    });
});

images.forEach(img => imageObserver.observe(img));

// ==================== BACK TO TOP BUTTON ====================
const backToTopBtn = document.createElement('button');
backToTopBtn.innerHTML = '↑';
backToTopBtn.style.cssText = `
    position: fixed;
    bottom: 30px;
    right: 30px;
    width: 50px;
    height: 50px;
    background: var(--vermillion);
    color: white;
    border: 2px solid var(--sumi-black);
    border-radius: 50%;
    font-size: 1.5rem;
    cursor: pointer;
    opacity: 0;
    visibility: hidden;
    transition: var(--transition);
    z-index: 1000;
    box-shadow: var(--shadow);
`;

document.body.appendChild(backToTopBtn);

window.addEventListener('scroll', () => {
    if (window.pageYOffset > 300) {
        backToTopBtn.style.opacity = '1';
        backToTopBtn.style.visibility = 'visible';
    } else {
        backToTopBtn.style.opacity = '0';
        backToTopBtn.style.visibility = 'hidden';
    }
});

backToTopBtn.addEventListener('click', () => {
    window.scrollTo({
        top: 0,
        behavior: 'smooth'
    });
});

backToTopBtn.addEventListener('mouseenter', () => {
    backToTopBtn.style.transform = 'scale(1.1)';
});

backToTopBtn.addEventListener('mouseleave', () => {
    backToTopBtn.style.transform = 'scale(1)';
});

// ==================== CURSOR PERSONALIZAT (OPȚIONAL - EFECT JAPONEZ) ====================
const cursor = document.createElement('div');
cursor.style.cssText = `
    width: 20px;
    height: 20px;
    border: 2px solid var(--vermillion);
    border-radius: 50%;
    position: fixed;
    pointer-events: none;
    z-index: 9999;
    transition: all 0.1s ease;
    display: none;
`;
document.body.appendChild(cursor);

// Activează doar pe desktop
if (window.innerWidth > 1024) {
    cursor.style.display = 'block';

    document.addEventListener('mousemove', (e) => {
        cursor.style.left = e.clientX - 10 + 'px';
        cursor.style.top = e.clientY - 10 + 'px';
    });

    // Mărește cursorul pe hover peste elemente interactive
    const interactiveElements = document.querySelectorAll('a, button, .btn');
    interactiveElements.forEach(el => {
        el.addEventListener('mouseenter', () => {
            cursor.style.transform = 'scale(1.5)';
            cursor.style.backgroundColor = 'rgba(211, 47, 47, 0.2)';
        });
        el.addEventListener('mouseleave', () => {
            cursor.style.transform = 'scale(1)';
            cursor.style.backgroundColor = 'transparent';
        });
    });
}

// ==================== CONSOLE MESSAGE ====================
console.log('%c心の学院 MindAcademy', 'color: #D32F2F; font-size: 24px; font-weight: bold;');
console.log('%cWelcome to MindAcademy - Where passion meets performance', 'color: #4A6741; font-size: 14px;');

// ==================== PERFORMANCE OPTIMIZATION ====================
// Debounce function pentru resize events
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

// Optimizează resize events
window.addEventListener('resize', debounce(() => {
    // Recalculează layout-ul dacă e necesar
    console.log('Window resized');
}, 250));