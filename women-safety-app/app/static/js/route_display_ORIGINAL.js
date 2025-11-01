function offsetRoute(route, index, totalRoutes) {
    if (!route || route.length < 2) return null;

    // Calculate base offset (increases with route index)
    const baseOffset = 0.0001 * (index + 1); // ~11 meters at equator

    // Calculate perpendicular offsets
    return route.map((point, pointIndex) => {
        // Fade offset near endpoints to maintain start/end positions
        const progress = pointIndex / (route.length - 1);
        const fadeOffset = baseOffset * Math.sin(progress * Math.PI);
        
        // Alternate offset direction based on route index
        const direction = index % 2 ? 1 : -1;
        
        return [
            point[0] + (fadeOffset * direction),
            point[1] + (fadeOffset * direction)
        ];
    });
}

function validateRoute(route, startPoint, endPoint) {
    if (!route || route.length < 2) return false;
    
    // Check if route connects start and end points
    const firstPoint = route[0];
    const lastPoint = route[route.length - 1];
    
    const startDist = haversineDistance(
        startPoint[0], startPoint[1],
        firstPoint[0], firstPoint[1]
    );
    
    const endDist = haversineDistance(
        endPoint[0], endPoint[1],
        lastPoint[0], lastPoint[1]
    );
    
    // Allow small deviation (100m) at endpoints
    return startDist <= 0.1 && endDist <= 0.1;
}

function haversineDistance(lat1, lon1, lat2, lon2) {
    const R = 6371; // Earth's radius in km
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = 
        Math.sin(dLat/2) * Math.sin(dLat/2) +
        Math.cos(lat1 * Math.PI / 180) * Math.cos(lat2 * Math.PI / 180) * 
        Math.sin(dLon/2) * Math.sin(dLon/2);
    return 2 * R * Math.asin(Math.sqrt(a));
}