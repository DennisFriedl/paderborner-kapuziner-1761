// Passt Schriftgröße der Überschrift an Überschriftslänge an.
$(document).ready(function () {
    var mainTitle = document.getElementsByTagName("h1")[0];
    if (mainTitle.innerHTML.length > 750) {
        mainTitle.style.fontSize = "1.4em";
    } else if (mainTitle.innerHTML.length > 650) {
        mainTitle.style.fontSize = "1.75em";
    } else if (mainTitle.innerHTML.length > 400) {
        mainTitle.style.fontSize = "2em";
    } else if (mainTitle.innerHTML.length > 260) {
        mainTitle.style.fontSize = "2.25em";
    } else if (mainTitle.innerHTML.length > 220) {
        mainTitle.style.fontSize = "2.5em";
    } else if (mainTitle.innerHTML.length > 150) {
        mainTitle.style.fontSize = "2.75em";
    }
});


function setEntityPicture(type, wikidataID) {
    if (wikidataID) {
        var url = "https://www.wikidata.org/wiki/Special:EntityData/" + wikidataID + ".json?flavor=dump"
        var imageName = null;
        $. get (url, function (data) {
            function namePath(property) {
                return data[ "entities"][wikidataID][ "claims"][property][0][ "mainsnak"][ "datavalue"][ "value"];
            };
            if (type == "place") {
                try {
                    imageName = namePath("P94");
                }
                catch (e) {
                    try {
                        imageName = namePath("P41");
                    }
                    catch (e) {
                        imageName = namePath("P18");
                    }
                }
            } else if (type == "person") {
                try {
                    imageName = namePath("P18");
                }
                catch (e) {
                    imageName = null;
                }
            }
            if (imageName && imageName.endsWith(".tif")){imageName = null;} // TIF-Bilder können im Browser nicht angezeigt werden
            if (imageName) {
                imageName = imageName.replaceAll(" ", "_");
                hash = $.md5(imageName);
                var imageURL = "https://upload.wikimedia.org/wikipedia/commons/" + hash[0] + "/" + hash[0] + hash[1] + "/" + imageName;
                document.getElementById("entity-image").setAttribute("src", imageURL);
                document.getElementById("entity-image-caption").innerHTML = "<a href='https://commons.wikimedia.org/wiki/File:" + imageName + "' target='_blank'>Quelle</a>";
            } else {
                document.getElementById("entity-image-caption").innerHTML = "Ohne Bild";
            }
        });
    } else {
        document.getElementById("entity-image-caption").innerHTML = "Ohne Bild";
    }
};