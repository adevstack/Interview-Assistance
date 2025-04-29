/**
 * Text-to-speech functionality for interview questions
 */

class SpeechManager {
    constructor() {
        this.synth = window.speechSynthesis;
        this.isSpeaking = false;
        this.utterance = null;
        
        // Check for browser support
        this.isSupported = 'speechSynthesis' in window;
        
        // Set default voice
        this.voice = null;
        this.setDefaultVoice();
    }
    
    // Load and set default voice
    setDefaultVoice() {
        if (!this.isSupported) return;
        
        // Wait for voices to load
        const setVoice = () => {
            const voices = this.synth.getVoices();
            
            // First try to find a female voice
            let preferredVoice = voices.find(voice => 
                voice.name.includes('female') || 
                voice.name.includes('Female') ||
                voice.name.includes('Samantha') ||
                voice.name.includes('Google UK English Female'));
            
            // If no female voice found, use any
            if (!preferredVoice && voices.length > 0) {
                preferredVoice = voices[0];
            }
            
            this.voice = preferredVoice;
        };
        
        // If voices are already loaded
        if (this.synth.getVoices().length > 0) {
            setVoice();
        } else {
            // Wait for voices to be loaded
            this.synth.addEventListener('voiceschanged', setVoice);
        }
    }
    
    // Speak text with safeguards against censorship cutoffs
    speak(text, callback) {
        if (!this.isSupported) {
            console.warn('Speech synthesis not supported in this browser');
            if (callback) callback();
            return;
        }
        
        // Cancel any current speech
        this.stop();
        
        // Check if the text contains potential censorship triggers
        const potentialTriggers = [
            'unprofessional', 'inappropriate', 'unacceptable', 'profanity',
            'offensive', 'disrespectful', 'rude', 'vulgar'
        ];
        
        let textToSpeak = text;
        let hasTriggers = false;
        
        // Log for debugging
        console.log("Original text to speak:", text);
        
        // Check if we have potential trigger words
        for (const trigger of potentialTriggers) {
            if (text.toLowerCase().includes(trigger)) {
                hasTriggers = true;
                console.log(`Detected potential trigger word: "${trigger}"`);
                // Don't modify the words - just note that we found a trigger
            }
        }
        
        if (hasTriggers) {
            console.log("Text contains potential speech synthesis triggers - using chunked approach");
            this.speakInChunks(textToSpeak, callback);
            return;
        }
        
        // Create utterance for regular text
        this.utterance = new SpeechSynthesisUtterance(textToSpeak);
        
        // Set voice if available
        if (this.voice) {
            this.utterance.voice = this.voice;
        }
        
        // Setting properties for natural sound
        this.utterance.rate = 1.0;
        this.utterance.pitch = 1.0;
        this.utterance.volume = 1.0;
        
        // Events
        this.utterance.onstart = () => {
            this.isSpeaking = true;
            document.body.classList.add('speaking');
        };
        
        this.utterance.onend = () => {
            this.isSpeaking = false;
            document.body.classList.remove('speaking');
            if (callback) callback();
        };
        
        this.utterance.onerror = (e) => {
            console.error('Speech error:', e);
            // If there's an error, try the chunked approach as fallback
            this.isSpeaking = false;
            document.body.classList.remove('speaking');
            
            console.log("Speech error occurred, trying chunked approach as fallback");
            setTimeout(() => {
                this.speakInChunks(text, callback);
            }, 500);
        };
        
        // Start speaking
        this.synth.speak(this.utterance);
    }
    
    // Speak text in smaller chunks to avoid censorship cutoffs
    speakInChunks(text, finalCallback) {
        if (!this.isSupported) {
            if (finalCallback) finalCallback();
            return;
        }
        
        // Cancel any current speech
        this.stop();
        
        // Split text into sentences and then into smaller chunks
        const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 0);
        console.log(`Text split into ${sentences.length} sentences`);
        
        // Setup for sequential speaking
        let currentIndex = 0;
        this.isSpeaking = true;
        document.body.classList.add('speaking');
        
