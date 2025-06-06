// Main JavaScript for Quiz App

document.addEventListener('DOMContentLoaded', function() {
    // Enable Bootstrap tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Quiz timer functionality
    const timerElement = document.getElementById('quiz-timer');
    if (timerElement) {
        let timeLeft = parseInt(timerElement.dataset.timeLimit, 10) * 60; // Convert minutes to seconds
        
        const timerInterval = setInterval(function() {
            if (timeLeft <= 0) {
                clearInterval(timerInterval);
                document.getElementById('quiz-form').submit();
            }
            
            const minutes = Math.floor(timeLeft / 60);
            const seconds = timeLeft % 60;
            
            timerElement.textContent = `${minutes}:${seconds < 10 ? '0' : ''}${seconds}`;
            timeLeft--;
        }, 1000);
    }

    // Auto-save quiz answers
    const quizForm = document.getElementById('quiz-form');
    if (quizForm) {
        const formInputs = quizForm.querySelectorAll('input[type="radio"]');
        formInputs.forEach(input => {
            input.addEventListener('change', function() {
                const questionId = this.name.split('_')[1];
                const optionId = this.value;
                const userQuizId = quizForm.dataset.userQuizId;
                
                // Send answer to server
                fetch(`/api/quiz/${userQuizId}/submit-answer`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        question_id: questionId,
                        option_id: optionId
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        // Show saved indicator
                        const savedIndicator = document.createElement('span');
                        savedIndicator.className = 'badge bg-success ms-2 save-indicator';
                        savedIndicator.textContent = 'Saved';
                        
                        // Remove any existing indicators
                        const existingIndicator = this.parentNode.querySelector('.save-indicator');
                        if (existingIndicator) {
                            existingIndicator.remove();
                        }
                        
                        this.parentNode.appendChild(savedIndicator);
                        
                        // Remove indicator after 2 seconds
                        setTimeout(() => {
                            savedIndicator.remove();
                        }, 2000);
                    }
                })
                .catch(error => {
                    console.error('Error saving answer:', error);
                });
            });
        });
    }

    // Confirm delete actions
    const deleteButtons = document.querySelectorAll('.btn-delete');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item? This action cannot be undone.')) {
                e.preventDefault();
            }
        });
    });
});
