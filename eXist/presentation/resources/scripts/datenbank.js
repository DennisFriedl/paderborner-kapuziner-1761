let prefix = "editions-"

// Hover over Icons:
$(function () {
    
    // Bei Hover über Advanced-Search-Icon wechselt er das Icon
    $('#advanced-search-icon').on('mouseover', function () {
        $(this).removeClass('fas');
        $(this).addClass('far');
    }).on('mouseout', function () {
        $(this).removeClass('far');
        $(this).addClass('fas');
    });
    
    // Bei Hover über new-search-row-button wechselt er das Icon
    $('#advanced-search-col').on('mouseover', '.new-search-row-icon', function () {
        $(this).removeClass('fas');
        $(this).addClass('far');
    }).on('mouseout', '.new-search-row-icon', function () {
        $(this).removeClass('far');
        $(this).addClass('fas');
    });
    
    // Bei Hover über switch-between-simple-and-advanced-search-icon wechselt er das Icon
    $('#switch-between-simple-and-advanced-search-icon').on('mouseover', function () {
        $(this).removeClass('fas');
        $(this).addClass('far');
    }).on('mouseout', function () {
        $(this).removeClass('far');
        $(this).addClass('fas');
    });
});

// Event Listener für einfache Suche
$(document).ready(function () {
    let input = document.getElementById('simple-search-bar');
    
    // Enter-Taste bei simpleSearch
    input.addEventListener("keyup", function (event) {
        if (event.keyCode === 13) {
            event.preventDefault();
            simpleSearch();
        };
    });
    
    // Enter-Taste bei advancedSearch
    document.addEventListener("keyup", function (event) {
        if (event.keyCode === 13 && document.getElementById('switch-between-simple-and-advanced-search').classList.contains("status-advanced")) {
            event.preventDefault();
            advancedSearch();
        };
    });
});


function switchBetweenSimpleAndAdvancedSearch() {
    var swapper = document.getElementById('switch-between-simple-and-advanced-search');
    var swapperIcon = document.getElementById('switch-between-simple-and-advanced-search-icon');
    var swapperWord = document.getElementById('switch-between-simple-and-advanced-search-word');
    var simpleSearchCol = document.getElementById('simple-search-col');
    var advancedSearchCol = document.getElementById('advanced-search-col');
    
    if (swapper.classList.contains('status-simple')) {
        // WIRD ZUR ERWEITERTEN SUCHE:
        // Status ändern:
        swapper.classList.remove('status-simple');
        swapper.classList.add('status-advanced');
        // Button wechseln:
        swapperIcon.classList.remove('fa-caret-square-down');
        swapperIcon.classList.add('fa-caret-square-up');
        // Wort wechseln:
        swapperWord.textContent = "Einfache";
        // Verstecken und Zeigen:
        simpleSearchCol.classList.add('hidden');
        advancedSearchCol.classList.remove('hidden');
    } else if (swapper.classList.contains('status-advanced')) {
        // WIRD ZUR EINFACHEN SUCHE:
        // Status ändern:
        swapper.classList.remove('status-advanced');
        swapper.classList.add('status-simple');
        // Button wechseln:
        swapperIcon.classList.remove('fa-caret-square-up');
        swapperIcon.classList.add('fa-caret-square-down');
        // Wort wechseln:
        swapperWord.textContent = "Erweiterte";
        // Verstecken und Zeigen:
        advancedSearchCol.classList.add('hidden');
        simpleSearchCol.classList.remove('hidden');
    }
};

function cleanQuery(query) {
    // Schneide Whitespace am Anfang und Ende ab
    let cleanQuery = query.trim();
    // jeder Whitespace (auch doppelte) wird zu "_"
    cleanQuery = cleanQuery.replace(/\s+/g, "_");
    return cleanQuery;
};

