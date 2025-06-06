// Theme toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    // Check for saved theme preference or use light mode as default
    const savedTheme = localStorage.getItem('theme');
    
    // Set initial theme - always default to light if no saved preference
    if (savedTheme) {
        document.documentElement.setAttribute('data-theme', savedTheme);
        document.body.setAttribute('data-theme', savedTheme);
        updateToggleIcon(savedTheme);
    } else {
        document.documentElement.setAttribute('data-theme', 'light');
        document.body.setAttribute('data-theme', 'light');
        updateToggleIcon('light');
    }
    
    // Add event listener to theme toggle button
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        themeToggle.addEventListener('click', function() {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            
            // Update theme
            document.documentElement.setAttribute('data-theme', newTheme);
            document.body.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            
            // Update icon
            updateToggleIcon(newTheme);
        });
    }
});

// Update the toggle icon based on current theme
function updateToggleIcon(theme) {
    const themeToggle = document.getElementById('theme-toggle');
    if (themeToggle) {
        if (theme === 'dark') {
            themeToggle.innerHTML = '<i class="fas fa-sun"></i>';
            themeToggle.setAttribute('title', 'Switch to light mode');
        } else {
            themeToggle.innerHTML = '<i class="fas fa-moon"></i>';
            themeToggle.setAttribute('title', 'Switch to dark mode');
        }
    }
}
