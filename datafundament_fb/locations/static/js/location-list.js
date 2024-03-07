const propertyList = JSON.parse(document.getElementById('property-list').textContent);

function setSearchField(){
    var propertyField = document.getElementById("id_property");
    var activePropertyId = 'id_' + propertyField.value

    propertyField.parentElement.classList.remove("filter-hide");
    for (property of propertyList) {
        var element = document.getElementById(property);
        if(element) {
            element.parentElement.classList.add("filter-hide");
            element.disabled = true;
        }
    }

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

