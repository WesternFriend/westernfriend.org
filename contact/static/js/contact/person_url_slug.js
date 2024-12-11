import { unidecode } from "https://cdn.jsdelivr.net/npm/unidecode@0.1.8/unidecode.min.js";

function generateAutoslug() {
  /*
  Auto-generate slug from given and family name fields.
  This is used for adding Person contacts and Memorials
  */
  let slug_text = "";

  const given_name_element = document.getElementById("id_given_name");
  const family_name_element = document.getElementById("id_family_name");
  const slug_element = document.getElementById("id_slug");

  if (!given_name_element || !family_name_element || !slug_element) {
    // If any of the elements do not exist, return early
    return;
  }

  const given_name = given_name_element.value;
  const family_name = family_name_element.value;

  if (given_name && family_name) {
    slug_text = `${given_name} ${family_name}`;
  } else if (given_name) {
    slug_text = given_name;
  }

  if (slug_text) {
    const slugified_name = cleanForSlug(slug_text);
    slug_element.value = slugified_name;
  }
}

function registerNameElementEventListeners() {
  /*
  When the page content loads
  register change listeners on given_name and family_name fields
  TODO: only run this hook on Contact edit forms
  */
  const given_name_element = document.getElementById("id_given_name");
  const family_name_element = document.getElementById("id_family_name");

  if (!given_name_element || !family_name_element) {
    // If any of the elements do not exist, return early
    return;
  }

  given_name_element.addEventListener("change", generateAutoslug);
  family_name_element.addEventListener("change", generateAutoslug);
}

document.addEventListener(
  "DOMContentLoaded",
  registerNameElementEventListeners,
);

function cleanForSlug(text) {
  /*
  Clean text for use in a URL by:
  - converting Unicode characters to ASCII
  - making it lowercase
  - replacing spaces with hyphens
  - replace all sequences of one or more characters that are not
    alphanumeric, not underscores, and not hyphens, with an empty string
  */
  const ascii_text = unidecode(text);
  const slug_text = ascii_text
    .toLowerCase()
    // replace spaces with hyphens
    .replace(/ /g, "-")
    // remove all non-word chars
    .replace(/[^\w-]+/g, "");

  return slug_text;
}
