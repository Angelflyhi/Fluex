const canvas = document.getElementById("hero-lightpass");
const context = canvas.getContext("2d");

// Update frame count to 83 based on user provided images
const frameCount = 83;
const currentFrame = index => (
  `/frames/ezgif-frame-${(index + 1).toString().padStart(3, '0')}.jpg`
);

const images = [];
const imageLoader = {
    loaded: 0,
    total: frameCount
};

// Preload images for smooth playback
const preloadImages = () => {
    for (let i = 0; i < frameCount; i++) {
        const img = new Image();
        img.src = currentFrame(i);
        img.onload = () => {
            imageLoader.loaded++;
            if (i === 0) {
                // Set initial canvas size and draw first frame
                renderInitial(img);
            }
        };
        images.push(img);
    }
};

const renderInitial = (img) => {
    canvas.width = img.naturalWidth || 1280;
    canvas.height = img.naturalHeight || 720;
    context.drawImage(img, 0, 0, canvas.width, canvas.height);
};

const updateImage = index => {
    if (images[index] && images[index].complete) {
        context.clearRect(0, 0, canvas.width, canvas.height);
        context.drawImage(images[index], 0, 0, canvas.width, canvas.height);
    }
};

// Scroll Handling
const sections = document.querySelectorAll('.section');
const indicator = document.querySelector('.scroll-indicator');

window.addEventListener('scroll', () => {  
    const html = document.documentElement;
    const scrollTop = html.scrollTop;
    const maxScrollTop = html.scrollHeight - window.innerHeight;
    const scrollFraction = Math.max(0, Math.min(1, scrollTop / maxScrollTop));
    
    // Calculate frame index
    const frameIndex = Math.min(
        frameCount - 1,
        Math.floor(scrollFraction * frameCount)
    );
    
    requestAnimationFrame(() => {
        updateImage(frameIndex);
        
        // Hide indicator after initial scroll
        if (scrollTop > 100) {
            indicator.style.opacity = '0';
        } else {
            indicator.style.opacity = '0.6';
        }

        // Section activation logic
        sections.forEach((section, idx) => {
            const rect = section.getBoundingClientRect();
            const viewHeight = window.innerHeight;
            
            // Section is active when its center is near the viewport center
            const centerOffset = Math.abs(rect.top + rect.height/2 - viewHeight/2);
            
            if (centerOffset < viewHeight * 0.4) {
                section.classList.add('active');
            } else {
                section.classList.remove('active');
            }
        });
    });
});

// Initialize
preloadImages();
// Force initial scroll check
window.dispatchEvent(new Event('scroll'));

// Resize handler
window.addEventListener('resize', () => {
    // Re-trigger scroll to ensure canvas keeps state
    window.dispatchEvent(new Event('scroll'));
});
