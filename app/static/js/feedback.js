/**
 * Automatic feedback loading and processing
 * Ensures feedback is loaded and displayed after form submission
 */

// Keep track of feedback processing attempts
let processingAttempts = 0;
let processingInProgress = false;
const MAX_PROCESSING_ATTEMPTS = 3;

// Process answer ID to ensure feedback is generated and displayed
function processAnswerFeedback(answerId) {
    console.log('Processing feedback for answer ID:', answerId);
    
    // Prevent duplicate processing attempts
    if (processingInProgress) {
        console.log('Already processing feedback, skipping duplicate request');
        return;
    }
    
    // Track that we're processing
    processingInProgress = true;
    processingAttempts++;
    
    // Show a loading indicator
    const feedbackElements = document.querySelectorAll('.chat-message.interviewer .message-content');
    const lastFeedbackElement = feedbackElements[feedbackElements.length - 1];
    
    if (lastFeedbackElement) {
        lastFeedbackElement.innerHTML = `
            <p><span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating feedback... (Attempt ${processingAttempts}/${MAX_PROCESSING_ATTEMPTS})</p>
        `;
    }
    
    // If we've tried too many times, just redirect to the feedback page
    if (processingAttempts > MAX_PROCESSING_ATTEMPTS) {
        console.log('Max processing attempts reached, redirecting to feedback page');
        window.location.href = `/feedback/answer/${answerId}`;
        return;
    }
    
    // Post to our new API endpoint to ensure feedback is generated
    fetch(`/api/process_answer/${answerId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        }
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`HTTP error ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Feedback processed:', data);
        processingInProgress = false;
        
        // Update the feedback display if successful
        if (data.success && data.has_feedback) {
            if (lastFeedbackElement) {
                // Update the feedback with the new content
                lastFeedbackElement.innerHTML = `
                    <p>${data.feedback}</p>
                    <p>${document.location.pathname.includes('next') ? 'Ready for the next question?' : 'That completes this session. Let\'s move on to the next part of the interview.'}</p>
                `;
            }
            
            // Update performance metrics if on feedback page
            updatePerformanceMetrics(answerId);
            
            // Reset processing attempts counter
            processingAttempts = 0;
        } else {
            // If no feedback yet, wait a moment and retry if we haven't exceeded the limit
            if (processingAttempts < MAX_PROCESSING_ATTEMPTS) {
                setTimeout(() => {
                    fetchAnswerDetails(answerId);
                }, 2000);
            } else {
                // If we've tried enough times, just redirect
                window.location.href = `/feedback/answer/${answerId}`;
            }
        }
    })
    .catch(error => {
        console.error('Error processing feedback:', error);
        processingInProgress = false;
        
        // If we've tried enough times, just redirect
        if (processingAttempts >= MAX_PROCESSING_ATTEMPTS) {
            window.location.href = `/feedback/answer/${answerId}`;
            return;
        }
        
        // If there's an error, just refresh from the server
        setTimeout(() => {
            fetchAnswerDetails(answerId);
        }, 3000);
    });
}

