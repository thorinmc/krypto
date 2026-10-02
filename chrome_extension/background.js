function sendTabs() {
  chrome.tabs.query({}, function(tabs) {
    let tabData = tabs.map(tab => ({
      title: tab.title,
      url: tab.url
    }));

    fetch("http://127.0.0.1:5000/tabs", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ tabs: tabData })
    }).catch(err => console.error("Błąd wysyłania do bota:", err));
  });
}

setInterval(sendTabs, 5000);