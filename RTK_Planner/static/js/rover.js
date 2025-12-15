document.addEventListener('DOMContentLoaded', function () {
    // Load rovers on page load
    loadRovers();

    // Add event listener for create rover button
    document.getElementById('createRoverBtn').addEventListener('click', createRover);
});

// Load all rovers from the database
function loadRovers() {
    fetch('/api/rovers')
        .then(response => response.json())
        .then(data => {
            const roversContainer = document.getElementById('roversListContainer');
            roversContainer.innerHTML = '';

            if (data.length === 0) {
                roversContainer.innerHTML = '<p>No rovers found. Add a rover to get started.</p>';
                return;
            }

            data.forEach(rover => {
                renderRoverCard(rover, roversContainer);
            });
        })
        .catch(error => {
            console.error('Error loading rovers:', error);
            alert('Failed to load rovers. Please try again later.');
        });
}

// Create a new rover
function createRover() {
    const name = document.getElementById('roverName').value.trim();
    const mac = document.getElementById('roverMac').value.trim();

    if (!name || !mac) {
        alert('Please enter both name and MAC address');
        return;
    }

    const roverData = {
        name: name,
        mac: mac,
        status: 'inactive'
    };

    fetch('/api/rovers', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(roverData)
    })
        .then(response => response.json())
        .then(data => {
            // Clear form
            document.getElementById('roverName').value = '';
            document.getElementById('roverMac').value = '';

            // Add the new rover to the list
            const roversContainer = document.getElementById('roversListContainer');
            renderRoverCard(data, roversContainer, true);
        })
        .catch(error => {
            console.error('Error creating rover:', error);
            alert('Failed to create rover. Please try again.');
        });
}

// Render a single rover card
function renderRoverCard(rover, container, prepend = false) {
    const roverCard = document.createElement('div');
    roverCard.className = 'rover-card';
    roverCard.id = `rover-${rover.id}`;

    const cardContent = `
                                    <div class="rover-header">
                                        <h3 class="rover-title">${rover.name}</h3>
                                        <button class="edit-rover-btn" onclick="toggleEditMode(${rover.id})">Edit</button>
                                    </div>
                                    <div class="rover-info">

                                        <table style="width:100%">
                                            <tr>
                                                <td><strong>MAC Address:</strong> <span class="rover-mac">${rover.mac}</span></td>
                                                <td><strong>Fix Status:</strong> <span id="${rover.mac}-fix-status" class="status-invalid">Unknown</span></td>
                                                <td><strong>Decimal Coordinates:</strong> <span id="${rover.mac}-dec-coords">-</span></td>
                                                <td><strong>Raw Coordinates:</strong> <span id="${rover.mac}-raw-coords">-</span></td>
                                            </tr>
                                            <tr>
                                                <td><strong>Speed:</strong> <span id="${rover.mac}-speed">-</span></td>
                                                <td><strong>Course:</strong> <span id="${rover.mac}-course">-</span></td>
                                                <td><strong>GPS Time:</strong> <span id="${rover.mac}-gps-time">-</span></td>
                                                <td><strong>Last Update:</strong> <span id="${rover.mac}-last-update">-</span></td>
                                            </tr>
                                        </table>
                                        <strong>Satellites in Use:</strong> <span id="${rover.mac}-su">-</span>

                                        <div class="trail-selector">
                                            <label><strong>Associated Trails:</strong></label>
                                            <select id="trail-dropdown-${rover.id}" onchange="displaySelectedTrail(${rover.id})">
                                                <option value="">Select a trail</option>
                                            </select>
                                            
                                            <button class="button-secondary" onclick="sendTrailToRover(${rover.id})">Send Trail</button>
                                            <button class="button-secondary" onclick="stopRover(${rover.id})">Stop</button>

                                            <p id="selected-trail-${rover.id}"></p>
                                        </div>

                                        <div class="associated-trails">
                                            <strong>Trails:</strong>
                                            <div class="trail-list" id="trail-list-${rover.id}">
                                                <span class="loading">Loading trails...</span>
                                            </div>
                                        </div>
                                    </div>

                                    <div class="edit-form" id="edit-form-${rover.id}">
                                        <h4>Edit Rover</h4>
                                        <div class="form-group">
                                            <label for="edit-name-${rover.id}">Name:</label>
                                            <input type="text" id="edit-name-${rover.id}" value="${rover.name}">
                                        </div>
                                        <div class="form-group">
                                            <label for="edit-mac-${rover.id}">MAC Address:</label>
                                            <input type="text" id="edit-mac-${rover.id}" value="${rover.mac}">
                                        </div>

                                        <div class="form-group">
                                            <label>Manage Trails:</label>
                                            <div id="edit-trails-${rover.id}">
                                                <select id="available-trails-${rover.id}">
                                                    <option value="">Loading available trails...</option>
                                                </select>
                                                <button class="button-secondary" onclick="addTrailToRover(${rover.id})">Add Trail</button>
                                            </div>
                                            <div id="rover-trails-${rover.id}" class="trail-list">
                                                Loading associated trails...
                                            </div>
                                        </div>

                                        <div class="edit-actions">
                                            <button onclick="saveRoverChanges(${rover.id})">OK</button>
                                            <button class="button-cancel" onclick="toggleEditMode(${rover.id})">Cancel</button>
                                            <button class="button-danger" onclick="deleteRover(${rover.id})">Delete</button>
                                        </div>
                                    </div>
                                `;

    roverCard.innerHTML = cardContent;

    if (prepend && container.firstChild) {
        container.insertBefore(roverCard, container.firstChild);
    } else {
        container.appendChild(roverCard);
    }

    // Load associated trails for this rover
    loadAssociatedTrailsForDropdown(rover.id);
    loadTrailsForRover(rover.id);
}

