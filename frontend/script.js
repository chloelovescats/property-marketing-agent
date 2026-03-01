/* ============================================================
   script.js — Real Estate Marketing AI Agent
   Handles form submission, SSE streaming, and rendering results.
   ============================================================ */

var SEARCH_API_URL = "/search-amenities";
var COPY_API_URL = "/generate-copy";

// --- Session-level stats ---
var sessionStats = {
    totalApiCalls: 0,
    geminiCalls: 0,
    mapsCalls: 0,
    searchesDone: 0,
};

// DOM references
var form = document.getElementById("address-form");
var addressInput = document.getElementById("address-input");
var profileInput = document.getElementById("profile-input");
var submitBtn = document.getElementById("submit-btn");
var loadingDiv = document.getElementById("loading");
var loadingText = document.getElementById("loading-text");
var errorDiv = document.getElementById("error-message");
var resultsSection = document.getElementById("results");
var coordContent = document.getElementById("coordinates-content");
var buyerProfileCard = document.getElementById("buyer-profile-card");
var buyerProfileContent = document.getElementById("buyer-profile-content");
var amenContent = document.getElementById("amenities-content");
var copyContent = document.getElementById("copy-content");
var generateCopyWrapper = document.getElementById("generate-copy-wrapper");
var generateCopyBtn = document.getElementById("generate-copy-btn");
var copyCard = document.getElementById("copy-card");
var copyTextBtn = document.getElementById("copy-text-btn");
var generateSpinner = document.getElementById("generate-spinner");

// Agent activity DOM references
var agentActivity = document.getElementById("agent-activity");
var agentSteps = document.getElementById("agent-steps");
var agentToggle = document.getElementById("agent-toggle");
var agentApiCount = document.getElementById("agent-api-count");

// Settings DOM references
var settingsToggle = document.getElementById("settings-toggle");
var settingsPanel = document.getElementById("settings-panel");
var settingsClose = document.getElementById("settings-close");

// How It Works DOM references
var howitworksToggle = document.getElementById("howitworks-toggle");
var howitworksPanel = document.getElementById("howitworks-panel");
var howitworksClose = document.getElementById("howitworks-close");

// Stored amenities globally so we can generate copy later
var lastSearchedAddress = "";
var currentBuyerProfile = null;


// --- Settings panel toggle ---
settingsToggle.addEventListener("click", function () {
    settingsPanel.classList.toggle("hidden");
    howitworksPanel.classList.add("hidden");
    updateSettingsDisplay();
});

settingsClose.addEventListener("click", function () {
    settingsPanel.classList.add("hidden");
});

// --- How It Works panel toggle ---
howitworksToggle.addEventListener("click", function () {
    howitworksPanel.classList.toggle("hidden");
    settingsPanel.classList.add("hidden");
});

howitworksClose.addEventListener("click", function () {
    howitworksPanel.classList.add("hidden");
});


// --- Agent activity toggle ---
agentToggle.addEventListener("click", function () {
    agentSteps.classList.toggle("collapsed");
    agentToggle.classList.toggle("rotated");
});


// --- Node display config ---
var NODE_CONFIG = {
    planner: { label: "Planner", icon: "🧠" },
    search: { label: "Search", icon: "🔍" },
    critic: { label: "Critic", icon: "✅" },
    done: { label: "Done", icon: "🎯" },
};


