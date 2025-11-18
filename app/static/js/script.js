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

  // Optional: Add form validation or loading states here in the future
  loginForm.addEventListener("submit", (e) => {
    // Form will submit naturally to Flask backend
    console.log("Login form submitting...");
  });

  signupForm.addEventListener("submit", (e) => {
    // Form will submit naturally to Flask backend
    console.log("Signup form submitting...");
  });
});
