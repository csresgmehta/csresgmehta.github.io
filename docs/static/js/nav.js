// Lets the "Services" nav dropdown be reached on touch devices, where
// CSS :hover never fires.
//
// A dedicated toggle button (sibling of the <a>, not nested inside it)
// isn't reliable here: on real touch input, Chromium snaps an ambiguous
// tap near a small target to the larger, more prominent nearby link
// instead — so a separate button next to "Services" still ends up
// targeting the link and navigating away.
//
// Instead this intercepts taps on the link itself while the mobile nav
// is in its collapsed (hamburger) layout: the first tap opens the
// submenu instead of navigating; a second tap (now that it's open)
// navigates through normally. Desktop is untouched — :hover already
// handles it there, and the media query guards the touch behavior to
// small screens only.
(function () {
  var mobileQuery = window.matchMedia("(max-width: 720px)");

  function closeDropdown(li) {
    li.classList.remove("dropdown-open");
    var toggle = li.querySelector(":scope > .dropdown-toggle");
    if (toggle) toggle.setAttribute("aria-expanded", "false");
  }

  function openDropdown(li) {
    document.querySelectorAll(".main-nav li.has-dropdown.dropdown-open").forEach(function (openLi) {
      if (openLi !== li) closeDropdown(openLi);
    });
    li.classList.add("dropdown-open");
    var toggle = li.querySelector(":scope > .dropdown-toggle");
    if (toggle) toggle.setAttribute("aria-expanded", "true");
  }

  document.querySelectorAll(".main-nav li.has-dropdown").forEach(function (li) {
    var link = li.querySelector(":scope > a");
    var toggle = li.querySelector(":scope > .dropdown-toggle");

    if (toggle) {
      toggle.addEventListener("click", function (e) {
        e.preventDefault();
        li.classList.contains("dropdown-open") ? closeDropdown(li) : openDropdown(li);
      });
    }

    if (link) {
      link.addEventListener("click", function (e) {
        if (mobileQuery.matches && !li.classList.contains("dropdown-open")) {
          e.preventDefault();
          openDropdown(li);
        }
        // Already open (or on desktop) - let the tap navigate normally.
      });
    }
  });
})();
