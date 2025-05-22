
# Row Key Design Decisions for WebTable

## 1. Overall Structure: `{salt}:{reversed_domain}{path}`

Our row key structure follows a `{salt}:{reversed_domain}{path}` format, for example: `a1:com.example/products`. This design balances multiple competing requirements for HBase performance and usability.

## 2. Salting to Prevent Region Server Hotspotting

### Problem Addressed
Without salting, pages from popular domains would create write hotspots, as sequential row keys (e.g., `com.example/page1`, `com.example/page2`) would all be written to the same region server.

### Solution
We apply a 2-character hexadecimal salt prefix generated from the domain, creating 256 possible prefixes that distribute writes across region servers. This ensures:

- Write operations for any domain are distributed across multiple region servers
- No single region server becomes a bottleneck during high-volume ingestion
- Data from same domain still resides in a limited number of predictable regions

### Implementation Details
- Salt generation uses first 2 characters of MD5 hash of the domain
- Pre-split regions using 16 evenly distributed prefixes ('00', '10', '20'...'f0') to avoid region splits during initial data loading
- Consistent hashing ensures pages from same domain always use same salt prefix

## 3. Reversed Domain Components

### Problem Addressed
Regular domain names (e.g., `example.com`, `support.example.com`) would not naturally group together in HBase's lexicographically ordered storage.

### Solution
We reverse the domain components (e.g., `com.example`, `com.example.support`), which ensures:

- All subdomains of a domain are stored contiguously
- Efficient scanning of entire domains with a single row prefix scan
- Natural hierarchical grouping that matches DNS hierarchy

### Benefits
- Content audits for entire domains become efficient single-scan operations
- Hierarchical data organization mirrors the natural domain ownership hierarchy
- Enables efficient filtering and scanning by domain without secondary indexes

## 4. Path Inclusion

### Problem Addressed
Web pages need a unique identifier that maintains their hierarchical relationship.

### Solution
We append the URL path directly after the reversed domain, maintaining the URL's hierarchical structure:

- Keeps all pages from the same path directory adjacent in storage
- Enables efficient scanning of all pages within a directory
- Preserves the semantic structure of the original URL

## 5. Tall-Narrow vs. Flat-Wide Design Choice

### Problem Addressed
HBase designs can either use many rows with fewer columns (tall-narrow) or fewer rows with many columns (flat-wide).

### Decision
We chose a tall-narrow design where each page has its own row because:

- Enables better distribution across regions (more granular splits)
- Prevents oversized rows for popular domains with many pages
- Improves parallelism for scans and data processing
- Provides better update performance for individual pages

### Trade-offs
- Requires handling salt prefixes for scans
- More complex row key construction
- Slightly more complex read patterns for domain-wide scans

## 6. Salt Length Optimization

### Problem Addressed
Salt length affects both write distribution and read efficiency.

### Decision
We chose a 2-character hexadecimal salt (256 possible values) as an optimal balance:

- Sufficient distribution to prevent hotspotting on most clusters
- Limited enough that domain scans require only 256 parallel operations maximum
- Provides reasonable pre-split region count for medium-sized clusters
- Aligns with common HBase best practices for salt prefix length

## 7. Pre-defined Salt Distribution

### Problem Addressed
Random salt distribution can lead to uneven region sizes.

### Solution
We use a pre-defined set of 16 evenly distributed salt prefixes for region pre-splitting:
`'00', '10', '20', '30', '40', '50', '60', '70', '80', '90', 'a0', 'b0', 'c0', 'd0', 'e0', 'f0'`

This ensures:
- Even distribution of regions from the beginning
- Predictable region boundaries for operations planning
- Elimination of performance issues from dynamic region splitting during initial load

## Summary

Our row key design:
1. Prevents hotspotting through strategic salting
2. Groups related content through domain reversal
3. Preserves URL hierarchy by including paths
4. Optimizes for both read and write operations
5. Scales horizontally across the cluster
6. Enables efficient scanning and filtering operations
7. Balances distribution with scan efficiency through optimal salt length
8. Pre-splits regions for predictable performance

This row key design has proven effective in handling web data at scale while maintaining query efficiency for all our business requirements.
