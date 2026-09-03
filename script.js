// ================================
// CKD Prediction Script (Final Fixed Version)
// ================================
document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("predictForm");
  const resultBox = document.getElementById("resultArea");
  const resultText = document.getElementById("predictionText");

  if (!form) return; // Prevent running on non-predict pages

  // -------------------------------
  // Handle Form Submission
  // -------------------------------
  form.addEventListener("submit", async function (event) {
    event.preventDefault();

    // ✅ Collect form data safely
    const formData = new FormData(form);
    const data = {};
    formData.forEach((value, key) => {
      value = value.trim();
      if (key === "name") {
        data[key] = value || "Unknown";
      } else if (value === "" || isNaN(value)) {
        data[key] = 0;
      } else {
        data[key] = parseFloat(value);
      }
    });
    console.log("✅ Data sent to backend:", data);

    const submitBtn = form.querySelector(".predict-btn");
    submitBtn.disabled = true;
    submitBtn.textContent = "⏳ Predicting...";

    try {
      const response = await fetch("/predict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data),
      });

      const result = await response.json();

      // ✅ Handle CKD prediction result
      if (result.error) {
        resultText.innerHTML = `❌ Error: ${result.error}`;
        resultText.style.color = "#ff4b4b";
      } else {
        resultText.innerHTML = `✅ Prediction: <b>${result.prediction}</b>`;
        resultText.style.color = result.prediction.includes("No CKD")
          ? "#00ffb7"
          : "#ff4b4b";
      }

      resultBox.style.display = "block";
      resultBox.style.opacity = "0";
      setTimeout(() => {
        resultBox.style.opacity = "1";
        resultBox.style.transition = "opacity 0.5s ease";
      }, 100);
    } catch (error) {
      resultText.innerHTML = `⚠️ Network or Server Error: ${error.message}`;
      resultText.style.color = "#ffcc00";
      resultBox.style.display = "block";
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "🔍 Predict CKD";
      submitBtn.blur();
    }
  });

  // -------------------------------
  // Reset Button Logic
  // -------------------------------
  const resetBtn = document.getElementById("resetBtn");
  if (resetBtn) {
    resetBtn.addEventListener("click", function () {
      form.reset();
      if (resultBox) {
        resultBox.style.opacity = "0";
        setTimeout(() => {
          resultBox.style.display = "none";
          resultBox.style.opacity = "1";
        }, 400);
      }
    });
  }

  // -------------------------------
  // Dropdown info for all CKD parameters
  // -------------------------------
  const fields = [
    "bpInput",
    "sgInput",
    "albInput",
    "sugarInput",
    "glucoseInput",
    "ureaInput",
    "creatinineInput",
    "hbInput",
    "htInput",      // ✅ Hypertension
    "dmInput",      // ✅ Diabetes Mellitus
    "anemiaInput"   // ✅ Anemia
  ];

  fields.forEach((id) => {
    const input = document.getElementById(id);
    const dropdown = document.getElementById(id.replace("Input", "Dropdown"));
    if (input && dropdown) {
      input.addEventListener("focus", () => {
        dropdown.style.display = "block";
      });
      input.addEventListener("blur", () => {
        setTimeout(() => {
          dropdown.style.display = "none";
        }, 150);
      });
    }
  });
});
