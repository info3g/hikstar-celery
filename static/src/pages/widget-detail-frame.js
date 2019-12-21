const resultsListID = ".results-page";
const searchPanelID = "#search-panel";
const detailBoxID = "#detail-box";
const hideClass = "hideOnResults";

function hideDetail(element) {
  $(detailBoxID).addClass(hideClass);
}

function displayDetail(element) {
  $(detailBoxID).removeClass(hideClass);
}

function hideSearchElements() {
  $(searchPanelID).addClass(hideClass);
  $(resultsListID).addClass(hideClass);
}

function displaySearchElements() {
  $(searchPanelID).removeClass(hideClass);
  $(resultsListID).removeClass(hideClass);
}

function openDetailFrame(url) {
  let detailBox;
  try {
    detailBox = window.parent.document.getElementById("detail-box");
  } catch (DOMException) {
    detailBox = document.getElementById("detail-box");
  }

  initDetailFrame(url, detailBox);
  hideSearchElements();
  displayDetail();
}

function closeDetailFrame() {
  hideDetail();
  removeDetailFrame();
  displaySearchElements();
}

function backDetailFrame() {
  this.classList.add('d-none');
  window.history.back();
}

function initDetailFrame(url, parentElement) {
  let detailFrame = document.createElement("iframe");
  const iframes = parentElement.getElementsByTagName("iframe");

  if (iframes.length > 0) {
    detailFrame = iframes[0];
    detailFrame.src = url;
    const backBtn = parentElement.getElementsByClassName('back-button')
    if (backBtn) {
      backBtn[0].classList.remove('d-none')
    }
  } else {
    detailFrame.src = url;
    detailFrame.setAttribute("position", "absolute");
    detailFrame.setAttribute("width", "100%");
    detailFrame.setAttribute(
      "height",
      parentElement.parentElement.scrollHeight + "px"
    );
    detailFrame.setAttribute("scrolling", "yes");

    var closeButton = document.createElement("button");
    closeButton.id = "closeButton";
    closeButton.onclick = closeDetailFrame;
    closeButton.innerHTML = CLOSE_LABEL;

    var backButton = document.createElement("button");
    backButton.id = "backButton";
    backButton.onclick = backDetailFrame;
    backButton.innerHTML = BACK_LABEL;
    backButton.classList.add('d-none', 'back-button')
    parentElement.appendChild(backButton);

    parentElement.appendChild(closeButton);
    parentElement.appendChild(detailFrame);
  }

}

function openWithCorrectUrl(url) {
  var subHikes = "hikes";

  var startIndex = url.indexOf(subHikes);
  if (startIndex === -1) {
    return;
  }

  var baseUrl = url.substring(0, startIndex);
  var inserted = "map-widget/";
  var endPoint = url.substring(startIndex);

  var updatedUrl = baseUrl + inserted + endPoint + '?' + WIDGET_PARAMS;
  console.log(url + " updated as " + updatedUrl);
  openDetailFrame(updatedUrl);
}

function removeDetailFrame() {
  $(detailBoxID).html("");
}
