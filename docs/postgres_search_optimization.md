# PostgreSQL Search Optimization for WesternFriend

This document provides recommendations for optimizing the PostgreSQL database configuration for better search performance in the WesternFriend project.

## Database Search Index Optimization

The WesternFriend project uses Wagtail's database search backend, which relies on PostgreSQL's full-text search capabilities. Here are recommendations to improve search performance:

### 1. PostgreSQL Configuration Tuning

Add or update the following settings in your `postgresql.conf` file:

```
# Memory configuration
shared_buffers = 256MB        # Increase for production servers (25% of RAM)
work_mem = 16MB               # Increase for complex search queries
maintenance_work_mem = 128MB  # Helps with index creation
effective_cache_size = 1GB    # Set to 50-75% of total RAM

# Query planner tuning
random_page_cost = 1.1        # Lower for SSDs (default is 4.0)
effective_io_concurrency = 200  # Higher for SSDs

# Vacuum and autovacuum
autovacuum = on
```

### 2. Create Functional Indexes for Search

Consider adding functional indexes for frequently searched text fields. For example, you can create a GIN index for the title and body fields:

```sql
-- Create a GIN index on the title field (run as SQL query)
CREATE INDEX page_title_search_idx ON wagtailcore_page
USING GIN (to_tsvector('english', title));

-- For other common search fields in your models
CREATE INDEX article_body_search_idx ON magazine_magazinearticle
USING GIN (to_tsvector('english', body));
```

### 3. Table Partitioning

For very large tables (millions of rows), consider partitioning by logical categories:

```sql
-- Example: Partition the Page table by content type
-- This is a complex operation requiring database migration planning
```

### 4. Regular Database Maintenance

Schedule regular maintenance tasks:

```sql
-- Analyze tables to update statistics
ANALYZE;

-- Vacuum tables to reclaim space and update indexes
VACUUM FULL;

-- Reindex to optimize index performance
REINDEX DATABASE westernfriend;
```

## Application-Level Optimizations

1. **Run the Rebuild Index Command**: After significant content changes, rebuild the search index:
   ```
   python manage.py rebuild_search_index
   ```

2. **Configure Django Cache**: Ensure Django's cache system is properly configured in settings.py:
   ```python
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.memcached.PyMemcacheCache',
           'LOCATION': '127.0.0.1:11211',
           'TIMEOUT': 3600,  # 1 hour
       }
   }
   ```

3. **Monitor Query Performance**: Use Django Debug Toolbar or PostgreSQL's explain analyze:
   ```sql
   EXPLAIN ANALYZE SELECT ... your query here ...;
   ```

4. **Connection Pooling**: For production, consider using PgBouncer or similar connection pooling solutions.

By implementing these recommendations, the PostgreSQL-based search functionality should perform significantly better, especially under load.
