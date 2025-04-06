function getData(endpoint, callback) {
    const request = new XMLHttpRequest();
    request.onreadystatechange = () => {
        if (request.readyState === 4) {
            callback(request.response);
        }
    };
    request.open("GET", endpoint);
    request.send();
}
class DebugForm {
    constructor() {
        this.debug_card = document.querySelector(".debug-card");
        this.form = this.debug_card.querySelector(".debug-form");

        this.clear_button = this.form.querySelector("button[data-action='clear']");
        this.clear_button.addEventListener("click", this.handleClearClick.bind(this));

        this.read_button = this.form.querySelector("button[data-action='read']");
        this.read_button.addEventListener("click", this.handleReadClick.bind(this));
    }

    handleClearClick(event) {
        event.preventDefault();
        let code = this.debug_card.querySelector("code");
        code.innerText = "";
    }

    handleReadClick(event) {
        event.preventDefault();
        const debugCard = document.querySelector(".debug-card");
        const input = debugCard.querySelector("input")
        const endpoint = input.value;
        getData(endpoint, this.showResponse);
    }

    showResponse(data) {
        const debugCard = document.querySelector(".debug-card");
        let code = debugCard.querySelector("code");
        code.innerText = data;
    }
}

if (document.querySelector(".debug-card")) {
    const debug = new DebugForm();
    debug.showResponse("");
}