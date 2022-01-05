import csv
parsed_authors = []

with open("magazine_authors.csv") as authors_csv:
    reader = csv.reader(authors_csv)
    authors = list(reader)

    for author in authors:
        original_name = author[0]
        author_split = original_name.split(sep=" ")
        family_name = author_split.pop()
        given_name = " ".join(author_split)

        parsed_author = {
            "given_name": given_name,
            "family_name": family_name,
            "original_name": original_name,
        }

        parsed_authors.append(parsed_author)

with open("magazine_authors_parsed.csv", "w", newline="") as parsed_authors_csv:
    fieldnames = ["given_name", "family_name", "original_name"]
    writer = csv.DictWriter(
        parsed_authors_csv,
        fieldnames=fieldnames,
    )

    writer.writeheader()

    for author in parsed_authors:
        writer.writerow(author)
