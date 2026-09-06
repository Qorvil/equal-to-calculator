const form = document.getElementById("calculator-form");
const expressionInput = document.getElementById("expression");

const status = document.getElementById("status");
const stepsContainer = document.getElementById("steps-container");
const stepsElement = document.getElementById("steps");

const resultContainer = document.getElementById("result-container");
const answerElement = document.getElementById("answer");
const confidenceElement = document.getElementById("confidence");

// Captcha Elements
const captchaContainer = document.getElementById("captcha-container");
const resultContent = document.getElementById("result-content");
const captchaCanvas = document.getElementById("captcha-canvas");
const captchaRefresh = document.getElementById("captcha-refresh");
const captchaInput = document.getElementById("captcha-input");
const captchaVerifyBtn = document.getElementById("captcha-verify-btn");
const captchaError = document.getElementById("captcha-error");

let currentCaptcha = "";

// Focus Mode Elements
const appLayout = document.getElementById("app-layout");
const focusToggle = document.getElementById("focus-toggle");
const focusPanel = document.getElementById("focus-panel");
const focusVideo = document.getElementById("focus-video");
const videoFallback = document.getElementById("video-fallback");

// Donate Modal Elements
const donateModal = document.getElementById("donate-modal");
const donateCloseX = document.getElementById("donate-close-x");
const donateDismissBtn = document.getElementById("donate-dismiss-btn");


function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


function showError(message) {
    status.textContent = message;
    stepsContainer.classList.add("hidden");
    resultContainer.classList.add("hidden");
}


// ============================================================
// CAPTCHA VERIFICATION SYSTEM
// ============================================================

