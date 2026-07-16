(function () {
  function setFeedback(card, isCorrect) {
    const feedback = card.querySelector(".quiz-feedback");
    if (!feedback) return;
    const prefix = isCorrect ? "Correct. " : "Not quite. ";
    feedback.textContent = prefix + feedback.dataset.feedback;
    feedback.classList.add("visible");
  }

  document.addEventListener("click", async function (event) {
    const copyButton = event.target.closest(".copy-button");
    if (copyButton) {
      const card = copyButton.closest(".code-card");
      const source = card && card.querySelector(".copy-source");
      if (!source) return;
      try {
        await navigator.clipboard.writeText(source.textContent);
        copyButton.textContent = "Copied";
        setTimeout(function () {
          copyButton.textContent = "Copy";
        }, 1200);
      } catch (_) {
        copyButton.textContent = "Copy failed";
        setTimeout(function () {
          copyButton.textContent = "Copy";
        }, 1200);
      }
      return;
    }

    const option = event.target.closest(".quiz-option");
    if (!option) return;
    const card = option.closest(".quiz-card");
    if (!card) return;
    const options = Array.from(card.querySelectorAll(".quiz-option"));
    options.forEach(function (button) {
      button.disabled = true;
      if (button.dataset.correct === "true") {
        button.classList.add("correct");
      }
    });
    const correct = option.dataset.correct === "true";
    if (!correct) {
      option.classList.add("incorrect");
    }
    setFeedback(card, correct);
  });
})();