function simpleSearch() {
    var query = document.getElementById('simple-search-bar').value;
    if (query != "") {
        query = cleanQuery(query);
        location.href = "datenbank.html?query=simpleSearch&simpleSearchString=" + encodeURIComponent(query) + "&resetCache=true&page=1";
    }
};

function advancedSearch() {
    var parameters = ""
    // AUFLAGEN
    if (prefix == "editions-") {
        parameters += "?query=alleAuflagen";
        // Titel Filter
        var titleString = document.getElementById('editions-filter-title-search').value;
        if (titleString != "") {
            titleString = cleanQuery(titleString);
            if (document.getElementById('editions-filter-title-radio').checked) {
                titleString = "!" + titleString;
            }
            parameters += "&edition_filterTitle=" + encodeURIComponent(titleString);
        }
        // Author Filter
        var authorString = document.getElementById('editions-filter-author-search').value;
        if (authorString != "") {
            authorString = cleanQuery(authorString);
            if (document.getElementById('editions-filter-author-radio').checked) {
                authorString = "!" + authorString;
            }
            parameters += "&edition_filterAuthorName=" + encodeURIComponent(authorString);
        }
        // Pubplace Filter
        var pubPlaceString = document.getElementById('editions-filter-pubPlace-search').value;
        if (pubPlaceString != "") {
            pubPlaceString = cleanQuery(pubPlaceString);
            if (document.getElementById('editions-filter-pubPlace-radio').checked) {
                pubPlaceString = "!" + pubPlaceString;
            }
            parameters += "&edition_filterPubPlaceName=" + encodeURIComponent(pubPlaceString);
        }
        // Pub Range of Date Filter
        var pubMinDate = document.getElementById('editions-filter-pubMinDate').value;
        var pubMaxDate = document.getElementById('editions-filter-pubMaxDate').value;
        if (pubMinDate != "" || pubMaxDate != "") {
            if (pubMinDate != "") {
                pubMinDate = cleanQuery(pubMinDate);
            }
            if (pubMaxDate != "") {
                pubMaxDate = cleanQuery(pubMaxDate);
            }
            parameters += "&edition_filterPubRangeOfDate=" + encodeURIComponent(pubMinDate) + "to" + encodeURIComponent(pubMaxDate);
        }
        // Format Filter
        var formatList =[]
        for (let checkbox of document.getElementsByClassName("editions-filter-format-checkbox")) {
            if (checkbox.checked) {
                formatList.push(checkbox.value);
            }
        }
        parameters += "&edition_filterFormat=" + encodeURIComponent(formatList.toString());

        // Sprache Filter
        var spracheInput = document.getElementById("editions-filter-language").value;
        if (spracheInput != "alle") {
            parameters += "&edition_filterLanguage=" + encodeURIComponent(spracheInput);
        }
        // Im Katalog Filter
        if (document.getElementById("editions-filter-in-catalog-checkbox").checked) {
            parameters += "&edition_FilterOccurence=true"
        }
    } else if (prefix == "persons-") {
        parameters += "?query=allePersonen";
        // Name Filter
        var nameString = document.getElementById('persons-filter-name-search').value;
        if (nameString != "") {
            nameString = cleanQuery(nameString);
            if (document.getElementById('persons-filter-name-radio').checked) {
                nameString = "!" + nameString;
            }
            parameters += "&person_filterName=" + encodeURIComponent(nameString);
        }
        // Birthcountry Filter
        var birthcountryString = document.getElementById('persons-filter-birthcountry-search').value;
        if (birthcountryString != "") {
            birthcountryString = cleanQuery(birthcountryString);
            if (document.getElementById('persons-filter-birthcountry-radio').checked) {
                birthcountryString = "!" + birthcountryString;
            }
            parameters += "&person_filterBirthCountryName=" + encodeURIComponent(birthcountryString);
        }
        // Deathcountry Filter
        var deathcountryString = document.getElementById('persons-filter-deathcountry-search').value;
        if (deathcountryString != "") {
            deathcountryString = cleanQuery(deathcountryString);
            if (document.getElementById('persons-filter-deathcountry-radio').checked) {
                deathcountryString = "!" + deathcountryString;
            }
            parameters += "&person_filterDeathCountryName=" + encodeURIComponent(deathcountryString);
        }
        // Organisation Filter
        var organisationString = document.getElementById('persons-filter-organisation-search').value;
        if (organisationString != "") {
            organisationString = cleanQuery(organisationString);
            if (document.getElementById('persons-filter-organisation-radio').checked) {
                organisationString = "!" + organisationString;
            }
            parameters += "&person_filterOrganisationName=" + encodeURIComponent(organisationString);
        }
        // Lifetime Range of Date Filter
        var lifeMinDate = document.getElementById('persons-filter-lifeMinDate').value;
        var lifeMaxDate = document.getElementById('persons-filter-lifeMaxDate').value;
        if (lifeMinDate != "" || lifeMaxDate != "") {
            if (lifeMinDate != "") {
                lifeMinDate = cleanQuery(lifeMinDate);
            }
            if (lifeMaxDate != "") {
                lifeMaxDate = cleanQuery(lifeMaxDate);
            }
            parameters += "&person_filterLifetimeRangeOfDate=" + encodeURIComponent(lifeMinDate) + "to" + encodeURIComponent(lifeMaxDate);
        }
        // Im Katalog Filter
        if (document.getElementById("persons-filter-in-catalog-checkbox").checked) {
            parameters += "&person_FilterOccurence=true";
        }
    } else if (prefix == "places-") {
        parameters += "?query=alleOrte";
        // Name Filter
        var nameString = document.getElementById('places-filter-name-search').value;
        if (nameString != "") {
            nameString = cleanQuery(nameString);
            if (document.getElementById('places-filter-name-radio').checked) {
                nameString = "!" + nameString;
            }
            parameters += "&place_filterName=" + encodeURIComponent(nameString);
        }
        // Country Filter
        var countryString = document.getElementById('places-filter-country-search').value;
        if (countryString != "") {
            countryString = cleanQuery(countryString);
            if (document.getElementById('places-filter-country-radio').checked) {
                countryString = "!" + countryString;
            }
            parameters += "&place_filterCountryName=" + encodeURIComponent(countryString);
        }
        // Im Katalog Filter
        if (document.getElementById("places-filter-in-catalog-checkbox").checked) {
            parameters += "&place_FilterOccurence=true";
        }
    }
    
    location.href = "datenbank.html" + parameters + "&resetCache=true&page=1";
};

