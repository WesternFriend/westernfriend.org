# Search N+1 Query Optimization

## Problem Description

The search functionality was experiencing N+1 query issues, particularly when displaying magazine articles with their authors. The problem manifested as:

1. An initial search query to get results
2. Additional `COUNT(*)` queries for each magazine article to check `magazinearticleauthor` relationships
3. Additional queries to fetch author details when accessing `author.author.title` in templates

## SQL Queries Observed

The problematic pattern showed queries like:
```sql
SELECT COUNT(*) AS "__count"
FROM "magazine_magazinearticleauthor"
WHERE "magazine_magazinearticleauthor"."article_id" = %s
```

This query was being executed once for each magazine article in the search results, creating the classic N+1 pattern.

## Solution

### Modified `search/views.py`

The search view was optimized to use `prefetch_related()` to eagerly load related data:

```python
search_results = (
    Page.objects.live()
    .search(search_query, operator="or")
    .select_related("owner", "content_type", "locale")
    .prefetch_related(
        # For magazine articles - prefetch authors and departments
        "magazinearticle__authors__author",
        "magazinearticle__department",
        # For magazine issues - prefetch cover images
        "magazineissue__cover_image",
        # For archive articles - prefetch authors
        "archivearticle__archive_authors__author",
    )
    .specific()
)
```

### Key Changes

1. **Separated search from optimization**: First perform the search, then apply optimizations
2. **Used prefetch_related**: Added prefetch paths for the most common related data accessed in templates
3. **Added select_related**: Optimized foreign key relationships that are always accessed
4. **Moved .specific() after prefetch**: Ensures prefetch relationships are preserved

### Prefetch Paths Explained

- `"magazinearticle__authors__author"`: Prefetches the MagazineArticleAuthor relationship and the related author Page object
- `"magazinearticle__department"`: Prefetches the department for magazine articles
- `"magazineissue__cover_image"`: Prefetches cover images for magazine issues
- `"archivearticle__archive_authors__author"`: Prefetches authors for archive articles

### Template Optimization

The templates (`search/magazine_article.html`, etc.) already access the related data efficiently:

```html
{% for author in entity.specific.authors.all %}
    <a href="{% pageurl author.author %}">
        {{ author.author.title }}
    </a>
{% endfor %}
```

With the prefetch optimization, these template accesses no longer trigger additional database queries.

## Testing

Comprehensive tests have been added to the search test suite (`search/tests.py`) to verify the optimization works correctly:

### SearchOptimizationTestCase

1. **test_search_query_optimization**: Verifies that accessing author relationships in search results does not trigger additional database queries (N+1 prevention)
2. **test_search_results_include_authors**: Ensures that author information is properly accessible in search results

The tests use Django's `override_settings(DEBUG=True)` to enable query logging and verify that:
- Initial search queries execute properly
- Accessing prefetched relationships triggers zero additional queries
- Search results maintain proper functionality

## Expected Results

With this optimization:

- Initial search queries may be slightly higher due to prefetch joins
- Accessing author information in templates should trigger **zero additional queries**
- Overall page load time and database load should be significantly reduced
- The N+1 query pattern should be eliminated

## Compatibility

This change is backward compatible and follows Django/Wagtail best practices for query optimization. The optimization only affects the search view and doesn't change any model definitions or template logic.

## Future Considerations

If additional search result types are added that require related data, their prefetch paths should be added to the `prefetch_related()` call in the search view.