// Toggle edit mode for a rover
function toggleEditMode(roverId) {
    const editForm = document.getElementById(`edit-form-${roverId}`);
    if (editForm.style.display === 'block') {
        editForm.style.display = 'none';
    } else {
        editForm.style.display = 'block';
        loadAvailableTrails(roverId);
        loadAssociatedTrails(roverId);
    }
}

// Load available trails for adding to a rover (in edit mode)
function loadAvailableTrails(roverId) {
    fetch('/api/trails')
        .then(response => response.json())
        .then(data => {
            const availableTrailsDropdown = document.getElementById(`available-trails-${roverId}`);
            availableTrailsDropdown.innerHTML = '';

            if (data.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No trails available';
                availableTrailsDropdown.appendChild(option);
                return;
            }

            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'Select a trail to add';
            availableTrailsDropdown.appendChild(defaultOption);

            data.forEach(trail => {
                const option = document.createElement('option');
                option.value = trail.id;
                option.textContent = trail.name;
                availableTrailsDropdown.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading available trails:', error);
            const availableTrailsDropdown = document.getElementById(`available-trails-${roverId}`);
            availableTrailsDropdown.innerHTML = '<option value="">Error loading trails</option>';
        });
}

// Load associated trails for the dropdown selector
function loadAssociatedTrailsForDropdown(roverId) {
    fetch(`/api/rovers/${roverId}/trails`)
        .then(response => response.json())
        .then(data => {
            const trailDropdown = document.getElementById(`trail-dropdown-${roverId}`);

            // Clear existing options except the first one
            while (trailDropdown.options.length > 1) {
                trailDropdown.remove(1);
            }

            if (data.length === 0) {
                const option = document.createElement('option');
                option.value = '';
                option.textContent = 'No trails associated';
                trailDropdown.innerHTML = '';
                trailDropdown.appendChild(option);
                return;
            }

            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'Select a trail';
            trailDropdown.innerHTML = '';
            trailDropdown.appendChild(defaultOption);

            data.forEach(trail => {
                const option = document.createElement('option');
                option.value = trail.id;
                option.textContent = trail.name;
                trailDropdown.appendChild(option);
            });
        })
        .catch(error => {
            console.error('Error loading associated trails for dropdown:', error);
            const trailDropdown = document.getElementById(`trail-dropdown-${roverId}`);
            trailDropdown.innerHTML = '<option value="">Error loading trails</option>';
        });
}

// Load trails associated with a specific rover
function loadTrailsForRover(roverId) {
    fetch(`/api/rovers/${roverId}/trails`)
        .then(response => response.json())
        .then(data => {
            const trailListContainer = document.getElementById(`trail-list-${roverId}`);
            trailListContainer.innerHTML = '';

            if (data.length === 0) {
                trailListContainer.innerHTML = '<span class="empty-message">No trails assigned</span>';
                return;
            }

            data.forEach(trail => {
                const trailTag = document.createElement('span');
                trailTag.className = 'trail-tag';
                trailTag.textContent = trail.name;
                trailListContainer.appendChild(trailTag);
            });
        })
        .catch(error => {
            console.error('Error loading rover trails:', error);
            const trailListContainer = document.getElementById(`trail-list-${roverId}`);
            trailListContainer.innerHTML = '<span>Error loading trails</span>';
        });
}

// Load associated trails for editing
function loadAssociatedTrails(roverId) {
    fetch(`/api/rovers/${roverId}/trails`)
        .then(response => response.json())
        .then(data => {
            const trailsContainer = document.getElementById(`rover-trails-${roverId}`);
            trailsContainer.innerHTML = '';

            if (data.length === 0) {
                trailsContainer.innerHTML = '<span class="empty-message">No trails assigned</span>';
                return;
            }

            data.forEach(trail => {
                const trailDiv = document.createElement('div');
                trailDiv.className = 'trail-tag';
                trailDiv.innerHTML = `
                                                ${trail.name}
                                                <button class="button-danger" style="padding: 2px 5px; font-size: 12px;"
                                                      onclick="removeTrailFromRover(${roverId}, ${trail.id})">�</button>
                                            `;
                trailsContainer.appendChild(trailDiv);
            });
        })
        .catch(error => {
            console.error('Error loading associated trails:', error);
            const trailsContainer = document.getElementById(`rover-trails-${roverId}`);
            trailsContainer.innerHTML = '<span>Error loading trails</span>';
        });
}

// Display the selected trail from dropdown
function displaySelectedTrail(roverId) {
    const dropdown = document.getElementById(`trail-dropdown-${roverId}`);
    const selectedTrailDisplay = document.getElementById(`selected-trail-${roverId}`);

    if (dropdown.value) {
        const selectedText = dropdown.options[dropdown.selectedIndex].text;
        selectedTrailDisplay.textContent = `Selected trail: ${selectedText}`;
    } else {
        selectedTrailDisplay.textContent = '';
    }
}

// Add a trail to a rover
function addTrailToRover(roverId) {
    const trailDropdown = document.getElementById(`available-trails-${roverId}`);
    const trailId = trailDropdown.value;

    if (!trailId) {
        alert('Please select a trail to add');
        return;
    }

    fetch(`/api/rovers/${roverId}/trails`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ trail_id: trailId })
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to add trail');
            }
            return response.json();
        })
        .then(() => {
            // Refresh the associated trails
            loadAssociatedTrails(roverId);
            loadTrailsForRover(roverId);
            loadAssociatedTrailsForDropdown(roverId);
        })
        .catch(error => {
            console.error('Error adding trail:', error);
            alert('Failed to add trail. It might already be associated with this rover.');
        });
}