function setSortingParameters(value) {
    var sortingKey = value.split("-")[0];
    var sortingDirection = value.split("-")[1];
    addURLParam([['page', '1'],[ 'resetCache', 'true'],[ 'sortingKey', sortingKey],[ 'sortingDirection', sortingDirection]]);
};

// Füllt die Formulare mit den Values aus den Paramtern nach Pageload
$(function () {
    
    function setSearchFields(filterName, p) {
        var inputString = p[1];
        if (p[1].startsWith("!")) {
            inputString = p[1].slice(1);
            document.getElementById(filterName + "-radio").checked = true;
        }
        document.getElementById(filterName + "-search").value = inputString.replaceAll("_", " ");
    }
    
    var searchParams = new URLSearchParams(window.location.search);
    var sortingKey = "";
    var sortingDirection = "";
    for (let p of searchParams) {
        switch (p[0]) {
            case "simpleSearchString":
            document.getElementById("simple-search-bar").value = p[1].replaceAll("_", " ");
            break;
            case "query":
            switch (p[1]) {
                case "alleAuflagen":
                switchAdvancedSearchEntityFilter(document.getElementById("filter-editions"), "editions-");
                break;
                case "allePersonen":
                switchAdvancedSearchEntityFilter(document.getElementById("filter-persons"), "persons-");
                break;
                case "alleOrte":
                switchAdvancedSearchEntityFilter(document.getElementById("filter-places"), "places-");
                break;
            }
            break;
            case "edition_filterTitle":
            setSearchFields("editions-filter-title", p);
            break;
            case "edition_filterAuthorName":
            setSearchFields("editions-filter-author", p);
            break;
            case "edition_filterPubPlaceName":
            setSearchFields("editions-filter-pubPlace", p);
            break;
            case "edition_filterPubRangeOfDate":
            var dates = p[1].split("to");
            var minDate = dates[0];
            var maxDate = dates[1];
            document.getElementById("editions-filter-pubMinDate").value = minDate;
            document.getElementById("editions-filter-pubMaxDate").value = maxDate;
            break;
            case "edition_filterFormat":
            var formats = p[1].split(",");
            for (var checkbox of document.getElementsByClassName("editions-filter-format-checkbox")){
                if (formats.includes(checkbox.value)){
                    checkbox.checked = true;
                } else {
                    checkbox.checked = false;
                }
            }
            break;
            case "edition_filterLanguage":
            document.getElementById("editions-filter-language").value = p[1];
            break;
            case "edition_FilterOccurence":
            if (p[1] == "true"){
                document.getElementById("editions-filter-in-catalog-checkbox").checked = true;
            } else {
                document.getElementById("editions-filter-in-catalog-checkbox").checked = false;
            }
            break;
            case "person_filterName":
            setSearchFields("persons-filter-name", p);
            break;
            case "person_filterBirthCountryName":
            setSearchFields("persons-filter-birthcountry", p);
            break;
            case "person_filterDeathCountryName":
            setSearchFields("persons-filter-deathcountry", p);
            break;
            case "person_filterOrganisationName":
            setSearchFields("persons-filter-organisation", p);
            break;
            case "person_filterLifetimeRangeOfDate":
            var dates = p[1].split("to");
            var minDate = dates[0];
            var maxDate = dates[1];
            document.getElementById("persons-filter-lifeMinDate").value = minDate;
            document.getElementById("persons-filter-lifeMaxDate").value = maxDate;
            break;
            case "person_FilterOccurence":
            if (p[1] == "true"){
                document.getElementById("persons-filter-in-catalog-checkbox").checked = true;
            } else {
                document.getElementById("persons-filter-in-catalog-checkbox").checked = false;
            }
            break;
            case "place_filterName":
            setSearchFields("places-filter-name", p);
            break;
            case "place_filterCountryName":
            setSearchFields("places-filter-country", p);
            break;   
            case "place_FilterOccurence":
            if (p[1] == "true"){
                document.getElementById("places-filter-in-catalog-checkbox").checked = true;
            } else {
                document.getElementById("places-filter-in-catalog-checkbox").checked = false;
            }
            break;
            case "sortingKey":
            sortingKey = p[1];
            break;
            case "sortingDirection":
            sortingDirection = p[1];
            break;
        }
    }
    var sortingValue = sortingKey + "-" + sortingDirection;
    if (sortingValue.length > 1) {
        document.getElementById("sorting-form-control").value = sortingValue;
    }
});


