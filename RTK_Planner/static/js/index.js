import { DebugForm } from "./debug.js";
import { updateElements } from "./select_rover.js";
import { activateCreateForm } from "./rover.js"

function main() {
    if (document.querySelector(".debug-card")) {
        const debug = new DebugForm();
        debug.showResponse("");
    }

    $(document).ready(function () {
        updateElements();
    });

    activateCreateForm();
}

main();