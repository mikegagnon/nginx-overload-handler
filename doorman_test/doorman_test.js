
var puzzle = document.getElementsByTagName("title")[0] === undefined;

function spawn() {
    window.open(window.location,'_blank');
}

// If it's a puzzle page then then wait until
if (puzzle) {
    document.body.style.background = "pink";
    window.onbeforeunload = spawn;
} else {
    // If its a page resulting from a solved puzzle,
    // then just close the tab
    if (window.location.href.search("&key=") >= 0 ||
        window.location.href.search("\\?key=") >= 0) {
            window.open('','_self','');window.close();
    }
    // If it's a page that never had a puzzle then
    // just keep spawning more.
    else {
        if (window.location.href.search("&diff") >= 0) {
            spawn();
        }

        // refresh
        window.location.href=window.location.href
    }
}

