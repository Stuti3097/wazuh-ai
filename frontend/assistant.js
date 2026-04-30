const assistantOutput = document.getElementById("assistantOutput");
const assistantInput = document.getElementById("assistantInput");

// ✅ ADDED (context storage)
let context = {};

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
            body: JSON.stringify({
                message: value,
                context: context
            })
        });

        console.log("STATUS:", res.status);

        const text = await res.text();
        console.log("RAW RESPONSE:", text);

        let data;

        try {
            data = JSON.parse(text);
        } catch (e) {
            aPrint("Invalid response from backend.");
            console.error("JSON parse error:", e);
            return;
        }

        if (!data || !data.response) {
            aPrint("No response from assistant.");
            console.log("BAD RESPONSE:", data);
            return;
        }

        const r = data.response;

        // USE CASE HANDLING
        if (r.type === "use_case") {

            // update context
            context = r.context || {};

            // show main output
            if (r.display) {
                aPrint(r.display);
            }

            // show next questions
            if (r.ask && r.ask.length > 0) {
                r.ask.forEach(q => aPrint(q));
            }

            return;
        }

        // fallback
        aPrint(r.message || "No useful response.");

    } catch (err) {
        console.error("FULL ERROR:", err);
        aPrint("Backend error.");
    }
}
