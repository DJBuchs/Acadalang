function handleButtonClick(currentLang) {
    fetch(`/switch-language/${currentLang}`, { method: 'POST' })
        .then(response => response.json())
        .then(data => {
            window.location.href = data.redirect_url;
        })
        .catch(error => console.error('Error:', error));
}

// Usage
buttons.translate.addEventListener('click', () => handleButtonClick('english'));
['easy', 'medium', 'hard'].forEach(difficulty => {
    buttons[difficulty].addEventListener('click', () => handleButtonClick('hebrew'));
});