/**
 * Audio player controller for AMA episode segments
 * Handles playback, navigation, filtering and error handling for audio segments
 */
const player = document.getElementById('audio-player');
const playPauseButton = document.getElementById('play-pause-button');
const prevButton = document.getElementById('prev-button');
const nextButton = document.getElementById('next-button');
const shuffleButton = document.getElementById('shuffle-button');
const segmentList = document.querySelector('.segment-list');
let segments = document.querySelectorAll('.segment-item');
let currentSegment = 0; // Index of currently playing segment
let shuffledIndices = Array.from(segments.keys()); // Array of original indices for shuffle functionality

/**
 * Get currently visible segments after filtering
 * @returns {Array} Array of visible segment elements
 */
function getVisibleSegments() {
    return Array.from(segments).filter(segment => 
        segment.style.display !== 'none'
    );
}

let firstPlay = true;

// Update play/pause button icon based on player state
player.addEventListener('play', () => {
    playPauseButton.querySelector('i').classList.replace('fa-play', 'fa-pause');
    playPauseButton.classList.add('active');
});

player.addEventListener('pause', () => {
    playPauseButton.querySelector('i').classList.replace('fa-pause', 'fa-play');
    playPauseButton.classList.remove('active');
});

// Add error event listener to player
player.addEventListener('error', (e) => {
    handlePlayerError(e);
});
const searchInput = document.getElementById('search-input');
const searchContainer = document.getElementById('search-container');
const searchToggleButton = document.getElementById('search-toggle-button');
const allSegments = Array.from(segments);

const visibleCount = document.getElementById('visible-count');

// Check for q parameter in URL
const urlParams = new URLSearchParams(window.location.search);
const searchQuery = urlParams.get('q');
if (searchQuery) {
    searchInput.value = searchQuery;
    searchContainer.style.display = 'block';
    searchToggleButton.classList.add('active');
    filterSegments();
}

searchToggleButton.addEventListener('click', () => {
    const isHidden = searchContainer.style.display === 'none';
    searchContainer.style.display = isHidden ? 'block' : 'none';
    searchToggleButton.classList.toggle('active', isHidden);
    if (isHidden) {
        searchInput.focus();
    }
});

// Initialize counter
visibleCount.textContent = allSegments.length;

/**
 * Normalize text for search comparisons
 * @param {string} text - Input text to normalize
 * @returns {string} Normalized text in lowercase with special characters removed
 */
function normalizeText(text) {
    // Replace hyphens with spaces and remove other special characters
    return text.toLowerCase()
              .replace(/[-]/g, ' ')
              .replace(/[^\w\s]/g, '');
}

const episodeFilter = document.getElementById('episode-filter');

/**
 * Filter segments based on search term and episode selection
 * Updates visible segment count and display
 */
function filterSegments() {
    const searchTerm = normalizeText(searchInput.value);
    const selectedEpisode = episodeFilter.value;
    let count = 0;
    
    allSegments.forEach(segment => {
        const text = normalizeText(segment.querySelector('.segment-text').textContent);
        const date = segment.querySelector('.segment-date').textContent.trim();
        
        const matchesSearch = text.includes(searchTerm);
        const matchesEpisode = !selectedEpisode || segment.querySelector('.segment-date').getAttribute('data-full-date') === selectedEpisode;
        
        if (matchesSearch && matchesEpisode) {
            segment.style.display = '';
            count++;
        } else {
            segment.style.display = 'none';
        }
    });
    
    visibleCount.textContent = count;
}

episodeFilter.addEventListener('change', filterSegments);
searchInput.addEventListener('input', filterSegments);

const clearFiltersButton = document.getElementById('clear-filters');
clearFiltersButton.addEventListener('click', () => {
    searchInput.value = '';
    episodeFilter.value = '';
    filterSegments();
    searchInput.focus();
});

/**
 * Handle audio player errors with user-friendly messages
 * @param {Error} error - The error object from the audio player
 */
