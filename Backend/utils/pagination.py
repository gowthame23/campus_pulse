def paginate(items: list, page: int = 1, limit: int = 20) -> dict:
    """Paginate a list of items and return standardized response format."""
    page = max(1, page)
    limit = max(1, min(limit, 100))  # Cap at 100

    total_items = len(items)
    total_pages = max(1, (total_items + limit - 1) // limit)

    start = (page - 1) * limit
    end = start + limit
    page_items = items[start:end]

    return {
        "items": page_items,
        "page": page,
        "limit": limit,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
        "has_previous": page > 1,
    }
