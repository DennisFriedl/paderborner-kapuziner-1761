// Springe zur Editionsseite durch die Strukturlinks
function jumpToEditionPageWithStructure(source) {
    let page = (parseInt(source.querySelectorAll('.structure-page')[0].innerHTML));
    addURLParam([[ 'page', page]]);
}


// Geht in der Edition eine Seite vor oder zurück
function turnEditionPage(source) {
    let step = parseInt($(source).data('step'));
    document.getElementById('pageInput').value = parseInt(document.getElementById('pageInput').value) + step;
    jumpToEditionPageWithForm();
}

// Springt zur richtigen Editionsseite durch das Formular
function jumpToEditionPageWithForm() {
    let queryString = window.location.search;
    let urlParams = new URLSearchParams(queryString);
    let page = urlParams. get ('page');
    
    let formValue = document.getElementById('pageInput').value;
    
    if (page != formValue) {
        if (formValue < 1) {
            formValue = 1;
        } else if (formValue > 367) {
            formValue = 367;
        }
        addURLParam([[ 'page', formValue]]);
    }
}

// Event Listener für Klick auf Strukurbutton
$(document).ready(function () {
    document.getElementById("struktur-button").addEventListener("click", function(){
            $('.dropdown-content').css('display', 'block');
        }); 
});
// Event Listener für Klick außerhalb von Strukurbutton, um zu schließen
document.addEventListener('click', function (event) {
  if (!document.getElementById("struktur-button").contains(event.target)) {
    $('.dropdown-content').css('display', 'none');
  }
});


// Event Listener für das Seiteneingabefeld
$(document).ready(function () {
    let input = document.getElementById('pageInput');
    
    // Enter-Taste
    input.addEventListener("keyup", function (event) {
        if (event.keyCode === 13) {
            event.preventDefault();
            jumpToEditionPageWithForm();
        };
    });
    
    // Out of focus
    input.addEventListener('focusout', (event) => {
        jumpToEditionPageWithForm();
    });
});


// URL-Paramter für Page wird in das Eingabefeld eingetragen
$(document).ready(function () {
    let queryString = window.location.search;
    let urlParams = new URLSearchParams(queryString);
    let page = urlParams. get ('page');
    
    let formValue = document.getElementById('pageInput').value;
    
    if (page != formValue) {
        document.getElementById('pageInput').value = page;
    }
});

// Click auf die Entitäten, um zur Seite für die Entität zu kommen.
$(document).ready(function () {
    document.querySelectorAll('.entity-link').forEach(item => {
        item.addEventListener('click', event => {
            let link = item.getAttribute('data-ref');
            window.open(link, '_blank').focus();
        })
    })
});


// Hole IIIF-Info der Seite und erstelle OpenSeaDragon
$(document).ready(function () {
    let queryString = window.location.search;
    let urlParams = new URLSearchParams(queryString);
    let page = urlParams. get ('page');
    
    $. get ("https://digital.ub.uni-paderborn.de/i3f/v20/6084969/manifest", function (data) {
        let jsonInfo = data.sequences[0].canvases[parseInt(page) -1].images[0].resource.service[ '@id'] + "/info.json";
        var viewer = new OpenSeadragon.Viewer({
            id: "edition-scan-image-col",
            prefixUrl: "../resources/lib/openseadragon/images/",
            tileSources: jsonInfo
        });
    });
});

// Trage die richtige Seitenangabe (unabhängig von der Scanseite) ein
$(document).ready(function () {
    let queryString = window.location.search;
    let urlParams = new URLSearchParams(queryString);
    let page = urlParams. get ('page');
    let field = document.getElementById('content-page-indicator');
    let value = "";
    
    if (page == "1") {
        value = "Vorderdeckel";
    } else if (page == "2") {
        value = "Vorderdeckel Innenseite";
    } else if (page == "3") {
        value = "Vorsatz";
    } else if (page == "4") {
        value = "Leerseite";
    } else if (page == "5") {
        value = "Titelblatt";
    } else if (page == "7") {
        value = "Chronogramm";
    } else if (parseInt(page) >= 312) {
        value = "Leerseite";
    } else {
        value = "Seite " + document.getElementById('page-number').innerHTML;
    }
    
    
    field.innerHTML = value;
});
