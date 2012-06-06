
chrome.tabs.onUpdated.addListener(function(tabId, changeInfo, tab){
  if(changeInfo.status == "complete"){
// THIS WORKS
//    chrome.tabs.executeScript(tabId, { code: "window.open('','_self','');window.close(); " });
  }
});

/*
chrome.tabs.onUpdated.addListener(function(tabId, changeInfo, tab) {
    if(changeInfo.status == "complete") {
        chrome.tabs.sendRequest(tab.id, {action: "getDoc"}, function(response) {
            response.doc.body.style.background = "purple";
        });
        //if(tab.url == "http://www.delicious.com/save") {
        //    chrome.tabs.remove(tabId);
        //}
        //var puzzle = tab.getElementsByTagName("title")[0] === undefined;
        //if (!puzzle) {
        //    //chrome.tabs.remove(tabId);
        //    tab.body.style.background = "purple";
        //}
    }
});
*/