// --- Form submit handler ---
form.addEventListener("submit", function (event) {
    event.preventDefault();
    var address = addressInput.value.trim();
    var profileText = profileInput.value.trim();

    if (!address) {
        showError("Please enter a property address.");
        return;
    }
    lastSearchedAddress = address;
    sessionStats.searchesDone++;

    hideError();
    hideResults();
    copyCard.classList.add("hidden");
    generateCopyWrapper.classList.add("hidden");
    buyerProfileCard.classList.add("hidden");

    // Show agent activity panel and clear old steps
    agentSteps.innerHTML = "";
    agentSteps.classList.remove("collapsed");
    agentToggle.classList.remove("rotated");
    agentActivity.classList.remove("hidden");
    agentApiCount.textContent = "0 API calls";
    showLoading();
    updateLoadingText("Starting AI agent...");

    // Use fetch with streaming reader for SSE
    fetch(SEARCH_API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ address: address, buyer_profile: profileText }),
    })
        .then(function (response) {
            if (!response.ok) {
                return response.json().then(function (data) {
                    throw new Error(data.error || "Something went wrong.");
                });
            }

            var reader = response.body.getReader();
            var decoder = new TextDecoder();
            var buffer = "";

            function processStream() {
                return reader.read().then(function (result) {
                    if (result.done) return;

                    buffer += decoder.decode(result.value, { stream: true });

                    // Process complete SSE messages (each ends with \n\n)
                    var parts = buffer.split("\n\n");
                    buffer = parts.pop(); // Keep incomplete part in buffer

                    parts.forEach(function (part) {
                        var line = part.trim();
                        if (line.indexOf("data: ") === 0) {
                            var jsonStr = line.substring(6);
                            try {
                                var event = JSON.parse(jsonStr);
                                handleSSEEvent(event);
                            } catch (e) {
                                console.warn("Failed to parse SSE event:", jsonStr);
                            }
                        }
                    });

                    return processStream();
                });
            }

            return processStream();
        })
        .catch(function (err) {
            hideLoading();
            showError(err.message || "Could not reach the server. Is the backend running?");
            console.error("Fetch error:", err);
        });
});


function handleSSEEvent(event) {
    if (event.type === "error") {
        hideLoading();
        showError(event.error || "An error occurred during search.");
        return;
    }

    if (event.type === "step") {
        // Add step to agent activity
        addAgentStep(event.node, event.message, event.iteration);
        agentApiCount.textContent = event.api_call_count + " API calls";

        // Update loading text based on node
        var config = NODE_CONFIG[event.node];
        if (config) {
            updateLoadingText(config.icon + " " + config.label + ": " + event.message);
        }
        return;
    }

    if (event.type === "done") {
        hideLoading();

        // Add completion step
        addAgentStep("done", "Search complete!", 0);

        // Update session stats
        var apiCalls = event.api_call_count || 0;
        sessionStats.totalApiCalls += apiCalls;

        // Estimate breakdown: planner + critic = Gemini, search = Maps
        var agentLog = event.agent_log || [];
        var geminiSteps = 0;
        var mapsSteps = 0;
        agentLog.forEach(function (entry) {
            if (entry.step === "planner" || entry.step === "critic") geminiSteps++;
            if (entry.step === "search") mapsSteps++;
        });
        sessionStats.geminiCalls += geminiSteps;
        sessionStats.mapsCalls += (apiCalls - geminiSteps);

        agentApiCount.textContent = apiCalls + " API calls this search";
        updateSettingsDisplay();

        // Render results
        if (event.coordinates) {
            renderCoordinates(event.coordinates);
        }

        if (event.buyer_profile) {
            currentBuyerProfile = event.buyer_profile;
            renderBuyerProfile(currentBuyerProfile);
            buyerProfileCard.classList.remove("hidden");
        } else {
            currentBuyerProfile = null;
            buyerProfileCard.classList.add("hidden");
        }

        if (event.amenities) {
            renderAmenities(event.amenities);
            generateCopyWrapper.classList.remove("hidden");
        }

        showResults();
        return;
    }
}


// --- Agent activity rendering ---

function addAgentStep(node, message, iteration) {
    var config = NODE_CONFIG[node];
    var icon = config ? config.icon : "✅";
    var label = config ? config.label : "Done";

    var stepEl = document.createElement("div");
    stepEl.className = "agent-step agent-step-enter";

    var iterBadge = "";
    if (iteration && iteration > 0) {
        iterBadge = '<span class="iter-badge">Loop ' + iteration + '</span>';
    }

    stepEl.innerHTML =
        '<span class="step-icon">' + icon + "</span>" +
        '<div class="step-content">' +
        '<span class="step-label">' + escapeHtml(label) + "</span>" +
        iterBadge +
        '<span class="step-message">' + escapeHtml(message) + "</span>" +
        "</div>";

    agentSteps.appendChild(stepEl);

    // Trigger animation
    requestAnimationFrame(function () {
        stepEl.classList.add("agent-step-visible");
    });

    // Auto-scroll to latest step
    agentSteps.scrollTop = agentSteps.scrollHeight;
}


