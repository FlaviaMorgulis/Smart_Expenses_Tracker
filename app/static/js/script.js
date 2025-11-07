document.addEventListener("DOMContentLoaded", () => {
  const loginTab = document.getElementById("loginTab");
  const signupTab = document.getElementById("signupTab");
  const loginForm = document.getElementById("loginForm");
  const signupForm = document.getElementById("signupForm");

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

  // Allow forms to submit normally - remove preventDefault to enable actual form submission
  // Forms will now submit to their respective Flask routes

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
