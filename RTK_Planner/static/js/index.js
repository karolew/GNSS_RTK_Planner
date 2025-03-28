import { DebugForm } from "./debug.js";
import { updateElements } from "./select_rover.js";
import { activateCreateForm } from "./rover.js"
import { addInteraction } from "./map.js"

function main() {
    if (document.querySelector(".debug-card")) {
        const debug = new DebugForm();
        debug.showResponse("");
    }

    updateElements();
    activateCreateForm();
    addInteraction();
}

main();