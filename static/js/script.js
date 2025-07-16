document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const helpToggle = document.getElementById('help-toggle');
    const helpModal = document.getElementById('help-modal');
    const helpModalClose = document.getElementById('help-modal-close');
    const form = document.getElementById('download-form');
    const progressSection = document.getElementById('progress-section');
    const progressFill = document.getElementById('progress-fill');
    const progressPercent = document.getElementById('progress-percent');
    const statusMessage = document.getElementById('status-message');
    const resultSection = document.getElementById('result-section');
    const downloadBtn = document.getElementById('download-btn');
    const newDownloadBtn = document.getElementById('new-download-btn');
    const flashContainer = document.getElementById('flash-messages');
    const resultPlayer = document.getElementById('result-player');
    const previewPlaceholder = document.getElementById('preview-placeholder');
    const videoLoading = document.getElementById('video-loading');
    const particlesContainer = document.getElementById('particles');
    const themeToggle = document.getElementById('theme-toggle');
    const themeIcon = themeToggle.querySelector('i');
    const previewPlayer = document.getElementById('preview-player');
    const videoPreviewContainer = document.getElementById('video-preview-container');
    const previewBtn = document.getElementById('preview-btn');
    const startTimeInput = document.getElementById('ss');
    const endTimeInput = document.getElementById('to');
    const formatSelector = document.getElementById('format-selector');
    const formatInput = document.getElementById('format');
    const formContainer = document.getElementById('form-container');
    const youtubeUrlInput = document.getElementById('link');
    const outputField = document.getElementById('output');
    
    // Modal elements
    const progressModal = document.getElementById('progress-modal');
    const modalProgressFill = document.getElementById('modal-progress-fill');
    const modalProgressPercent = document.getElementById('modal-progress-percent');
    const modalStatusMessage = document.getElementById('modal-status-message');
    const modalClose = document.getElementById('modal-close');
    
    let videoDuration = 0;
    let isOutputEdited = false;

    // Track output field modifications
    outputField.addEventListener('input', function() {
        isOutputEdited = true;
    });

    // Reset output edit flag when URL changes
    youtubeUrlInput.addEventListener('input', function() {
        isOutputEdited = false;
    });
helpToggle.addEventListener('click', () => {
    helpModal.style.display = 'block';
});

helpModalClose.addEventListener('click', () => {
    helpModal.style.display = 'none';
});