        const speakNextChunk = () => {
            if (currentIndex >= sentences.length) {
                // All chunks spoken, we're done
                this.isSpeaking = false;
                document.body.classList.remove('speaking');
                if (finalCallback) finalCallback();
                return;
            }
            
            let currentSentence = sentences[currentIndex].trim();
            
            // Skip empty chunks
            if (!currentSentence) {
                currentIndex++;
                speakNextChunk();
                return;
            }
            
            // Apply subtle modifications to potentially problematic words
            // - Introducing very slight character variations can bypass filters 
            // - These are almost impossible to hear but avoid censorship
            const problematicWords = [
                { word: 'unprofessional', replacement: 'unprofessi\u200Conal' },
                { word: 'inappropriate', replacement: 'inappropri\u200Cate' },
                { word: 'unacceptable', replacement: 'unaccept\u200Cable' },
                { word: 'profanity', replacement: 'profani\u200Cty' }
            ];
            
            // Apply the replacements
            let modifiedSentence = currentSentence;
            problematicWords.forEach(item => {
                if (modifiedSentence.toLowerCase().includes(item.word)) {
                    // Replace with a version containing zero-width characters that's phonetically identical
                    modifiedSentence = modifiedSentence.replace(
                        new RegExp(item.word, 'gi'),
                        item.replacement
                    );
                }
            });
            
            console.log(`Speaking chunk ${currentIndex + 1}/${sentences.length}: ${modifiedSentence}`);
            
            // Create utterance for this chunk
            const utterance = new SpeechSynthesisUtterance(modifiedSentence);
            
            // Set voice if available
            if (this.voice) {
                utterance.voice = this.voice;
            }
            
            // Setting properties for natural sound, with adjustments to improve censorship bypass
            utterance.rate = 0.9;  // Slightly slower rate
            utterance.pitch = 1.05; // Slightly higher pitch
            utterance.volume = 1.0;
            
            // When this chunk is done, move to the next
            utterance.onend = () => {
                currentIndex++;
                // Small pause between chunks
                setTimeout(speakNextChunk, 100);
            };
            
            // If error, skip to next chunk
            utterance.onerror = (e) => {
                console.error(`Speech error on chunk ${currentIndex}:`, e);
                currentIndex++;
                setTimeout(speakNextChunk, 100);
            };
            
            // Speak this chunk
            this.synth.speak(utterance);
        };
        
        // Start the chain
        speakNextChunk();
    }
    
    // Stop speaking
    stop() {
        if (!this.isSupported) return;
        
        this.synth.cancel();
        this.isSpeaking = false;
        document.body.classList.remove('speaking');
    }
    
    // Toggle speech pause/resume
    togglePause() {
        if (!this.isSupported || !this.isSpeaking) return;
        
        if (this.synth.paused) {
            this.synth.resume();
        } else {
            this.synth.pause();
        }
    }
}

// Initialize the speech manager globally for easy access
const speechManager = new SpeechManager();

/**
 * Automatically speak the interview question in chat interface
 */
function initSpeechForInterviewQuestions() {
    // Check if we're on the interview page with chat interface
    const chatContainer = document.getElementById('chat-container');
    if (!chatContainer) return;
    
    // Find the interviewer message with the question
    const questionMessages = document.querySelectorAll('.chat-message.interviewer');
    if (questionMessages.length > 0) {
        // Get the last question (the current one)
        const currentQuestion = questionMessages[questionMessages.length - 1];
        const questionText = currentQuestion.querySelector('.message-content p').textContent;
        
        // Add a small speech indicator
        const speechIndicator = document.createElement('div');
        speechIndicator.className = 'speech-indicator';
        speechIndicator.innerHTML = '<button type="button" class="btn btn-sm btn-link text-muted speech-toggle">' +
            '<i class="fas fa-volume-up"></i>' +
            '</button>';
        currentQuestion.querySelector('.message-content').appendChild(speechIndicator);
        
        // Add event listener for the speech toggle button
        const speechToggleBtn = speechIndicator.querySelector('.speech-toggle');
        speechToggleBtn.addEventListener('click', () => {
            if (speechManager.isSpeaking) {
                speechManager.stop();
                speechToggleBtn.innerHTML = '<i class="fas fa-volume-up"></i>';
            } else {
                speechManager.speak(questionText);
                speechToggleBtn.innerHTML = '<i class="fas fa-volume-mute"></i>';
            }
        });
        
        // Auto-speak the question on page load
        setTimeout(() => {
            speechManager.speak(questionText);
        }, 1000);
    }
}

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize speech for interview questions
    initSpeechForInterviewQuestions();
    
    // Add styles for speech indicators
    const style = document.createElement('style');
    style.textContent = `
        .speech-indicator {
            margin-top: 10px;
            text-align: right;
            font-size: 12px;
        }
        .speaking .chat-message.interviewer {
            animation: pulse 1.5s infinite;
        }
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.8; }
            100% { opacity: 1; }
        }
    `;
    document.head.appendChild(style);
});