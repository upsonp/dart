var position = 0;
// var tabCount = 0;

// lets move to using this function and phasing out others
function hotKey(targetId, keyName) {
    $(document).keydown(function (event) {
        if (event.key == keyName) {
            event.preventDefault();
            $("#" + targetId)[0].click();
        }
    });
}

function assignIndexToElements(indexName, className) {
    for (var i = 0; i < $("." + className).length; i++) {
        $("." + className)[i].setAttribute(indexName, i)
    }
    // have this variable called position that will always have the index of the focused element
    $("." + className).focus(function () {
        position = Number(this.getAttribute(indexName))
    })
}


function startFocusOnElement(targetId, altTargetId = null, selectText = true) {
    $(document).ready(function () {
        $primary = $("#" + targetId);
        $secondary = $("#" + altTargetId);

        if ($primary.length === 0 && $secondary.length > 0) {
            $secondary[0].focus();
            if (selectText) {
                $secondary[0].select();
            }
        } else {
            $primary[0].focus();
            if (selectText) {
                $primary[0].select();
            }
        }
    });
}

function disableKey(keyName) {
    $(document).keydown(function (event) {
        if (event.key == keyName) {
            event.preventDefault()
        }
    });
}

function escapeKey(targetId) {
    $(document).keydown(function (event) {
        if (event.key == 'Escape') {
            event.preventDefault()
            $("#" + targetId)[0].click();
        }
    });
}


function upDownKeys(className) {
    $(document).keydown(function (event) {
        // var myPosition = 0
        //  DOWN ARROW KEY
        if (event.key == 'ArrowDown') {
            event.preventDefault();
            myPosition = position + 1;
            $("." + className + ":eq(" + myPosition + ")").select();
            $("." + className + ":eq(" + myPosition + ")")[0].focus();
        }

        //  UP ARROW KEY
        else if (event.key == 'ArrowUp') {
            event.preventDefault();
            myPosition = position - 1;
            $("." + className + ":eq(" + myPosition + ")").select();
            $("." + className + ":eq(" + myPosition + ")")[0].focus();
        }

    });
}

function enterKey(className, submitButtonId) {
    $(document).keydown(function (event) {

        // determine how many fields there are
        var maxCount = $("." + className).length;
        if (event.key == 'Enter') {
            event.preventDefault();
            // DESIRED BEHAVIOUR:
            // if you press enter, it will act as down arrow, unless you are on the last field, at which point
            // it will act as a submit button

            // if we are on the last button
            if (position == maxCount - 1) {
                console.log(submitButtonId);
                $("#" + submitButtonId)[0].click()
            }
            // else, jump to the next record
            else {
                var myPosition = position +1;
                $("." + className)[position + 1].focus();
                $("." + className + ":eq("  + myPosition + ")").select()
            }
        }
    });
}


function pageUpDownKeys(prevPageHref, nextPageHref) {
    $(document).keydown(function (event) {
        if (event.key == 'PageDown') {
            event.preventDefault()
            document.location.href = nextPageHref;
        } else if (event.key == 'PageUp') {
            event.preventDefault()
            document.location.href = prevPageHref;
        }
    });
}

function combinationKey(keyName, targetId) {
    keyName = keyName.toUpperCase()
    document.addEventListener("keydown", function (zEvent) {
        if (zEvent.ctrlKey && zEvent.code === "Key" + keyName) {
            zEvent.preventDefault()
            $("#" + targetId)[0].click();
        }
    });
}