// Close modal when clicking outside
window.addEventListener('click', (e) => {
    if (e.target === helpModal) {
        helpModal.style.display = 'none';
    }
});

    // ===== Counter Animation =====
    function animateCounter(element, target, suffix = '', precision = 0) {
        let start = 0;
        const duration = 2000;
        const startTime = performance.now();
        const isInteger = Number.isInteger(target);
        
        function updateCounter(currentTime) {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const value = progress * target;
            
            element.textContent = isInteger ? 
                Math.floor(value) + suffix : 
                value.toFixed(precision) + suffix;
            
            if (progress < 1) {
                requestAnimationFrame(updateCounter);
            }
        }
        requestAnimationFrame(updateCounter);
    }
    
    // Initialize counters
    animateCounter(document.getElementById('avg-processing'), 4.8, '', 1);
    animateCounter(document.getElementById('clips-created'), 12000, '', 0);
    animateCounter(document.getElementById('success-rate'), 99.7, '', 1);
    
    // ===== Theme Management =====
    // Set default to dark mode
    document.body.classList.add('dark-mode');
    document.body.classList.remove('light-mode');
    themeIcon.className = 'fas fa-sun';
    localStorage.setItem('preferredTheme', 'dark');
    
    // Toggle theme manually
    themeToggle.addEventListener('click', function() {
        const isDarkMode = document.body.classList.contains('dark-mode');
        
        document.body.classList.toggle('dark-mode', !isDarkMode);
        document.body.classList.toggle('light-mode', isDarkMode);
        themeIcon.className = isDarkMode ? 'fas fa-moon' : 'fas fa-sun';
        
        // Save preference
        localStorage.setItem('preferredTheme', isDarkMode ? 'light' : 'dark');
        
        // Animation
        this.classList.add('animate__animated', 'animate__rubberBand');
        setTimeout(() => {
            this.classList.remove('animate__animated', 'animate__rubberBand');
        }, 1000);
    });
    
    // ===== Format Selector =====
    formatSelector.querySelectorAll('.btn-format').forEach(btn => {
        btn.addEventListener('click', function() {
            formatSelector.querySelectorAll('.btn-format').forEach(b => {
                b.classList.remove('active');
            });
            this.classList.add('active');
            formatInput.value = this.dataset.format;
        });
    });
    
    // ===== Enhanced Particle System =====
    function createParticles() {
        const particleCount = 100;
        const sizes = ['small', 'medium', 'large', 'x-large'];
        const colors = [
            'linear-gradient(135deg, #8a2be2, #4361ee)',
            'linear-gradient(135deg, #4cc9f0, #38b000)',
            'linear-gradient(135deg, #9d4edd, #f72585)',
            'linear-gradient(135deg, #7209b7, #3a0ca3)'
        ];
        
        for (let i = 0; i < particleCount; i++) {
            const particle = document.createElement('div');
            particle.classList.add('particle');
            
            // Random size
            const size = sizes[Math.floor(Math.random() * sizes.length)];
            particle.classList.add(size);
            
            // Random position
            particle.style.left = `${Math.random() * 100}%`;
            particle.style.top = `${Math.random() * 100}%`;
            
            // Random color
            const color = colors[Math.floor(Math.random() * colors.length)];
            particle.style.background = color;
            
            // Random animation
            const duration = Math.random() * 30 + 10;
            const delay = Math.random() * 5;
            particle.style.animationDuration = `${duration}s`;
            particle.style.animationDelay = `${delay}s`;
            
            particlesContainer.appendChild(particle);
        }
    }
    
    // ===== Button Effects =====
    const buttons = document.querySelectorAll('.btn, .btn-format');
    buttons.forEach(button => {
        // Ripple effect
        button.addEventListener('click', function(e) {
            const x = e.clientX - e.target.getBoundingClientRect().left;
            const y = e.clientY - e.target.getBoundingClientRect().top;
            
            const ripple = document.createElement('span');
            ripple.classList.add('ripple');
            ripple.style.left = `${x}px`;
            ripple.style.top = `${y}px`;
            
            this.appendChild(ripple);
            
            setTimeout(() => {
                ripple.remove();
            }, 600);
        });
        
        // 3D tilt effect
        button.addEventListener('mousemove', (e) => {
            const rect = button.getBoundingClientRect();
            const x = (e.clientX - rect.left) / rect.width;
            const y = (e.clientY - rect.top) / rect.height;
            
            const tiltX = (x - 0.5) * 20;
            const tiltY = (y - 0.5) * 20;
            
            button.style.transform = `translateY(-3px) rotateX(${-tiltY}deg) rotateY(${tiltX}deg) scale(1.05)`;
        });
        
        button.addEventListener('mouseleave', () => {
            button.style.transform = '';
        });
    });
    
    // ===== Form Animations =====
    const formInputs = document.querySelectorAll('.form-control');
    formInputs.forEach(input => {
        input.addEventListener('focus', () => {
            input.parentElement.style.transform = 'translateY(-5px)';
        });
        
        input.addEventListener('blur', () => {
            input.parentElement.style.transform = '';
        });
    });
    
    // ===== Video Player =====
    resultPlayer.preload = 'none';
    resultPlayer.playsInline = true;
    resultPlayer.disableRemotePlayback = true;
    resultPlayer.crossOrigin = 'anonymous';
    
    // ===== Helper Functions =====
    function formatTime(seconds) {
        const h = Math.floor(seconds / 3600);
        const m = Math.floor((seconds % 3600) / 60);
        const s = Math.floor(seconds % 60);
        
        return [
            h.toString().padStart(2, '0'),
            m.toString().padStart(2, '0'),
            s.toString().padStart(2, '0')
        ].join(':');
    }
    
    // ===== Modal Functions =====
    function showProgressModal() {
        progressModal.style.display = 'block';
    }
    
    function hideProgressModal() {
        progressModal.style.display = 'none';
    }
    
    function updateModalProgress(progress, message) {
        modalProgressFill.style.width = `${progress}%`;
        modalProgressPercent.textContent = `${Math.round(progress)}%`;
        modalStatusMessage.innerHTML = `<i class="fas fa-cogs"></i> ${message}`;
        
        // Add pulse effect when progress updates
        if (progress > 0) {
            modalProgressFill.style.animation = 'none';
            void modalProgressFill.offsetWidth; // Trigger reflow
            modalProgressFill.style.animation = 'pulse 0.5s ease';
        }
    }
    
    // ===== Preview Button Handler =====
    previewBtn.addEventListener('click', async function() {
        const youtubeUrl = youtubeUrlInput.value.trim();
        
        if (!youtubeUrl) {
            showFlash('error', 'Please enter a YouTube URL');
            return;
        }
        
        try {
            previewBtn.disabled = true;
            previewBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            
            // Extract video ID
            const videoId = extractVideoId(youtubeUrl);
            if (!videoId) {
                throw new Error('Invalid YouTube URL');
            }
            
            // Get video info from backend
            const response = await fetch(`/video_info/${videoId}`);
            if (!response.ok) {
                throw new Error('Failed to fetch video info');
            }
            
            const data = await response.json();
            if (!data.stream_url) {
                throw new Error('No stream URL found');
            }
            
            // Set video source
            previewPlayer.src = data.stream_url;
            videoPreviewContainer.style.display = 'block';
            
            // Wait for metadata to load
            await new Promise((resolve) => {
                previewPlayer.onloadedmetadata = () => {
                    // Get actual video duration
                    videoDuration = previewPlayer.duration;
                    
                    // Reset time inputs
                    startTimeInput.value = '00:00:00';
                    endTimeInput.value = formatTime(Math.min(videoDuration, 300));
                    
                    // Update filename only if not manually edited
                    if (data.title && (!isOutputEdited || outputField.value.trim() === '')) {
                        const cleanTitle = data.title.replace(/[^\w\s]/gi, '').substring(0, 50);
                        outputField.value = cleanTitle;
                        isOutputEdited = false;  // Reset flag after auto-setting
                    }
                    
                    // AUTOPLAY THE VIDEO AFTER LOADING
                    previewPlayer.play().catch(e => {
                        console.warn('Autoplay prevented:', e);
                        showFlash('info', 'Click the play button to start video');
                    });
                    
                    resolve();
                };
                
                previewPlayer.onerror = () => {
                    throw new Error('Failed to load video preview');
                };
            });
            
            previewBtn.innerHTML = '<i class="fas fa-eye"></i> Preview Video';
            previewBtn.disabled = false;
            
        } catch (error) {
            showFlash('error', error.message);
            previewBtn.innerHTML = '<i class="fas fa-eye"></i> Preview Video';
            previewBtn.disabled = false;
        }
    });
    
    // ===== Helper Functions =====
    function extractVideoId(url) {
    	const regExp = /^(?:https?:\/\/)?(?:www\.|m\.)?(?:youtu\.be\/|youtube\.com\/(?:embed\/|v\/|watch\?v=|shorts\/|live\/|user\/\w+\/|attribution_link\?.*v%3D))([^#&?]{11})/;
    	const match = url.match(regExp);
    	return match ? match[1] : null;
    }    
    function showFlash(type, message) {
        const flash = document.createElement('div');
        flash.className = `alert ${type}`;
        flash.innerHTML = `
            <i class="fas fa-${type === 'error' ? 'exclamation-circle' : 'check-circle'}"></i>
            ${message}
        `;
        
        flashContainer.appendChild(flash);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            flash.style.animation = 'slideOut 0.4s forwards';
            setTimeout(() => {
                flash.remove();
            }, 400);
        }, 5000);
    }
    
    // ===== Download Button Setup =====
    function setupDownloadButton(filename) {
        // Remove any existing click handlers
        downloadBtn.onclick = null;
        
        // Set new handler
        downloadBtn.onclick = () => {
            // Create hidden iframe to trigger download
            const iframe = document.createElement('iframe');
            iframe.style.display = 'none';
            iframe.src = `/download/${encodeURIComponent(filename)}`;
            document.body.appendChild(iframe);
            
            // Remove iframe after download starts
            setTimeout(() => {
                document.body.removeChild(iframe);
            }, 5000);
        };
    }
    
    // ===== Form Submission =====
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Show modal
        showProgressModal();
        updateModalProgress(0, 'Starting download process...');
        
        // Get form data
        const formData = new FormData(form);
        const data = {
            link: formData.get('link'),
            ss: formData.get('ss'),
            to: formData.get('to'),
            output: formData.get('output'),
            format: formData.get('format')
        };
        
        // Simulate progress for demo
        if (data.link.includes('demo')) {
            simulateDemoProgress(data);
            return;
        }
        
        try {
            // Start download process
            const response = await fetch('/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data)
            });
            
            // Handle error responses
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.errors.join(', '));
            }
            
            // Process successful response
            const result = await response.json();
            trackProgress(result.request_id, result.filename);
        } catch (error) {
            hideProgressModal();
            showFlash('error', error.message);
        }
    });
    
    // ===== Video Preview =====
    previewPlaceholder.addEventListener('click', async function() {
        if (resultPlayer.src) {
            try {
                // Show loading indicator with animation
                videoLoading.style.display = 'flex';
                videoLoading.style.animation = 'fadeIn 0.3s ease-out';
                
                // Preload first 5MB before showing player
                await preloadVideo(resultPlayer.src);
                
                // Hide placeholder and show player with animation
                previewPlaceholder.style.animation = 'fadeOut 0.3s ease-out';
                setTimeout(() => {
                    previewPlaceholder.style.display = 'none';
                    resultPlayer.style.display = 'block';
                    resultPlayer.style.animation = 'fadeIn 0.6s ease-out';
                    videoLoading.style.display = 'none';
                    
                    // Start playback
                    const playPromise = resultPlayer.play();
                    
                    if (playPromise !== undefined) {
                        playPromise.catch(e => {
                            showFlash('info', 'Click the play button to start video');
                        });
                    }
                }, 300);
            } catch (e) {
                console.error('Preload failed:', e);
                videoLoading.style.display = 'none';
                showFlash('error', 'Failed to load video preview');
            }
        }
    });
    
    // ===== Helper Functions =====
    async function preloadVideo(url) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('GET', url);
            xhr.setRequestHeader('Range', 'bytes=0-5242880'); // Preload first 5MB
            
            xhr.onload = function() {
                if (xhr.status === 206) {
                    resolve();
                } else {
                    reject(new Error('Preload failed'));
                }
            };
            
            xhr.onerror = function() {
                reject(new Error('Preload failed'));
            };
            
            xhr.send();
        });
    }
    
    function simulateDemoProgress(data) {
        let progress = 0;
        const messages = [
            "Connecting to YouTube...",
            "Analyzing video content...",
            "Extracting HD streams...",
            "Processing clip segment...",
            "Finalizing your video..."
        ];
        
        const interval = setInterval(() => {
            progress += Math.floor(Math.random() * 8) + 3;
            if (progress > 100) progress = 100;
            
            updateModalProgress(progress, messages[Math.min(Math.floor(progress/20), 4)]);
            
            if (progress === 100) {
                clearInterval(interval);
                setTimeout(() => {
                    hideProgressModal();
                    
                    // Show result section
                    resultSection.style.display = 'block';
                    resultSection.style.animation = 'zoomIn 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
                    
                    // Show preview player with animation
                    previewPlaceholder.style.animation = 'fadeOut 0.3s ease-out';
                    setTimeout(() => {
                        previewPlaceholder.style.display = 'none';
                        resultPlayer.style.display = 'block';
                        resultPlayer.style.animation = 'fadeIn 0.6s ease-out';
                        
                        // Set a demo video source
                        resultPlayer.src = "https://assets.codepen.io/4175254/stock-video.mp4";
                        
                        // Set up download button
                        const demoFilename = data.output || 'your_clip.mp4';
                        setupDownloadButton(demoFilename);
                        
                        // Scroll to result
                        resultSection.scrollIntoView({ behavior: 'smooth' });
                    }, 300);
                }, 800);
            }
        }, 200);
    }
    
    function trackProgress(requestId, initialFilename) {
        let progressInterval = setInterval(async () => {
            try {
                const response = await fetch(`/progress/${requestId}`);
                const data = await response.json();
                
                // Update modal progress
                const progress = data.progress || 0;
                updateModalProgress(progress, data.message);
                
                // Handle different states
                if (data.status === 'completed') {
                    clearInterval(progressInterval);
                    setTimeout(() => {
                        hideProgressModal();
                        
                        // Show result section
                        resultSection.style.display = 'block';
                        resultSection.style.animation = 'zoomIn 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275)';
                        
                        // Set the video source
                        resultPlayer.src = `/stream/${data.filename}`;
                        
                        // Set up download button
                        setupDownloadButton(data.filename);
                        
                        // Scroll to result
                        resultSection.scrollIntoView({ behavior: 'smooth' });
                    }, 500);
                } 
                else if (data.status === 'error') {
                    clearInterval(progressInterval);
                    hideProgressModal();
                    showFlash('error', data.message);
                }
            } catch (error) {
                clearInterval(progressInterval);
                hideProgressModal();
                showFlash('error', `Error tracking progress: ${error.message}`);
            }
        }, 1000);
    }
    
    // ===== Initialize =====
    createParticles();
    
    // Setup new download button
    newDownloadBtn.onclick = () => {
        resultSection.style.animation = 'fadeOut 0.4s ease-out';
        setTimeout(() => {
            resultSection.style.display = 'none';
            form.reset();
            
            // Reset all video players
            previewPlayer.src = '';
            previewPlayer.load();
            resultPlayer.src = '';
            resultPlayer.load();
            
            // Hide preview container
            videoPreviewContainer.style.display = 'none';
            
            // Reset preview placeholder
            resultPlayer.style.display = 'none';
            previewPlaceholder.style.display = 'flex';
            previewPlaceholder.style.animation = 'fadeIn 0.6s ease-out';
            
            // Reset format selector
            formatSelector.querySelectorAll('.btn-format').forEach(b => {
                b.classList.remove('active');
            });
            formatSelector.querySelector('.btn-format[data-format="mp4"]').classList.add('active');
            formatInput.value = 'mp4';
            
            // Reset output edit flag
            isOutputEdited = false;
            
            // Scroll to top and focus on URL input
            window.scrollTo({ top: 0, behavior: 'smooth' });
            setTimeout(() => {
                youtubeUrlInput.focus();
            }, 500);
        }, 400);
    };
    
    // Initialize animations on elements when they come into view
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animate');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.1 });
    
    document.querySelectorAll('.card, .stat-card, .form-group').forEach(el => {
        observer.observe(el);
    });
    
    // Modal close handler
    modalClose.addEventListener('click', function() {
        hideProgressModal();
    });
});