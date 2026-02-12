/**
 * Unwraps paginated/wrapped API responses into plain arrays.
 * Handles Spring Page, custom wrappers, and direct arrays.
 *
 * @param {any} payload - The API response data
 * @param {string[]} keys - Potential keys where the array might be hidden
 * @returns {Array} The extracted array or an empty array
 */
export const unwrapArray = (payload, keys = ['data', 'content', 'events', 'items', 'results', 'streams']) => {
    // 1. If it's already an array, return it
    if (Array.isArray(payload)) return payload;

    // 2. If it's null/undefined or not an object, return empty array
    if (!payload || typeof payload !== 'object') return [];

    // 3. Check common wrapper keys
    for (const key of keys) {
        if (Array.isArray(payload[key])) {
            return payload[key];
        }
    }

    // 4. Fallback: if no known key works, return empty
    return [];
};

/**
 * Safe getter for nested properties to avoid "cannot read property of undefined"
 */
export const safeGet = (obj, path, defaultValue = null) => {
    return path.split('.').reduce((acc, part) => acc?.[part], obj) ?? defaultValue;
};
