def deduplicate_records(records, unique_key="invoice_no"):
    """
    Remove duplicates from a list of dictionary records based on a unique key.
    If multiple records share the same key, keeps the last occurrence.
    """
    if not records:
        return []
        
    seen = {}
    for r in records:
        key = r.get(unique_key)
        if key is not None:
            seen[key] = r
            
    return list(seen.values())

def merge_partial_records(records, unique_key="invoice_no"):
    """
    Merges records sharing the same key by overwriting None values with known values.
    """
    merged_map = {}
    for r in records:
        key = r.get(unique_key)
        if not key:
            continue
            
        if key not in merged_map:
            merged_map[key] = r.copy()
        else:
            # Update missing values
            for k, v in r.items():
                if merged_map[key].get(k) is None and v is not None:
                    merged_map[key][k] = v
                    
    return list(merged_map.values())