function generateCaptcha() {
    if (!captchaCanvas) return;

    const chars = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ";
    let text = "";
    for (let i = 0; i < 5; i++) {
        text += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    currentCaptcha = text;

    const ctx = captchaCanvas.getContext("2d");
    ctx.clearRect(0, 0, captchaCanvas.width, captchaCanvas.height);

    // Dark canvas background
    ctx.fillStyle = "#0c0823";
    ctx.fillRect(0, 0, captchaCanvas.width, captchaCanvas.height);

    // Interference curves
    for (let i = 0; i < 4; i++) {
        ctx.strokeStyle = `rgba(${Math.floor(Math.random() * 200 + 55)}, ${Math.floor(Math.random() * 200 + 55)}, 255, 0.4)`;
        ctx.lineWidth = Math.random() * 2 + 1;
        ctx.beginPath();
        ctx.moveTo(Math.random() * captchaCanvas.width, Math.random() * captchaCanvas.height);
        ctx.bezierCurveTo(
            Math.random() * captchaCanvas.width, Math.random() * captchaCanvas.height,
            Math.random() * captchaCanvas.width, Math.random() * captchaCanvas.height,
            Math.random() * captchaCanvas.width, Math.random() * captchaCanvas.height
        );
        ctx.stroke();
    }

    // Interference noise dots
    for (let i = 0; i < 35; i++) {
        ctx.fillStyle = `rgba(255, 97, 216, ${Math.random() * 0.5})`;
        ctx.beginPath();
        ctx.arc(
            Math.random() * captchaCanvas.width,
            Math.random() * captchaCanvas.height,
            Math.random() * 2 + 0.5,
            0,
            Math.PI * 2
        );
        ctx.fill();
    }

    // Draw characters with distinct colors & rotation
    const colors = ["#6ee7ff", "#ff61d8", "#ffd166", "#ffffff", "#a64bff"];
    const charSpacing = (captchaCanvas.width - 30) / text.length;

    for (let i = 0; i < text.length; i++) {
        ctx.save();
        const x = 18 + i * charSpacing;
        const y = 33 + (Math.random() * 6 - 3);
        const angle = (Math.random() * 32 - 16) * Math.PI / 180;

        ctx.translate(x, y);
        ctx.rotate(angle);

        ctx.fillStyle = colors[i % colors.length];
        ctx.font = "bold 24px 'Courier New', monospace";
        ctx.fillText(text[i], 0, 0);
        ctx.restore();
    }

    if (captchaInput) {
        captchaInput.value = "";
    }
    if (captchaError) {
        captchaError.classList.add("hidden");
        captchaError.textContent = "";
    }
}

function showCaptchaError(message) {
    if (!captchaError) return;
    captchaError.textContent = message;
    captchaError.classList.remove("hidden");
}

function verifyCaptcha() {
    if (!captchaInput) return;

    const userInput = captchaInput.value.trim().toUpperCase();

    if (!userInput) {
        showCaptchaError("Please enter the code above.");
        return;
    }

    if (userInput === currentCaptcha) {
        // Human verified: reveal the blurred answer & confidence!
        if (resultContent) {
            resultContent.classList.remove("blurred");
            resultContent.classList.add("unblurred");
        }
        if (captchaContainer) {
            captchaContainer.classList.add("hidden");
        }

        // Pop up the "Pls Donate" window shortly after seeing the answer
        setTimeout(() => {
            showDonateModal();
        }, 5000);
    } else {
        showCaptchaError("Incorrect code! Please try again.");
        if (captchaContainer) {
            captchaContainer.classList.add("captcha-shake");
            setTimeout(() => {
                captchaContainer.classList.remove("captcha-shake");
            }, 400);
        }
        generateCaptcha();
    }
}

function showDonateModal() {
    if (!donateModal) return;
    donateModal.classList.remove("hidden");
    donateModal.setAttribute("aria-hidden", "false");
}

function closeDonateModal() {
    if (!donateModal) return;
    donateModal.classList.add("hidden");
    donateModal.setAttribute("aria-hidden", "true");
}

if (donateCloseX) {
    donateCloseX.addEventListener("click", closeDonateModal);
}

if (donateDismissBtn) {
    donateDismissBtn.addEventListener("click", closeDonateModal);
}

if (donateModal) {
    donateModal.addEventListener("click", (event) => {
        if (event.target === donateModal) {
            closeDonateModal();
        }
    });
}

if (captchaRefresh) {
    captchaRefresh.addEventListener("click", generateCaptcha);
}

if (captchaVerifyBtn) {
    captchaVerifyBtn.addEventListener("click", verifyCaptcha);
}

if (captchaInput) {
    captchaInput.addEventListener("keydown", (event) => {
        if (event.key === "Enter") {
            event.preventDefault();
            verifyCaptcha();
        }
    });
}


async function showSteps(steps) {
    stepsElement.innerHTML = "";
    stepsContainer.classList.remove("hidden");

    for (const step of steps) {
        const stepElement = document.createElement("div");
        stepElement.className = "step";

        stepElement.innerHTML = `
            <strong>Step ${step.number}</strong>
            <div>${step.description}</div>
            <small>${step.formula}</small>
            <div>→ ${step.result}</div>
        `;

        stepsElement.appendChild(stepElement);

        // Scroll the latest step into view.
        stepElement.scrollIntoView({
            behavior: "smooth",
            block: "nearest"
        });

        // Random delay makes the calculator feel like it's thinking.
        const delay = Math.floor(Math.random() * 600) + 300;

        await sleep(delay);
    }
}


form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const expression = expressionInput.value.trim();

    if (!expression) {
        showError("You forgot to give me something to calculate.");
        return;
    }

    // Reset previous calculation.
    closeDonateModal();
    status.textContent = "Thinking like a human...";
    stepsContainer.classList.add("hidden");
    resultContainer.classList.add("hidden");
    stepsElement.innerHTML = "";

    // Reset blur state & show captcha container for the next answer
    if (resultContent) {
        resultContent.classList.remove("unblurred");
        resultContent.classList.add("blurred");
    }
    if (captchaContainer) {
        captchaContainer.classList.remove("hidden");
    }

    try {
        const response = await fetch("/calculate", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                expression: expression
            })
        });

        const data = await response.json();

        // --------------------------------------------------
        // Error
        // --------------------------------------------------

        if (data.type === "error") {
            showError(data.message);
            return;
        }

        // --------------------------------------------------
        // YouTube redirect
        // --------------------------------------------------

        if (data.type === "redirect") {
            status.textContent = data.message;

            await sleep(1500);

            window.location.href = data.url;

            return;
        }

        // --------------------------------------------------
        // Normal calculation
        // --------------------------------------------------

        if (data.type === "calculation") {
            status.textContent = "Calculation in progress...";

            await showSteps(data.steps);

            status.textContent = "Calculation complete.";

            answerElement.textContent = data.answer;

            confidenceElement.textContent =
                `Probability of correctness: ${data.confidence}%`;

            // Ensure result is blurred and generate fresh captcha challenge
            if (resultContent) {
                resultContent.classList.remove("unblurred");
                resultContent.classList.add("blurred");
            }
            if (captchaContainer) {
                captchaContainer.classList.remove("hidden");
            }
            generateCaptcha();

            resultContainer.classList.remove("hidden");
        }

    } catch (error) {
        console.error(error);

        showError(
            "The calculator has stopped functioning due to an unexpected encounter with mathematics."
        );
    }
});


// ============================================================
// FOCUS MODE (SUBWAY SURFERS)
// ============================================================

function openFocusMode() {
    if (!focusPanel) return;

    appLayout.classList.add("focus-active");
    focusPanel.classList.add("active");
    focusPanel.setAttribute("aria-hidden", "false");

    if (focusToggle) {
        focusToggle.classList.add("active");
        focusToggle.textContent = "Exit Focus";
    }

    if (focusVideo) {
        focusVideo.currentTime = 0;
        focusVideo.play().catch(() => {});
    }
}

function closeFocusMode() {
    if (!focusPanel) return;

    appLayout.classList.remove("focus-active");
    focusPanel.classList.remove("active");
    focusPanel.setAttribute("aria-hidden", "true");

    if (focusToggle) {
        focusToggle.classList.remove("active");
        focusToggle.textContent = "Focus Mode";
    }

    if (focusVideo) {
        focusVideo.pause();
    }
}

if (focusToggle) {
    focusToggle.addEventListener("click", () => {
        if (focusPanel.classList.contains("active")) {
            closeFocusMode();
        } else {
            openFocusMode();
        }
    });
}

// Fallback handling if ss.mp4 is missing
if (focusVideo && videoFallback) {
    focusVideo.addEventListener("error", () => {
        videoFallback.classList.remove("hidden");
    });

    const source = focusVideo.querySelector("source");
    if (source) {
        source.addEventListener("error", () => {
            videoFallback.classList.remove("hidden");
        });
    }
}