// Fetch answer details from the API
function fetchAnswerDetails(answerId) {
    // Increment the processing attempt counter
    processingAttempts++;
    console.log(`Fetching answer details (attempt ${processingAttempts}/${MAX_PROCESSING_ATTEMPTS})`);
    
    // If we've tried too many times, just redirect
    if (processingAttempts > MAX_PROCESSING_ATTEMPTS) {
        console.log('Max attempts reached, redirecting to feedback page');
        window.location.href = `/feedback/answer/${answerId}`;
        return;
    }
    
    // Show a loading indicator with attempt number
    const feedbackElements = document.querySelectorAll('.chat-message.interviewer .message-content');
    const lastFeedbackElement = feedbackElements[feedbackElements.length - 1];
    
    if (lastFeedbackElement) {
        lastFeedbackElement.innerHTML = `
            <p><span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Generating feedback... (Attempt ${processingAttempts}/${MAX_PROCESSING_ATTEMPTS})</p>
        `;
    }
    
    fetch(`/api/answer/${answerId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Answer details fetched:', data);
            processingInProgress = false;
            
            // Update the feedback display
            const feedbackElements = document.querySelectorAll('.chat-message.interviewer .message-content');
            const lastFeedbackElement = feedbackElements[feedbackElements.length - 1];
            
            if (lastFeedbackElement && data.feedback) {
                // Update the feedback with the fetched content
                lastFeedbackElement.innerHTML = `
                    <p>${data.feedback}</p>
                    <p>${document.location.pathname.includes('next') ? 'Ready for the next question?' : 'That completes this session. Let\'s move on to the next part of the interview.'}</p>
                `;
                
                // Reset the counter since we're successful
                processingAttempts = 0;
            } else if (lastFeedbackElement) {
                // Still no feedback, retry after a delay if we haven't hit the limit
                if (processingAttempts < MAX_PROCESSING_ATTEMPTS) {
                    setTimeout(() => {
                        fetchAnswerDetails(answerId);
                    }, 3000);
                } else {
                    // If we've tried too many times, just redirect
                    window.location.href = `/feedback/answer/${answerId}`;
                }
            }
            
            // Update performance metrics if on feedback page
            updatePerformanceMetrics(answerId);
        })
        .catch(error => {
            console.error('Error fetching answer details:', error);
            processingInProgress = false;
            
            // If we've hit the limit, redirect
            if (processingAttempts >= MAX_PROCESSING_ATTEMPTS) {
                window.location.href = `/feedback/answer/${answerId}`;
                return;
            }
            
            // Try again after a delay
            setTimeout(() => {
                fetchAnswerDetails(answerId);
            }, 3000);
        });
}

// Update performance metrics on the feedback page
function updatePerformanceMetrics(answerId) {
    // Only proceed if we have the metrics container
    const metricsContainer = document.querySelector('.performance-metrics');
    if (!metricsContainer) return;
    
    fetch(`/api/answer/${answerId}`)
        .then(response => response.json())
        .then(data => {
            // Update overall score
            const scoreElement = document.querySelector('.card-header .badge');
            if (scoreElement && data.score) {
                const score = Math.round(data.score);
                let bgClass = 'bg-danger';
                
                if (score >= 80) bgClass = 'bg-success';
                else if (score >= 60) bgClass = 'bg-primary';
                else if (score >= 40) bgClass = 'bg-warning';
                
                scoreElement.className = `badge ${bgClass}`;
                scoreElement.textContent = `${score}%`;
            }
            
            // Update individual metrics
            updateMetricProgress('completeness', data.completeness);
            updateMetricProgress('relevance', data.relevance);
            updateMetricProgress('structure', data.structure);
            updateMetricProgress('grammar', data.grammar_score);
            
            // Update grammar issues
            const grammarIssuesElement = document.querySelector('.grammar-issues');
            if (grammarIssuesElement && data.grammar_issues) {
                grammarIssuesElement.innerHTML = data.grammar_issues.replace(/\n/g, '<br>');
            }
            
            // Update improvement suggestions
            const suggestionsElement = document.querySelector('.improvement-suggestions');
            if (suggestionsElement && data.improvement_suggestions) {
                suggestionsElement.innerHTML = data.improvement_suggestions.replace(/\n/g, '<br>');
            }
        })
        .catch(error => {
            console.error('Error updating metrics:', error);
        });
}

// Update a specific metric progress bar
function updateMetricProgress(metricName, value) {
    if (!value) return;
    
    const progressElement = document.querySelector(`.metric-${metricName} .progress-bar`);
    if (progressElement) {
        const score = Math.round(value);
        progressElement.style.width = `${score}%`;
        progressElement.textContent = `${score}%`;
        
        // Update progress bar color based on score
        progressElement.className = 'progress-bar';
        if (score >= 80) progressElement.classList.add('bg-success');
        else if (score >= 60) progressElement.classList.add('bg-primary');
        else if (score >= 40) progressElement.classList.add('bg-warning');
        else progressElement.classList.add('bg-danger');
    }
}

// Initialize feedback processing when the page loads
document.addEventListener('DOMContentLoaded', function() {
    // Check if we're on a feedback page
    const url = window.location.pathname;
    const feedbackMatch = url.match(/\/feedback\/answer\/(\d+)/);
    
    if (feedbackMatch && feedbackMatch[1]) {
        const answerId = feedbackMatch[1];
        
        // Check if feedback exists, if not, process it
        const feedbackElement = document.querySelector('.chat-message.interviewer .message-content p');
        if (feedbackElement && feedbackElement.textContent.trim() === 'Thank you for your response. Let\'s move on to the next question.') {
            // No feedback yet, process it
            processAnswerFeedback(answerId);
        }
    }
    
    // For pages with auto-redirects, intercept the form submission
    const answerForm = document.getElementById('answerForm');
    if (answerForm) {
        answerForm.addEventListener('submit', function(event) {
            // Store the form submission timestamp to detect auto-submissions
            window.lastFormSubmission = Date.now();
        });
    }
});

// Global function to detect redirections to feedback page and auto-process if needed
(function() {
    let lastUrl = window.location.href;
    
    // Monitor for URL changes (redirects)
    const urlChangeInterval = setInterval(function() {
        if (window.location.href !== lastUrl) {
            const newUrl = window.location.href;
            lastUrl = newUrl;
            
            // Check if we were redirected to a feedback page
            const feedbackMatch = newUrl.match(/\/feedback\/answer\/(\d+)/);
            if (feedbackMatch && feedbackMatch[1]) {
                const answerId = feedbackMatch[1];
                
                // Check if this was an auto-submission (recent form submission)
                if (window.lastFormSubmission && (Date.now() - window.lastFormSubmission < 5000)) {
                    // This was likely an auto-submission, force-process the feedback
                    console.log('Auto-submission detected, processing feedback automatically');
                    
                    // Give a moment for the page to load
                    setTimeout(function() {
                        processAnswerFeedback(answerId);
                    }, 1000);
                }
            }
        }
    }, 500);
})();