function generateAutoslug() {
  var slug_text = undefined;

  var given_name = $("#id_given_name").val();
  var family_name = $("#id_family_name").val();

  if (given_name && family_name) {
    slug_text = `${given_name} ${family_name}`;
  } else if (given_name) {
    slug_text = given_name;
  }

  if (slug_text) {
    var slugified_name = cleanForSlug(slug_text, true);

    $("#id_slug").val(slugified_name);
  }
}

$(function autopopulateSlugForContact() {
  $("#id_given_name").on("change", function() {
    generateAutoslug();
  });

  $("#id_family_name").on("change", function() {
    generateAutoslug();
  });
});
