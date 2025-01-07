class AudioFingerprinter {
    constructor() {
        this.context = new AudioContext();
        this.analyzer = this.context.createAnalyser();
        this.analyzer.fftSize = 2048;
        this.analyzer.smoothingTimeConstant = 0; // Disable smoothing
        this.bufferLength = this.analyzer.frequencyBinCount;
        this.dataArray = new Float32Array(this.bufferLength);
    }

    setupSource(audioElement) {
        const source = this.context.createMediaElementSource(audioElement);
        source.connect(this.analyzer);
        this.analyzer.connect(this.context.destination);
    }

    generateFingerprint() {
        // Get current frequency data
        this.analyzer.getFloatFrequencyData(this.dataArray);
        
        // Only use first half of FFT bins to match rfft behavior
        const peaks = [];
        for (let i = 0; i < this.bufferLength/2; i++) {
            if (this.dataArray[i] > -60) {
                peaks.push({freq: i, magnitude: this.dataArray[i]});
            }
        }
        
        peaks.sort((a, b) => b.magnitude - a.magnitude);
        return peaks.slice(0, 20).map(p => p.freq);
    }

    compareFingerprints(fp1, fp2, threshold = 0.7) {
        const matches = fp1.filter(f => fp2.includes(f));
        return matches.length / Math.min(fp1.length, fp2.length);
    }

    async findSegment(targetFingerprint, audioElement, expectedStart, maxSearch = 30) {
        return new Promise((resolve) => {
            // Start with tight window around expected start
            let searchStart = Math.max(0, expectedStart - 5);
            let searchEnd = expectedStart + 5;
            let phase = 1;
            let bestMatch = null;
            const threshold = 0.7;
            
            console.log(`Starting phase ${phase} search from ${searchStart}s to ${searchEnd}s`);
            
            const checkInterval = setInterval(() => {
                const currentFingerprint = this.generateFingerprint();
                const similarity = this.compareFingerprints(currentFingerprint, targetFingerprint);
                
                if (similarity >= threshold) {
                    if (similarity > 0.9) {
                        console.log(`Strong match found at ${audioElement.currentTime.toFixed(2)}s!`);
                        clearInterval(checkInterval);
                        resolve(audioElement.currentTime);
                        return;
                    }
                    if (!bestMatch || similarity > bestMatch.similarity) {
                        bestMatch = {time: audioElement.currentTime, similarity};
                    }
                }

                if (audioElement.currentTime >= searchEnd) {
                    if (phase === 1 && !bestMatch) {
                        // Expand search window
                        phase = 2;
                        searchStart = Math.max(0, expectedStart - 10);
                        searchEnd = expectedStart + maxSearch;
                        console.log(`Starting phase ${phase} search from ${searchStart}s to ${searchEnd}s`);
                        audioElement.currentTime = searchStart;
                    } else {
                        clearInterval(checkInterval);
                        resolve(bestMatch ? bestMatch.time : expectedStart);
                    }
                } else {
                    audioElement.currentTime += 0.5; // Half second jumps
                }
            }, 250);

            audioElement.currentTime = searchStart;
            audioElement.play();
        });
    }
}
