function addURLParam(input) {
    // input ist Array von Arrays. In den verschachtelten Arrays ist [0] der Paramtername und [1] der Wert
    if ('URLSearchParams' in window) {
        var searchParams = new URLSearchParams(window.location.search);
        for (let x of input) {
            searchParams. set (x[0], x[1]);
        }
        window.location.search = searchParams.toString();
    }
};

// Überprüft, ob die Eingabe eine Ziffer ist.
function isNumberKey(evt) {
    var charCode = (evt.which) ? evt.which: evt.keyCode;
    if (charCode > 31 && (charCode < 48 || charCode > 57)) {
        return false;
    }
    return true;
};

// Überprüft, ob die Eingabe eine Ziffer oder Minus ist.
function isNumberOrMinusKey(evt) {
    var charCode = (evt.which) ? evt.which: evt.keyCode;
    if (charCode == 45) {
        return true;
    } else if (charCode > 31 && (charCode < 48 || charCode > 57)) {
        return false;
    }
    return true;
};




