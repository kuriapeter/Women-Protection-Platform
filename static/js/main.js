let currentStep = 0;
const steps = document.querySelectorAll(".step");

function showStep(index) {
    steps.forEach((step, i) => {
        step.classList.toggle("active", i === index);
    });
}

function nextStep() {
    if (currentStep < steps.length - 1) {
        currentStep++;
        showStep(currentStep);
    }
}

function prevStep() {
    if (currentStep > 0) {
        currentStep--;
        showStep(currentStep);
    }
}

showStep(currentStep);


const panicBtn = document.getElementById("panicBtn");
const panicModal = document.getElementById("panicModal");

panicBtn.onclick = () => {
    panicModal.style.display = "block";
};

function closePanic() {
    panicModal.style.display = "none";
}

function quickExit() {
    window.location.href = "https://www.google.com";
}
