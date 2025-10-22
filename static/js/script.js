

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

  // Simple alert to simulate form submission
  loginForm.addEventListener("submit", (e) => {
    e.preventDefault();
    alert("✅ Login form submitted!");
  });

  signupForm.addEventListener("submit", (e) => {
    e.preventDefault();
    alert("🎉 Sign up form submitted!");
  });
});




















