function generateAutoslug() {
  /*
  Auto-generate slug from given and family name fields.
  This is used for adding Person contacts and Memorials
  */
  let slug_text = "";

  const given_name = document.getElementById("id_given_name").value;
  const family_name = document.getElementById("id_family_name").value;

  if (given_name && family_name) {
    slug_text = `${given_name} ${family_name}`;
  } else if (given_name) {
    slug_text = given_name;
  }

  if (slug_text) {
    const slugified_name = cleanForSlug(slug_text, true);

    document.getElementById("id_slug").value = slugified_name;
  }
}

function registerNameElementEventListeners() {
  /*
  When the page content loads
  register change listeners on given_name and family_name fields
  TODO: only run this hook on Contact edit forms
  */
  document
    .getElementById("id_given_name")
    .addEventListener("change", generateAutoslug);

  document
    .getElementById("id_family_name")
    .addEventListener("change", generateAutoslug);
}

document.addEventListener(
  "DOMContentLoaded",
  registerNameElementEventListeners
);
