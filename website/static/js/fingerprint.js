class AudioFingerprinter {
    constructor() {
        this.context = new AudioContext();
        this.analyzer = this.context.createAnalyser();
        this.analyzer.fftSize = 2048;
        this.bufferLength = this.analyzer.frequencyBinCount;
        this.dataArray = new Float32Array(this.bufferLength);
    }

    setupSource(audioElement) {
        const source = this.context.createMediaElementSource(audioElement);
        source.connect(this.analyzer);
        this.analyzer.connect(this.context.destination);
    }

    generateFingerprint() {
        this.analyzer.getFloatFrequencyData(this.dataArray);
        // Create fingerprint from strongest frequency components
        const peaks = [];
        for (let i = 0; i < this.bufferLength; i++) {
            if (this.dataArray[i] > -60) { // Threshold for significant frequencies
                peaks.push({freq: i, magnitude: this.dataArray[i]});
            }
        }
        // Sort by magnitude and take top N peaks
        peaks.sort((a, b) => b.magnitude - a.magnitude);
        return peaks.slice(0, 20).map(p => p.freq);
    }

    compareFingerprints(fp1, fp2, threshold = 0.7) {
        const matches = fp1.filter(f => fp2.includes(f));
        return matches.length / Math.min(fp1.length, fp2.length);
    }

    async findSegment(targetFingerprint, audioElement, expectedStart, maxSearch = 30) {
        return new Promise((resolve) => {
            let searchStart = Math.max(0, expectedStart - 10);
            let searchEnd = expectedStart + maxSearch;
            const threshold = 0.7;
            
            console.log(`Starting search from ${searchStart}s to ${searchEnd}s (expected: ${expectedStart}s)`);
            console.log(`Target fingerprint:`, targetFingerprint);
            
            const checkInterval = setInterval(() => {
                const currentFingerprint = this.generateFingerprint();
                const similarity = this.compareFingerprints(currentFingerprint, targetFingerprint);
                console.log(`At ${audioElement.currentTime.toFixed(2)}s:`, {
                    currentFingerprint: currentFingerprint.slice(0, 5) + '...',
                    similarity: similarity.toFixed(2)
                });
                
                if (similarity >= threshold) {
                    console.log(`Match found at ${audioElement.currentTime.toFixed(2)}s!`);
                    clearInterval(checkInterval);
                    resolve(audioElement.currentTime);
                    return;
                }

                if (audioElement.currentTime >= searchEnd) {
                    console.log(`Search timeout at ${audioElement.currentTime.toFixed(2)}s, falling back to expected start`);
                    clearInterval(checkInterval);
                    resolve(expectedStart);
                    return;
                }
            }, 100);

            audioElement.currentTime = searchStart;
            audioElement.play();
        });
    }
}
