// Get json data from the webpage
const propertyList = JSON.parse(document.getElementById('property-list').textContent);

// Function to hide/unhide and disable/enable select/text input fields depending on a chosen location property
function setSearchField(){
    // Get the chosen location property
    var propertyField = document.getElementById("id_property");
    // Get the current active form element for the location property
    var activePropertyId = 'id_' + propertyField.value

    // Hide and disable all the elements
    propertyField.parentElement.classList.remove("filter-hide");
    for (property of propertyList) {
        var element = document.getElementById(property);
        if(element) {
            element.parentElement.classList.add("filter-hide");
            element.disabled = true;
        }
    }

    // Unhide and enable a select element, when location property has list values, otherwise a text input field
    if (propertyList.includes(activePropertyId)) {
        var activeField = document.getElementById(activePropertyId);
    } else {
        var activeField = document.getElementById("id_search");
    }
    activeField.parentElement.classList.remove("filter-hide");
    activeField.disabled = false;
}

window.onload = function () {
    setSearchField()
};

