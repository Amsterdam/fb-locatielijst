const propertyList = JSON.parse(document.getElementById('property-list').textContent);

function setSearchField(){
    var searchField = document.getElementById("id_search");
    var activeProperty = document.getElementById("id_property");
    var activePropertyId = 'id_' + activeProperty.value

    for (property of propertyList) {
        var element = document.getElementById(property);
        if(element) {
            console.log(property);
            element.style.visibility = "hidden";
            element.disabled = true;
            element.style.display = "none";
        }
    }

    if(propertyList.includes(activePropertyId)) {
        var selectField = document.getElementById(activePropertyId);
        selectField.style.visibility = "visible";
        selectField.style.display = "inline";
        selectField.disabled = false;
    } else {
        searchField.style.visibility = "visible";       
        searchField.style.display = "inline";
        searchField.disabled = false;
    }
}

window.onload = function () {
    setSearchField()
};