// Remove a trail from a rover
function removeTrailFromRover(roverId, trailId) {
    fetch(`/api/rovers/${roverId}/trails/${trailId}`, {
        method: 'DELETE'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to remove trail');
            }
            return response.json();
        })
        .then(() => {
            // Refresh the associated trails
            loadAssociatedTrails(roverId);
            loadTrailsForRover(roverId);
            loadAssociatedTrailsForDropdown(roverId);
        })
        .catch(error => {
            console.error('Error removing trail:', error);
            alert('Failed to remove trail.');
        });
}

// Save changes to a rover
function saveRoverChanges(roverId) {
    const name = document.getElementById(`edit-name-${roverId}`).value.trim();
    const mac = document.getElementById(`edit-mac-${roverId}`).value.trim();

    if (!name || !mac) {
        alert('Name and MAC address cannot be empty');
        return;
    }

    const roverData = {
        name: name,
        mac: mac
    };

    fetch(`/api/rovers/${roverId}`, {
        method: 'PUT',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(roverData)
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to update rover');
            }
            return response.json();
        })
        .then(data => {
            // Update the rover card
            const roverTitle = document.querySelector(`#rover-${roverId} .rover-title`);
            const roverMac = document.querySelector(`#rover-${roverId} .rover-mac`);

            roverTitle.textContent = data.name;
            roverMac.textContent = data.mac;

            // Close edit form
            toggleEditMode(roverId);
        })
        .catch(error => {
            console.error('Error updating rover:', error);
            alert('Failed to update rover. Please try again.');
        });
}

// Delete a rover
function deleteRover(roverId) {
    if (!confirm('Are you sure you want to delete this rover?')) {
        return;
    }

    fetch(`/api/rovers/${roverId}`, {
        method: 'DELETE'
    })
        .then(response => {
            if (!response.ok) {
                throw new Error('Failed to delete rover');
            }
            return response.json();
        })
        .then(() => {
            // Remove the rover card from the DOM
            const roverCard = document.getElementById(`rover-${roverId}`);
            roverCard.remove();

            // Show message if no rovers left
            const roversContainer = document.getElementById('roversListContainer');
            if (roversContainer.children.length === 0) {
                roversContainer.innerHTML = '<p>No rovers found. Add a rover to get started.</p>';
            }
        })
        .catch(error => {
            console.error('Error deleting rover:', error);
            alert('Failed to delete rover. Please try again.');
        });
}

// Send trail to rover
function sendTrailToRover(roverId) {
    const trailListContainer = document.getElementById(`trail-dropdown-${roverId}`);
    const trailId = trailListContainer.value;

    if (!trailId) {
        alert('Please select a trail to send');
        return;
    }

    fetch(`/trail/upload/${roverId}/${trailId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ trail_id: trailId })
    })
        .then(() => {
            console.log(roverId, trailId);
        });
}

// Send empty trail list, stop the Rover.
function stopRover(roverId) {
    fetch(`/trail/stop/${roverId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ rover_id: roverId })
    })
        .then(() => {
            console.log(roverId, trailId);
        });
}
