const player = document.getElementById('audio-player');
const playButton = document.getElementById('play-button');
const pauseButton = document.getElementById('pause-button');
const prevButton = document.getElementById('prev-button');
const nextButton = document.getElementById('next-button');
const shuffleButton = document.getElementById('shuffle-button');
const segmentList = document.querySelector('.segment-list');
let segments = document.querySelectorAll('.segment-item');
let currentSegment = 0;

let firstPlay = true;

function updatePlayerSource() {
    player.src = segments[currentSegment].dataset.url;
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
        const nextSegment = segments[currentSegment];
        nextSegment.click();
    }
});

prevButton.addEventListener('click', () => {
    const currentStart = parseFloat(segments[currentSegment].dataset.start);
    if (player.currentTime - currentStart > 2) {
        segments[currentSegment].click();
    } else if (currentSegment > 0) {
        currentSegment--;
        const prevSegment = segments[currentSegment];
        prevSegment.click();
    }
});

shuffleButton.addEventListener('click', () => {
    const segmentsArray = Array.from(segments);
    for (let i = segmentsArray.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [segmentsArray[i], segmentsArray[j]] = [segmentsArray[j], segmentsArray[i]];
    }
    segmentList.innerHTML = '';
    segmentsArray.forEach(segment => {
        segmentList.appendChild(segment);
    });
    segments = document.querySelectorAll('.segment-item');
    currentSegment = 0;
    segments.forEach(s => s.classList.remove('playing'));
    segments[0].classList.add('playing');
    const start = parseFloat(segments[0].dataset.start);
    const end = parseFloat(segments[0].dataset.end);
    playSegment(start, end);
});

let currentListener = null;

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
                const nextSegment = segments[currentSegment];
                nextSegment.click();
            }
        }
    };

    currentListener = checkTime;
    player.addEventListener('timeupdate', checkTime);
}

segments.forEach((segment, index) => {
    segment.addEventListener('click', () => {
        segments.forEach(s => s.classList.remove('playing'));
        segment.classList.add('playing');
        currentSegment = index;
        updatePlayerSource();
        const start = parseFloat(segment.dataset.start);
        const end = parseFloat(segment.dataset.end);
        playSegment(start, end);
    });
});