// --- Settings display ---

function updateSettingsDisplay() {
    document.getElementById("stat-total-api").textContent = sessionStats.totalApiCalls;
    document.getElementById("stat-gemini").textContent = sessionStats.geminiCalls;
    document.getElementById("stat-maps").textContent = sessionStats.mapsCalls;
    document.getElementById("stat-searches").textContent = sessionStats.searchesDone;
}


// --- Render functions ---

function renderCoordinates(coords) {
    coordContent.innerHTML =
        '<div class="coord-grid">' +
        '<div class="coord-item full">' +
        '<div class="label">Address</div>' +
        '<div class="value">' + escapeHtml(coords.formatted_address) + '</div>' +
        '</div>' +
        '<div class="coord-item">' +
        '<div class="label">Latitude</div>' +
        '<div class="value">' + coords.latitude + '</div>' +
        '</div>' +
        '<div class="coord-item">' +
        '<div class="label">Longitude</div>' +
        '<div class="value">' + coords.longitude + '</div>' +
        '</div>' +
        '</div>';
}

function renderBuyerProfile(profile) {
    if (!profile) return;

    var html = '<div class="profile-grid">';

    html += '<div class="profile-item"><strong>Persona:</strong> ' + escapeHtml(profile.persona_name || "Unknown") + '</div>';
    html += '<div class="profile-item"><strong>Life Stage:</strong> ' + escapeHtml(profile.life_stage || "Unknown") + '</div>';

    if (profile.priorities && profile.priorities.length > 0) {
        html += '<div class="profile-item full"><strong>Priorities:</strong> ' + escapeHtml(profile.priorities.join(", ")) + '</div>';
    }

    if (profile.lifestyle && profile.lifestyle.likes && profile.lifestyle.likes.length > 0) {
        html += '<div class="profile-item full"><strong>Likes:</strong> ' + escapeHtml(profile.lifestyle.likes.join(", ")) + '</div>';
    }

    if (profile.kids && profile.kids.has_kids) {
        var schoolLevel = profile.kids.school_level ? " (" + profile.kids.school_level + ")" : "";
        html += '<div class="profile-item"><strong>Has Kids:</strong> Yes' + escapeHtml(schoolLevel) + '</div>';
    }

    if (profile.commute) {
        var commuteMode = profile.commute.mode || "any";
        var dest = profile.commute.destination_name ? " to " + profile.commute.destination_name : "";
        var maxMins = profile.commute.max_commute_mins ? " (Max " + profile.commute.max_commute_mins + " mins)" : "";
        html += '<div class="profile-item full"><strong>Commute:</strong> ' + escapeHtml(commuteMode) + escapeHtml(dest) + escapeHtml(maxMins) + '</div>';
    }

    html += '</div>';
    buyerProfileContent.innerHTML = html;
}

function renderAmenities(amenities) {
    var html = "";
    var categories = Object.keys(amenities);

    categories.forEach(function (key) {
        var places = amenities[key] || [];
        var label = key.replace(/_/g, ' ');
        // capitalize label
        label = label.charAt(0).toUpperCase() + label.slice(1);

        html += '<div class="amenity-category">';
        html += '<h3>' + label + '</h3>';

        if (places.length === 0) {
            html += '<p class="amenity-empty">No results matching the criteria.</p>';
        } else {
            html += '<ul class="amenity-list">';
            places.forEach(function (place) {
                html += '<li>';
                html += '  <label class="amenity-checkbox-label">';
                html += '    <input type="checkbox" class="amenity-checkbox" data-category="' + key + '" data-name="' + escapeHtml(place.name) + '" data-distance="' + place.distance_meters + '" checked>';
                html += '    <span class="amenity-name">' + escapeHtml(place.name) + '</span>';
                html += '  </label>';
                html += '  <span class="amenity-meta">';
                html += '    <span>' + place.distance_meters + ' m</span>';
                html += '    <a href="' + place.google_maps_link + '" target="_blank" rel="noopener">Map</a>';
                html += '  </span>';
                html += '</li>';
            });
            html += '</ul>';
        }
        html += '</div>';
    });

    amenContent.innerHTML = html;
}

