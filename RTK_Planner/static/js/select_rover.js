// Function to update the dropdown elements
export function updateElements() {
    // Load all rovers into the first dropdown
    $.getJSON('/rover', function (data) {
        const roverSelect = $('#roverSelect');

        $.each(data, function (index, rover) {
            roverSelect.append($('<option>', {
                value: rover.id,
                text: rover.name
            }));
        });
    });

    // Set up the event handler for rover selection
    $('#roverSelect').change(function () {
        const roverId = $(this).val();
        const trailSelect = $('#trailSelect');

        // Clear previous options
        trailSelect.find('option').not(':first').remove();

        if (roverId) {
            // Enable the trail dropdown
            trailSelect.prop('disabled', false);

            // Load trails for the selected rover
            $.getJSON(`/trail/${roverId}`, function (data) {
                $.each(data, function (index, trail) {
                    trailSelect.append($('<option>', {
                        value: trail.id,
                        text: trail.name
                    }));
                });
            });
        } else {
            // Disable the trail dropdown if no rover is selected
            trailSelect.prop('disabled', true);
        }
    });
}


// Call the function when the document is ready
$(document).ready(function () {
    updateElements();
});