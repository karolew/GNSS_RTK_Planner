import { sendForm } from "./request.js";


export function activateCreateForm() {
    const roverForm = document.querySelector(".rover-create-card form");
    new CreateRoverForm(roverForm);
}

class CreateRoverForm {
    constructor(el) {
        this.form = el;
        this.createButton = el.querySelector("button[data-action='create']");
        this.createButton.addEventListener(
            "click",
            this.handleCreateClick.bind(this)
        );
    }

    handleCreateClick(event) {
        event.preventDefault();
        sendForm(this.form, "POST", "/rover", window.location.reload());    /*Ugly reload whole page*/
        this.form.reset();
    }
}
