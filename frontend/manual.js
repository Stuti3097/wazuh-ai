let manualState = {
    step: "idle",
    issues: [],
    selectedService: null
};

const manualOutput = document.getElementById("manualOutput");
const manualInput = document.getElementById("manualInput");

function mPrint(text) {
    manualOutput.innerText += text + "\n";
}

function startManualFlow(issueList) {

    manualOutput.innerText = "";

    manualState.issues = issueList;

    if (!issueList.length) {
        mPrint("No issues.");
        return;
    }

    mPrint("Select issue number:");

    issueList.forEach((i, idx) => {
        mPrint(`${idx + 1}. ${i}`);
    });

    manualState.step = "choose";
}

async function handleManual() {

    let value = manualInput.value.trim();
    manualInput.value = "";

    if (!value) return;

    mPrint("You: " + value);

    if (manualState.step === "choose") {

        let i = parseInt(value) - 1;

        if (isNaN(i) || i < 0 || i >= manualState.issues.length) {
            mPrint("Invalid.");
            return;
        }

        manualState.selectedService = manualState.issues[i];

        mPrint("Restart it? (yes/no)");
        manualState.step = "confirm";
        return;
    }

    if (manualState.step === "confirm") {

        if (value.toLowerCase() !== "yes") {
            mPrint("Cancelled.");
            manualState.step = "idle";
            return;
        }

        mPrint("Restarting...");

        let res = await fetch(BASE_URL + "/fix?service=" + manualState.selectedService);
        let data = await res.json();

        mPrint(data.message);

        manualState.step = "idle";
    }
}