function handlePlayerError(error) {
    console.error('Audio playback error:', error);
    
    const segment = segments[shuffledIndices[currentSegment]];
    
    // Reset duration display
    const durationElement = segment.querySelector('.segment-duration');
    const start = parseFloat(segment.dataset.start);
    const end = parseFloat(segment.dataset.end);
    durationElement.textContent = formatTime(end - start);
    
    // Remove any existing error messages
    const existingError = segment.querySelector('.error-message');
    if (existingError) {
        existingError.remove();
    }
    
    // Create and insert error message
    const errorDiv = document.createElement('div');
    errorDiv.className = 'error-message';
    
    let message = 'Sorry, this audio segment is no longer available.';
    if (error.name === 'MediaError') {
        switch (error.code) {
            case MediaError.MEDIA_ERR_NETWORK:
                message = 'A network error occurred while loading the audio.';
                break;
            case MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED:
                message = 'This audio segment is no longer available.';
                break;
        }
    }
    
    errorDiv.textContent = message;
    segment.appendChild(errorDiv);
    
    // Only auto-advance if the player is not paused
    if (!player.paused && currentSegment < segments.length - 1) {
        setTimeout(() => {
            // Double check we're still playing before advancing
            if (!player.paused) {
                currentSegment++;
                const nextSegment = segments[shuffledIndices[currentSegment]];
                nextSegment.click();
            }
        }, 3000);
    }
}

/**
 * Update audio player source to current segment's URL
 * Handles errors if segment URL is invalid
 */
function updatePlayerSource() {
    const segment = segments[shuffledIndices[currentSegment]];
    console.log('Updating player source for segment:', segment);
    console.log('Segment URL:', segment.dataset.url);
    try {
        player.src = segment.dataset.url;
    } catch (error) {
        handlePlayerError(error);
    }
}

playPauseButton.addEventListener('click', () => {
    if (player.paused) {
        if (firstPlay) {
            const visibleSegments = getVisibleSegments();
            if (visibleSegments.length === 0) return;
            
            segments.forEach(s => s.classList.remove('playing'));
            visibleSegments[0].classList.add('playing');
            currentSegment = shuffledIndices.indexOf(Array.from(segments).indexOf(visibleSegments[0]));
            updatePlayerSource();
            const start = parseFloat(visibleSegments[0].dataset.start);
            const end = parseFloat(visibleSegments[0].dataset.end);
            playSegment(start, end);
            firstPlay = false;
        } else {
            player.play();
        }
        playPauseButton.querySelector('i').classList.replace('fa-play', 'fa-pause');
    } else {
        player.pause();
        playPauseButton.querySelector('i').classList.replace('fa-pause', 'fa-play');
    }
});

nextButton.addEventListener('click', () => {
    if (currentSegment < segments.length - 1) {
        // Reset duration of current segment before moving to next
        resetDurationDisplay(segments[shuffledIndices[currentSegment]]);
        currentSegment++;
        const nextSegment = segments[shuffledIndices[currentSegment]];
        nextSegment.click();
    }
});

prevButton.addEventListener('click', () => {
    const currentStart = parseFloat(segments[shuffledIndices[currentSegment]].dataset.start);
    if (player.currentTime - currentStart > 2) {
        segments[shuffledIndices[currentSegment]].click();
    } else if (currentSegment > 0) {
        // Reset duration of current segment before moving to previous
        resetDurationDisplay(segments[shuffledIndices[currentSegment]]);
        currentSegment--;
        const prevSegment = segments[shuffledIndices[currentSegment]];
        prevSegment.click();
    }
});

shuffleButton.addEventListener('click', () => {
    console.log('Shuffle button clicked');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    const visibleSegments = getVisibleSegments();
    if (visibleSegments.length === 0) return;
    
    // Create array of visible indices
    const visibleIndices = visibleSegments.map(segment => 
        Array.from(segments).indexOf(segment)
    );
    
    // Shuffle only the visible indices
    for (let i = visibleIndices.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [visibleIndices[i], visibleIndices[j]] = [visibleIndices[j], visibleIndices[i]];
    }
    
    // Update shuffledIndices to put visible segments first
    shuffledIndices = [
        ...visibleIndices,
        ...shuffledIndices.filter(index => !visibleIndices.includes(index))
    ];
    
    // Reorder the DOM elements based on shuffled indices
    const fragment = document.createDocumentFragment();
    shuffledIndices.forEach(index => {
        fragment.appendChild(segments[index]);
    });
    segmentList.innerHTML = '';
    segmentList.appendChild(fragment);
    
    // Reset playback state
    resetDurationDisplay(segments[shuffledIndices[currentSegment]]);
    currentSegment = 0;
    segments.forEach(s => s.classList.remove('playing'));
    const firstSegment = segments[shuffledIndices[0]];
    
    firstSegment.classList.add('playing');
    const start = parseFloat(firstSegment.dataset.start);
    const end = parseFloat(firstSegment.dataset.end);
    
    try {
        updatePlayerSource();
        playSegment(start, end);
    } catch (error) {
        console.error('Error during shuffle playback:', error);
    }
});

