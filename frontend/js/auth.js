// Scam Shield - Auth Page Controller (Log In & Sign Up)
import { authApi, isAuthenticated } from "./api.js";

document.addEventListener("DOMContentLoaded", () => {
  // If already authenticated, redirect to main check dashboard
  if (isAuthenticated()) {
    window.location.href = "check.html";
    return;
  }

  // Detect initial mode based on filename or URL parameter
  const isSignupPage = window.location.pathname.endsWith("signup.html") || 
                       new URLSearchParams(window.location.search).get("mode") === "signup";
  let currentMode = isSignupPage ? "signup" : "login";

  // Elements
  const tabLogin = document.getElementById("tab-login");
  const tabSignup = document.getElementById("tab-signup");
  const confirmContainer = document.getElementById("confirm-password-container");
  const confirmInput = document.getElementById("confirm-password-input");
  const submitBtn = document.getElementById("submit-cta");
  const submitBtnText = document.getElementById("submit-cta-text");
  const submitIcon = document.getElementById("submit-icon");
  const submitSpinner = document.getElementById("submit-spinner");
  const bottomToggleBtn = document.getElementById("bottom-toggle-btn");
  const passwordLabelText = document.getElementById("password-label-text");
  const authForm = document.getElementById("auth-form");
  const emailInput = document.getElementById("email-input");
  const passwordInput = document.getElementById("password-input");
  const alertBox = document.getElementById("alertBox");
  const alertTitle = document.getElementById("alertTitle");
  const alertMessage = document.getElementById("alertMessage");

  // Mode Switcher
  function setMode(mode) {
    currentMode = mode;
    clearAlert();

    const activeTabClass = "flex-1 py-3 px-3 rounded-xl font-bold text-sm transition-all duration-200 text-center flex items-center justify-center gap-2 bg-surface-container-lowest text-primary shadow-sm";
    const inactiveTabClass = "flex-1 py-3 px-3 rounded-xl font-bold text-sm transition-all duration-200 text-center flex items-center justify-center gap-2 bg-transparent text-secondary hover:text-on-surface";

    if (mode === "signup") {
      tabSignup.setAttribute("aria-selected", "true");
      tabSignup.className = activeTabClass;
      tabSignup.querySelector(".material-symbols-outlined").style.fontVariationSettings = "'FILL' 1";

      tabLogin.setAttribute("aria-selected", "false");
      tabLogin.className = inactiveTabClass;
      tabLogin.querySelector(".material-symbols-outlined").style.fontVariationSettings = "";

      if (confirmContainer) {
        confirmContainer.classList.remove("hidden");
        confirmContainer.classList.add("flex");
        confirmInput.setAttribute("required", "required");
      }

      submitBtnText.textContent = "Create Free Account";
      submitIcon.textContent = "person_add";
      passwordLabelText.textContent = "Create Password";
      bottomToggleBtn.textContent = "Already have an account? Log in here";
    } else {
      tabLogin.setAttribute("aria-selected", "true");
      tabLogin.className = activeTabClass;
      tabLogin.querySelector(".material-symbols-outlined").style.fontVariationSettings = "'FILL' 1";

      tabSignup.setAttribute("aria-selected", "false");
      tabSignup.className = inactiveTabClass;
      tabSignup.querySelector(".material-symbols-outlined").style.fontVariationSettings = "";

      if (confirmContainer) {
        confirmContainer.classList.add("hidden");
        confirmContainer.classList.remove("flex");
        confirmInput.removeAttribute("required");
      }

      submitBtnText.textContent = "Log In to Scam Shield";
      submitIcon.textContent = "shield";
      passwordLabelText.textContent = "Password";
      bottomToggleBtn.textContent = "Don't have an account yet? Sign up here";
    }
  }

  // Initialize mode
  setMode(currentMode);

  // Event Listeners for Tabs & Toggle Link
  tabLogin?.addEventListener("click", () => setMode("login"));
  tabSignup?.addEventListener("click", () => setMode("signup"));
  bottomToggleBtn?.addEventListener("click", () => {
    setMode(currentMode === "login" ? "signup" : "login");
  });

  // Password Visibility Toggles
  function setupPasswordToggle(toggleBtnId, inputId, iconId) {
    const btn = document.getElementById(toggleBtnId);
    const input = document.getElementById(inputId);
    const icon = document.getElementById(iconId);

    if (btn && input && icon) {
      btn.addEventListener("click", () => {
        if (input.type === "password") {
          input.type = "text";
          icon.textContent = "visibility_off";
          btn.setAttribute("aria-label", "Hide password");
        } else {
          input.type = "password";
          icon.textContent = "visibility";
          btn.setAttribute("aria-label", "Show password");
        }
      });
    }
  }

  setupPasswordToggle("toggle-password-btn", "password-input", "password-eye-icon");
  setupPasswordToggle("toggle-confirm-password-btn", "confirm-password-input", "confirm-eye-icon");

  // Alert Helpers
  function showAlert(title, message, isSuccess = false) {
    if (!alertBox) return;
    alertBox.classList.remove("hidden");
    alertBox.classList.add("flex");

    if (isSuccess) {
      alertBox.className = "bg-tertiary-container text-on-tertiary-container p-4 rounded-2xl mb-5 flex items-start gap-3 shadow-sm";
      alertBox.querySelector(".w-7").className = "w-7 h-7 rounded-full bg-tertiary text-on-tertiary flex items-center justify-center shrink-0 mt-0.5";
      alertBox.querySelector(".material-symbols-outlined").textContent = "check_circle";
    } else {
      alertBox.className = "bg-error-container text-on-error-container p-4 rounded-2xl mb-5 flex items-start gap-3 shadow-sm";
      alertBox.querySelector(".w-7").className = "w-7 h-7 rounded-full bg-error text-on-error flex items-center justify-center shrink-0 mt-0.5";
      alertBox.querySelector(".material-symbols-outlined").textContent = "priority_high";
    }

    if (alertTitle) alertTitle.textContent = title;
    if (alertMessage) alertMessage.textContent = message;
    alertBox.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }

  function clearAlert() {
    if (!alertBox) return;
    alertBox.classList.add("hidden");
    alertBox.classList.remove("flex");
  }

  // Form Submission
  authForm?.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearAlert();

    const email = emailInput.value.trim();
    const password = passwordInput.value;
    const confirmPassword = confirmInput?.value;

    if (!email || !password) {
      showAlert("Missing information", "Please fill in all required fields.");
      return;
    }

    if (password.length < 8) {
      showAlert("Password too short", "Password must be at least 8 characters long.");
      return;
    }

    if (currentMode === "signup" && password !== confirmPassword) {
      showAlert("Passwords do not match", "Please make sure both passwords match.");
      return;
    }

    try {
      submitBtn.disabled = true;
      submitIcon.style.display = "none";
      submitSpinner.style.display = "inline-block";

      if (currentMode === "signup") {
        submitBtnText.textContent = "Creating Account...";
        await authApi.signup(email, password);
        showAlert("Success!", "Account created safely. Logging you in...", true);

        // Auto login
        await authApi.login(email, password);
        setTimeout(() => {
          window.location.href = "check.html";
        }, 500);
      } else {
        submitBtnText.textContent = "Verifying...";
        await authApi.login(email, password);
        window.location.href = "check.html";
      }
    } catch (err) {
      showAlert("Authentication Failed", err.message || "An error occurred. Please try again.");
    } finally {
      submitBtn.disabled = false;
      submitIcon.style.display = "inline-block";
      submitSpinner.style.display = "none";
      submitBtnText.textContent = currentMode === "signup" ? "Create Free Account" : "Log In to Scam Shield";
    }
  });
});
