document.addEventListener("DOMContentLoaded", () => {
    const loginTab = document.getElementById("loginTab");
    const signupTab = document.getElementById("signupTab");
    const loginForm = document.getElementById("loginForm");
    const signupForm = document.getElementById("signupForm");

    // Only run if login/signup elements exist (i.e., we're on the login page)
    if (!loginTab || !signupTab || !loginForm || !signupForm) {
        return;
    }

    // Toggle between Login / Sign Up
    const switchToLogin = () => {
        loginTab.classList.add("active");
        signupTab.classList.remove("active");
        loginForm.classList.add("active");
        signupForm.classList.remove("active");
    };

    const switchToSignup = () => {
        signupTab.classList.add("active");
        loginTab.classList.remove("active");
        signupForm.classList.add("active");
        loginForm.classList.remove("active");
    };

    loginTab.addEventListener("click", switchToLogin);
    signupTab.addEventListener("click", switchToSignup);

    // Flash mesagge close
    const flashCloseButtons = document.querySelectorAll('.flash-close');
    flashCloseButtons.forEach(button => {
        button.addEventListener('click', function() {
            const flashMessage = this.closest('.flash-message');
            if (flashMessage) {
                flashMessage.style.animation = 'slideOutRight 0.3s ease-in forwards';
                setTimeout(() => {
                    flashMessage.remove();
                }, 300);
            }
        });
    });

    // Otomatic close
    const flashMessages = document.querySelectorAll('.flash-message');
    flashMessages.forEach(message => {
        setTimeout(() => {
            if (message.parentNode) {
                message.style.animation = 'slideOutRight 0.3s ease-in forwards';
                setTimeout(() => {
                    if (message.parentNode) {
                        message.remove();
                    }
                }, 300);
            }
        }, 5000);
    });
});