let currentListener = null;

/**
 * Format seconds into MM:SS display format
 * @param {number} seconds - Time in seconds
 * @returns {string} Formatted time string
 */
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`;
}

/**
 * Reset duration display for a segment to its original value
 * @param {Element} segment - The segment element to reset
 */
function resetDurationDisplay(segment) {
    const durationElement = segment.querySelector('.segment-duration');
    const start = parseFloat(segment.dataset.start);
    const end = parseFloat(segment.dataset.end);
    durationElement.innerHTML = `${formatTime(end - start)} <i class="fas fa-external-link-alt"></i>`;
}

/**
 * Check if element is visible in viewport (below header)
 * @param {Element} element - DOM element to check
 * @returns {boolean} True if element is visible
 */
function isElementVisible(element) {
    const rect = element.getBoundingClientRect();
    const headerHeight = document.querySelector('.fixed-header').offsetHeight;
    return rect.top >= headerHeight && rect.bottom <= window.innerHeight;
}

/**
 * Smooth scroll to segment, accounting for fixed header
 * @param {Element} segment - Segment element to scroll to
 */
function scrollToSegment(segment) {
    if (isElementVisible(segments[shuffledIndices[currentSegment]])) {
        const headerHeight = document.querySelector('.fixed-header').offsetHeight;
        const elementTop = segment.getBoundingClientRect().top + window.pageYOffset;
        window.scrollTo({
            top: elementTop - headerHeight - 20,
            behavior: 'smooth'
        });
    }
}

/**
 * Play audio segment with smooth fade out and auto-advance
 * @param {number} start - Start time in seconds
 * @param {number} end - End time in seconds
 */
function playSegment(start, end) {
    if (currentListener) {
        player.removeEventListener('timeupdate', currentListener);
        currentListener = null;
    }

    const segment = segments[shuffledIndices[currentSegment]];
    const durationElement = segment.querySelector('.segment-duration');
    const originalDurationText = durationElement.textContent;
    const totalDuration = end - start;
    const fadeOutDuration = 0.75; // 750ms fade out

    player.currentTime = start;
    player.volume = 1;
    player.play();

    const stopAt = end;
    const checkTime = () => {
        if (player.currentTime >= stopAt) {
            player.pause();
            player.volume = 1; // Reset volume for next segment
            player.removeEventListener('timeupdate', checkTime);
            currentListener = null;
            durationElement.innerHTML = originalDurationText;

            if (currentSegment < segments.length - 1) {
                // Find next visible segment
                let nextSegmentIndex = currentSegment + 1;
                while (nextSegmentIndex < segments.length && 
                       segments[shuffledIndices[nextSegmentIndex]].style.display === 'none') {
                    nextSegmentIndex++;
                }
                
                if (nextSegmentIndex < segments.length) {
                    currentSegment = nextSegmentIndex;
                    const nextSegment = segments[shuffledIndices[currentSegment]];
                    scrollToSegment(nextSegment);
                    nextSegment.click();
                }
            }
        } else {
            const remaining = end - player.currentTime;
            durationElement.textContent = formatTime(remaining);

            // Start fading out during the last 750ms
            if (remaining <= fadeOutDuration) {
                const startVolume = 1.0;
                const endVolume = 0.3;
                const fadeProgress = remaining / fadeOutDuration;
                player.volume = startVolume * fadeProgress + endVolume * (1 - fadeProgress);
            }
        }
    };

    currentListener = checkTime;
    player.addEventListener('timeupdate', checkTime);
}

segments.forEach((segment, index) => {
    segment.addEventListener('click', (event) => {
        // Check if the click was on a debug link or duration link
        if (event.target.closest('.debug-link') || event.target.closest('.segment-duration')) {
            return;
        }
        
        // Reset duration of current segment before changing
        if (currentSegment !== shuffledIndices.indexOf(index)) {
            resetDurationDisplay(segments[shuffledIndices[currentSegment]]);
        }
        
        segments.forEach(s => s.classList.remove('playing'));
        segment.classList.add('playing');
        currentSegment = shuffledIndices.indexOf(index);
        updatePlayerSource();
        scrollToSegment(segment);
        const start = parseFloat(segment.dataset.start);
        const end = parseFloat(segment.dataset.end);
        playSegment(start, end);
    });
});
