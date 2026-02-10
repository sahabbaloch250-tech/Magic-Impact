// Magic Impact - Main JavaScript

// Navbar scroll effect
window.addEventListener('scroll', function() {
    const navbar = document.getElementById('mainNav');
    if (window.scrollY > 50) {
        navbar.classList.add('navbar-scrolled');
        navbar.style.background = 'rgba(10, 14, 39, 0.98)';
        navbar.style.boxShadow = '0 4px 20px rgba(0, 0, 0, 0.3)';
    } else {
        navbar.classList.remove('navbar-scrolled');
        navbar.style.background = 'rgba(10, 14, 39, 0.95)';
        navbar.style.boxShadow = 'none';
    }
});

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
        e.preventDefault();
        const target = document.querySelector(this.getAttribute('href'));
        if (target) {
            target.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    });
});

// Counter animation for stats
function animateCounter(element, target, duration = 2000) {
    let start = 0;
    const increment = target / (duration / 16);
    const timer = setInterval(() => {
        start += increment;
        if (start >= target) {
            element.textContent = formatNumber(target);
            clearInterval(timer);
        } else {
            element.textContent = formatNumber(Math.floor(start));
        }
    }, 16);
}

function formatNumber(num) {
    if (num >= 1000000) {
        return (num / 1000000).toFixed(1) + 'M';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'K';
    }
    return num.toString();
}

// Trigger counter animation when stats come into view
const observerOptions = {
    threshold: 0.5,
    rootMargin: '0px'
};

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            const statElement = entry.target;
            const targetValue = parseInt(statElement.dataset.target);
            animateCounter(statElement, targetValue);
            observer.unobserve(statElement);
        }
    });
}, observerOptions);

// Set up stats observation
document.addEventListener('DOMContentLoaded', () => {
    const statUsers = document.getElementById('stat-users');
    if (statUsers) {
        statUsers.dataset.target = '50000';
        observer.observe(statUsers);
    }
});

// File upload preview
document.querySelectorAll('.upload-box input[type="file"]').forEach(input => {
    input.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const uploadBox = this.closest('.upload-box');
            const uploadContent = uploadBox.querySelector('.upload-content');
            
            // Create preview
            const reader = new FileReader();
            reader.onload = function(e) {
                uploadContent.innerHTML = `
                    <img src="${e.target.result}" style="max-width: 100%; max-height: 200px; border-radius: 8px;">
                    <p class="mt-2 mb-0">${file.name}</p>
                    <small class="text-success">File uploaded successfully</small>
                `;
            };
            reader.readAsDataURL(file);
        }
    });
});

// Drag and drop for file upload
document.querySelectorAll('.upload-box').forEach(box => {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        box.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        box.addEventListener(eventName, () => {
            box.style.borderColor = 'var(--primary)';
            box.style.background = 'rgba(13, 110, 253, 0.05)';
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        box.addEventListener(eventName, () => {
            box.style.borderColor = 'rgba(255, 255, 255, 0.3)';
            box.style.background = 'transparent';
        }, false);
    });

    box.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        const input = box.querySelector('input[type="file"]');
        input.files = files;
        
        // Trigger change event
        const event = new Event('change', { bubbles: true });
        input.dispatchEvent(event);
    }, false);
});

// Investment Modal function (already defined in HTML but included here for completeness)
window.openInvestment = function(plan, amount, daily) {
    document.getElementById("planName").innerText = plan;
    document.getElementById("planAmount").innerText = amount;
    const modal = new bootstrap.Modal(document.getElementById('investmentModal'));
    modal.show();
};

// Add loading animation to buttons
document.querySelectorAll('.btn').forEach(button => {
    button.addEventListener('click', function(e) {
        // Only for submit buttons
        if (this.type === 'submit' || this.classList.contains('btn-submit')) {
            this.classList.add('loading');
            const originalText = this.innerHTML;
            this.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...';
            
            // Reset after 2 seconds (adjust based on actual form submission)
            setTimeout(() => {
                this.innerHTML = originalText;
                this.classList.remove('loading');
            }, 2000);
        }
    });
});

// Animate elements on scroll
const animateOnScroll = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('fade-in');
        }
    });
}, {
    threshold: 0.1
});

document.addEventListener('DOMContentLoaded', () => {
    // Animate all cards
    document.querySelectorAll('.plan-card, .feature-card, .testimonial-card').forEach(card => {
        animateOnScroll.observe(card);
    });
});

// Navbar mobile menu close on link click
document.querySelectorAll('.nav-link').forEach(link => {
    link.addEventListener('click', () => {
        const navbarCollapse = document.getElementById('navbarNav');
        if (navbarCollapse.classList.contains('show')) {
            const bsCollapse = new bootstrap.Collapse(navbarCollapse);
            bsCollapse.hide();
        }
    });
});

// Add active class to current nav item
const currentLocation = window.location.hash;
if (currentLocation) {
    document.querySelectorAll('.nav-link').forEach(link => {
        if (link.getAttribute('href') === currentLocation) {
            link.classList.add('active');
        }
    });
}

console.log('🎉 Magic Impact loaded successfully!');