const form = document.getElementById("calculator-form");
const expressionInput = document.getElementById("expression");

const status = document.getElementById("status");
const stepsContainer = document.getElementById("steps-container");
const stepsElement = document.getElementById("steps");

const resultContainer = document.getElementById("result-container");
const answerElement = document.getElementById("answer");
const confidenceElement = document.getElementById("confidence");

// Focus Mode Elements
const appLayout = document.getElementById("app-layout");
const focusToggle = document.getElementById("focus-toggle");
const focusPanel = document.getElementById("focus-panel");
const focusClose = document.getElementById("focus-close");
const focusVideo = document.getElementById("focus-video");
const soundToggle = document.getElementById("sound-toggle");
const videoFallback = document.getElementById("video-fallback");


function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}


function showError(message) {
    status.textContent = message;
    stepsContainer.classList.add("hidden");
    resultContainer.classList.add("hidden");
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
    status.textContent = "Thinking like a human...";
    stepsContainer.classList.add("hidden");
    resultContainer.classList.add("hidden");
    stepsElement.innerHTML = "";

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
        focusToggle.innerHTML = '<span class="focus-btn-icon"></span> Exit Focus';
    }

    if (focusVideo) {
        focusVideo.currentTime = 0;
        const playPromise = focusVideo.play();
        if (playPromise !== undefined) {
            playPromise.catch(() => {
                // If browser blocks unmuted play, ensure muted and retry
                focusVideo.muted = true;
                if (soundToggle) soundToggle.textContent = "";
                focusVideo.play().catch(() => {});
            });
        }
    }
}

function closeFocusMode() {
    if (!focusPanel) return;

    appLayout.classList.remove("focus-active");
    focusPanel.classList.remove("active");
    focusPanel.setAttribute("aria-hidden", "true");

    if (focusToggle) {
        focusToggle.classList.remove("active");
        focusToggle.innerHTML = '<span class="focus-btn-icon"></span> Focus Mode';
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

if (focusClose) {
    focusClose.addEventListener("click", closeFocusMode);
}

if (soundToggle && focusVideo) {
    soundToggle.addEventListener("click", () => {
        focusVideo.muted = !focusVideo.muted;
        soundToggle.textContent = focusVideo.muted ? "" : "";
        soundToggle.title = focusVideo.muted ? "Unmute" : "Mute";
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
