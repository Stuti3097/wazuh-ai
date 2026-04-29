const assistantOutput = document.getElementById("assistantOutput");
const assistantInput = document.getElementById("assistantInput");

function aPrint(text) {
    assistantOutput.innerText += text + "\n";
    assistantOutput.scrollTop = assistantOutput.scrollHeight;
}

async function handleAssistant() {

    let value = assistantInput.value.trim();
    assistantInput.value = "";

    if (!value) return;

    aPrint("You: " + value);

    try {

        const res = await fetch(BASE_URL + "/assistant", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ message: value })
        });

        const data = await res.json();

        if (!data || !data.response) {
            aPrint("No response from assistant.");
            return;
        }

        const r = data.response;

        // -----------------------------
        // USE CASE EXECUTION (REAL FIX)
        // -----------------------------
        if (r.type === "use_case") {

            aPrint("\nIssue: " + r.name);
            aPrint("\nStarting troubleshooting...\n");

            for (let i = 0; i < r.steps.length; i++) {

                const step = r.steps[i];

                aPrint("Step " + (i + 1) + ": " + step.title);

                if (step.run) {

                    aPrint("Running: " + step.run);

                    try {
                        const runRes = await fetch(
                            BASE_URL + "/run?cmd=" + encodeURIComponent(step.run)
                        );

                        const runData = await runRes.json();
                        const output = runData.output || "";

                        aPrint("Result:");
                        aPrint(output);

                        // ✅ validation
                        if (step.expected) {
                            if (output.toLowerCase().includes(step.expected.toLowerCase())) {
                                aPrint("✔ OK");
                            } else {
                                aPrint("❌ NOT OK");

                                if (step.fix) {
                                    aPrint("Fix:");
                                    step.fix.forEach(f => aPrint(" - " + f));
                                }
                            }
                        }

                    } catch (err) {
                        aPrint("Execution failed.");
                    }
                }

                if (step.note) {
                    aPrint("Note: " + step.note);
                }

                aPrint("");
            }

            return;
        }

        // fallback
        aPrint(r.message || "No useful response.");

    } catch (err) {
        aPrint("Backend error.");
    }
}
