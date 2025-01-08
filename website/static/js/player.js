const player = document.getElementById('audio-player');
const playButton = document.getElementById('play-button');
const pauseButton = document.getElementById('pause-button');
const prevButton = document.getElementById('prev-button');
const nextButton = document.getElementById('next-button');
const shuffleButton = document.getElementById('shuffle-button');
const segmentList = document.querySelector('.segment-list');
let segments = document.querySelectorAll('.segment-item');
let currentSegment = 0;
let shuffledIndices = Array.from(segments.keys()); // Array of original indices

let firstPlay = true;
const searchInput = document.getElementById('search-input');
const searchContainer = document.getElementById('search-container');
const searchToggleButton = document.getElementById('search-toggle-button');
const allSegments = Array.from(segments);

const visibleCount = document.getElementById('visible-count');

searchToggleButton.addEventListener('click', () => {
    const isHidden = searchContainer.style.display === 'none';
    searchContainer.style.display = isHidden ? 'block' : 'none';
    if (isHidden) {
        searchInput.focus();
    }
});

// Initialize counter
visibleCount.textContent = allSegments.length;

function normalizeText(text) {
    // Replace hyphens with spaces and remove other special characters
    return text.toLowerCase()
              .replace(/[-]/g, ' ')
              .replace(/[^\w\s]/g, '');
}

searchInput.addEventListener('input', (e) => {
    const searchTerm = normalizeText(e.target.value);
    let count = 0;
    
    allSegments.forEach(segment => {
        const text = normalizeText(segment.querySelector('.segment-text').textContent);
        if (text.includes(searchTerm)) {
            segment.style.display = '';
            count++;
        } else {
            segment.style.display = 'none';
        }
    });
    
    visibleCount.textContent = count;
});

function updatePlayerSource() {
    const segment = segments[shuffledIndices[currentSegment]];
    console.log('Updating player source for segment:', segment);
    console.log('Segment URL:', segment.dataset.url);
    player.src = segment.dataset.url;
}

playButton.addEventListener('click', () => {
    if (firstPlay) {
        segments[0].classList.add('playing');
        updatePlayerSource();
        const start = parseFloat(segments[0].dataset.start);
        const end = parseFloat(segments[0].dataset.end);
        playSegment(start, end);
        firstPlay = false;
    } else {
        player.play();
    }
});

pauseButton.addEventListener('click', () => {
    player.pause();
});

nextButton.addEventListener('click', () => {
    if (currentSegment < segments.length - 1) {
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
        currentSegment--;
        const prevSegment = segments[shuffledIndices[currentSegment]];
        prevSegment.click();
    }
});

shuffleButton.addEventListener('click', () => {
    console.log('Shuffle button clicked');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    
    // Shuffle the indices array
    for (let i = shuffledIndices.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffledIndices[i], shuffledIndices[j]] = [shuffledIndices[j], shuffledIndices[i]];
    }
    console.log('Shuffled indices:', shuffledIndices);
    
    // Reorder the DOM elements based on shuffled indices
    const fragment = document.createDocumentFragment();
    shuffledIndices.forEach(index => {
        fragment.appendChild(segments[index]);
    });
    segmentList.innerHTML = '';
    segmentList.appendChild(fragment);
    
    // Reset playback state
    currentSegment = 0;
    segments.forEach(s => s.classList.remove('playing'));
    const firstSegment = segments[shuffledIndices[0]];
    console.log('First segment after shuffle:', firstSegment);
    
    firstSegment.classList.add('playing');
    const start = parseFloat(firstSegment.dataset.start);
    const end = parseFloat(firstSegment.dataset.end);
    console.log('Playing segment from', start, 'to', end);
    
    try {
        updatePlayerSource();
        console.log('Player source updated');
        playSegment(start, end);
        console.log('Play segment called');
    } catch (error) {
        console.error('Error during shuffle playback:', error);
    }
});

let currentListener = null;

function isElementVisible(element) {
    const rect = element.getBoundingClientRect();
    const headerHeight = document.querySelector('.fixed-header').offsetHeight;
    return rect.top >= headerHeight && rect.bottom <= window.innerHeight;
}

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

function playSegment(start, end) {
    if (currentListener) {
        player.removeEventListener('timeupdate', currentListener);
        currentListener = null;
    }

    player.currentTime = start;
    player.play();

    const stopAt = end;
    const checkTime = () => {
        if (player.currentTime >= stopAt) {
            player.pause();
            player.removeEventListener('timeupdate', checkTime);
            currentListener = null;

            if (currentSegment < segments.length - 1) {
                currentSegment++;
                const nextSegment = segments[shuffledIndices[currentSegment]];
                scrollToSegment(nextSegment);
                nextSegment.click();
            }
        }
    };

    currentListener = checkTime;
    player.addEventListener('timeupdate', checkTime);
}

segments.forEach((segment, index) => {
    segment.addEventListener('click', (event) => {
        // Check if the click was on a debug link
        if (event.target.closest('.debug-link')) {
            return;
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