// Paging-Buttons unter Ergebnisliste aufbauen
$(function () {
    var currentPage = 1;
    if ('URLSearchParams' in window) {
        var searchParams = new URLSearchParams(window.location.search);
        var x = parseInt(searchParams. get ('page'));
        if (x) {
            currentPage = x
        };
    }
    
    var pagingDiv = document.getElementById('paging-ul');
    if (pagingDiv) {
        var hits = parseInt(pagingDiv.getAttribute('data-hits'));
        var hitsPerPage = parseInt(pagingDiv.getAttribute('data-hitsPerPage'));
        var lastPageNumber = Math.ceil(hits / hitsPerPage);
        // Pfeil links
        var arrowDisabled = "";
        if (currentPage == 1) {
            arrowDisabled = " disabled"
        };
        pagingDiv.innerHTML = '<li class="page-item' + arrowDisabled + '"> <a class="page-link arrow-left" onclick="jumpToPage(this)"><i class="fas fa-caret-left"/></a></li>';
        // Immer Seite 1
        pagingDiv.innerHTML += '<li class="page-item hide-when-smallest" id="page' + '1' + '"><a class="page-link page-number" onclick="jumpToPage(this)">1</a></li>';
        
        // ...
        if ((currentPage >= 5) && (lastPageNumber > 9)) {
            pagingDiv.innerHTML += '<li class="page-item disabled hide-when-smallest"><a class="page-link">...</a></li>';
        }
        
        // 5, 6, 7 etc.
        var pageBeginning;
        var pageEnd;
        if (lastPageNumber <= 9) {
            // Alle Seitenzahlen
            pageBeginning = 2;
            pageEnd = lastPageNumber;
        } else if (currentPage < 5) {
            // Wenn links
            pageBeginning = 2;
            pageEnd = 7;
        } else if (currentPage > lastPageNumber - 4) {
            // Wenn rechts
            pageBeginning = lastPageNumber - 5;
            pageEnd = lastPageNumber;
        } else {
            // Wenn mittendrin
            pageBeginning = currentPage - 2;
            pageEnd = currentPage + 3;
        }
        for (let i = pageBeginning; i < pageEnd; i++) {
            pagingDiv.innerHTML += '<li class="page-item hide-when-smaller" id="page' + i + '"><a class="page-link page-number" onclick="jumpToPage(this)">' + i + '</a></li>';
        }
        
        // ...
        if ((currentPage <= lastPageNumber - 4) && (lastPageNumber > 9)) {
            pagingDiv.innerHTML += '<li class="page-item disabled hide-when-smallest"><a class="page-link">...</a></li>';
        }
        
        // Immer letzte Seite
        if (lastPageNumber > 1) {
            pagingDiv.innerHTML += '<li class="page-item hide-when-smallest" id="page' + lastPageNumber + '"><a class="page-link page-number" onclick="jumpToPage(this)">' + lastPageNumber + '</a></li>';
        }
        
        // Pfeil rechts
        var arrowDisabled = "";
        if (currentPage == lastPageNumber) {
            arrowDisabled = " disabled"
        }
        pagingDiv.innerHTML += '<li class="page-item' + arrowDisabled + '"> <a class="page-link arrow-right" onclick="jumpToPage(this)"><i class="fas fa-caret-right"/></a></li>';
        
        
        // Aktivstellen der aktuellen Seite:
        var currentPageButton = document.getElementById('page' + currentPage);
        currentPageButton.classList.add('active');
        currentPageButton.classList.remove('hide-when-smaller');
        currentPageButton.classList.remove('hide-when-smallest');
    }
});


function jumpToPage(source) {
    var currentPageNumber = 1;
    var futurePageNumber;
    if ('URLSearchParams' in window) {
        var searchParams = new URLSearchParams(window.location.search);
        currentPageNumber = parseInt(searchParams. get ('page'))
    }
    
    if (source.classList.contains('page-number')) {
        futurePageNumber = parseInt(source.innerHTML);
    } else if (source.classList.contains('arrow-right')) {
        futurePageNumber = currentPageNumber + 1;
    } else if (source.classList.contains('arrow-left')) {
        futurePageNumber = currentPageNumber - 1;
    }
    
    addURLParam([[ 'resetCache', 'false'],[ 'page', futurePageNumber]]);
};

function switchAdvancedSearchEntityFilter(source, newPrefix) {
    prefix = newPrefix;
    
    // "checked" entfernen
    for (let elem of document.getElementsByClassName("checkbutton")) {
        elem.classList.remove("checked");
    }
    // "checked" hinzufügen
    source.classList.add("checked")
    
    // alle auf "hidden"
    for (let elem of document.getElementsByClassName("filter-div")) {
        elem.classList.add("hidden");
    }
    // "hidden" entfernen
    document.getElementById(prefix + "filter-div").classList.remove("hidden")
}