function renderCopy(copyText) {
    copyContent.textContent = copyText || "No marketing copy was generated.";
}

// --- Generate Copy handler ---
generateCopyBtn.addEventListener("click", function () {
    var checkboxes = document.querySelectorAll(".amenity-checkbox:checked");
    var selectedAmenities = {};

    checkboxes.forEach(function (cb) {
        var category = cb.getAttribute("data-category");
        if (!selectedAmenities[category]) {
            selectedAmenities[category] = [];
        }
        selectedAmenities[category].push({
            name: cb.getAttribute("data-name"),
            distance_meters: parseInt(cb.getAttribute("data-distance"), 10)
        });
    });

    hideError();
    generateCopyBtn.disabled = true;
    generateCopyBtn.textContent = "Generating...";
    if (generateSpinner) {
        generateSpinner.classList.remove("hidden");
        generateSpinner.style.display = "block";
    }

    // Count this as a Gemini call
    sessionStats.totalApiCalls++;
    sessionStats.geminiCalls++;
    updateSettingsDisplay();

    fetch(COPY_API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            address: lastSearchedAddress,
            selected_amenities: selectedAmenities,
            buyer_profile: currentBuyerProfile
        })
    })
        .then(function (response) {
            return response.json().then(function (data) {
                return { ok: response.ok, data: data };
            });
        })
        .then(function (result) {
            generateCopyBtn.disabled = false;
            generateCopyBtn.textContent = "Generate Marketing Copy";
            if (generateSpinner) {
                generateSpinner.classList.add("hidden");
                generateSpinner.style.display = "none";
            }
            if (!result.ok) {
                showError(result.data.error || "Failed to generate copy.");
                return;
            }
            renderCopy(result.data.marketing_copy);
            copyCard.classList.remove("hidden");
        })
        .catch(function (err) {
            generateCopyBtn.disabled = false;
            generateCopyBtn.textContent = "Generate Marketing Copy";
            if (generateSpinner) {
                generateSpinner.classList.add("hidden");
                generateSpinner.style.display = "none";
            }
            showError("Could not reach the server to generate copy.");
            console.error("Fetch error:", err);
        });
});


// --- Copy Text handler ---
if (copyTextBtn) {
    copyTextBtn.addEventListener("click", function () {
        var textToCopy = copyContent.textContent;
        if (!textToCopy) return;

        navigator.clipboard.writeText(textToCopy).then(function () {
            var originalTitle = copyTextBtn.title;
            copyTextBtn.title = "Copied!";
            var originalHTML = copyTextBtn.innerHTML;
            copyTextBtn.innerHTML = '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>';
            setTimeout(function () {
                copyTextBtn.title = originalTitle;
                copyTextBtn.innerHTML = originalHTML;
            }, 2000);
        }).catch(function (err) {
            console.error("Could not copy text: ", err);
        });
    });
}

// --- UI helpers ---

function showLoading() { loadingDiv.classList.remove("hidden"); submitBtn.disabled = true; }
function hideLoading() { loadingDiv.classList.add("hidden"); submitBtn.disabled = false; }
function updateLoadingText(text) { loadingText.textContent = text; }
function showError(msg) { errorDiv.textContent = msg; errorDiv.classList.remove("hidden"); }
function hideError() { errorDiv.classList.add("hidden"); }
function showResults() { resultsSection.classList.remove("hidden"); }
function hideResults() { resultsSection.classList.add("hidden"); }


// --- Security helper ---

function escapeHtml(text) {
    var div = document.createElement("div");
    div.appendChild(document.createTextNode(text));
    return div.innerHTML;
}
