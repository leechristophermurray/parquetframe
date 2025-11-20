/// Advanced geometric operations for Phase 2.
///
/// Provides buffer, intersection, union, and difference operations.

use crate::{Geometry, GeoError, Result};
use geo::{
    Buffer, BooleanOps, LineString as GeoLineString, Point as GeoPoint, Polygon as GeoPolygon,
};

/// Create a buffer around a geometry.
///
/// Returns a polygon representing all points within the specified distance.
pub fn buffer(geom: &Geometry, distance: f64) -> Result<Geometry> {
    match geom {
        Geometry::Point(p) => {
            // Simple circular buffer around point
            let buffered = p.buffer(distance);
            Ok(Geometry::Polygon(buffered))
        }
        Geometry::LineString(ls) => {
            let buffered = ls.buffer(distance);
            Ok(Geometry::Polygon(buffered))
        }
        Geometry::Polygon(poly) => {
            let buffered = poly.buffer(distance);
            Ok(Geometry::Polygon(buffered))
        }
        _ => Err(GeoError::GeometryError(
            "Buffer not yet implemented for this geometry type".to_string(),
        )),
    }
}

/// Calculate the intersection of two geometries.
pub fn intersection(geom1: &Geometry, geom2: &Geometry) -> Result<Option<Geometry>> {
    match (geom1, geom2) {
        (Geometry::Polygon(p1), Geometry::Polygon(p2)) => {
            let result = p1.intersection(p2);
            match result {
                geo::Geometry::Polygon(poly) if !poly.exterior().0.is_empty() => {
                    Ok(Some(Geometry::Polygon(poly)))
                }
                geo::Geometry::MultiPolygon(mp) if !mp.0.is_empty() => {
                    // For now, just return first polygon
                    if let Some(first) = mp.0.first() {
                        Ok(Some(Geometry::Polygon(first.clone())))
                    } else {
                        Ok(None)
                    }
                }
                _ => Ok(None),
            }
        }
        _ => Err(GeoError::GeometryError(
            "Intersection only supports Polygon geometries currently".to_string(),
        )),
    }
}

/// Calculate the union of two geometries.
pub fn union(geom1: &Geometry, geom2: &Geometry) -> Result<Geometry> {
    match (geom1, geom2) {
        (Geometry::Polygon(p1), Geometry::Polygon(p2)) => {
            let result = p1.union(p2);
            match result {
                geo::Geometry::Polygon(poly) => Ok(Geometry::Polygon(poly)),
                geo::Geometry::MultiPolygon(mp) => {
                    // For now, return as multi-polygon
                    Ok(Geometry::MultiPolygon(mp.0))
                }
                _ => Err(GeoError::GeometryError("Unexpected union result".to_string())),
            }
        }
        _ => Err(GeoError::GeometryError(
            "Union only supports Polygon geometries currently".to_string(),
        )),
    }
}

/// Calculate the difference of two geometries (geom1 - geom2).
pub fn difference(geom1: &Geometry, geom2: &Geometry) -> Result<Option<Geometry>> {
    match (geom1, geom2) {
        (Geometry::Polygon(p1), Geometry::Polygon(p2)) => {
            let result = p1.difference(p2);
            match result {
                geo::Geometry::Polygon(poly) if !poly.exterior().0.is_empty() => {
                    Ok(Some(Geometry::Polygon(poly)))
                }
                geo::Geometry::MultiPolygon(mp) if !mp.0.is_empty() => {
                    // Return first polygon
                    if let Some(first) = mp.0.first() {
                        Ok(Some(Geometry::Polygon(first.clone())))
                    } else {
                        Ok(None)
                    }
                }
                _ => Ok(None),
            }
        }
        _ => Err(GeoError::GeometryError(
            "Difference only supports Polygon geometries currently".to_string(),
        )),
    }
}

/// Check if two geometries are disjoint (do not intersect).
pub fn disjoint(geom1: &Geometry, geom2: &Geometry) -> Result<bool> {
    use geo::Intersects;

    match (geom1, geom2) {
        (Geometry::Polygon(p1), Geometry::Polygon(p2)) => Ok(!p1.intersects(p2)),
        (Geometry::Point(pt), Geometry::Polygon(poly)) => Ok(!poly.contains(pt)),
        (Geometry::Polygon(poly), Geometry::Point(pt)) => Ok(!poly.contains(pt)),
        _ => Err(GeoError::GeometryError(
            "Disjoint not implemented for these geometry types".to_string(),
        )),
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use geo::{point, polygon};

    #[test]
    fn test_buffer_point() {
        let pt = Geometry::Point(point!(x: 0.0, y: 0.0));
        let buffered = buffer(&pt, 1.0).unwrap();

        // Should return a polygon
        assert_eq!(buffered.geometry_type(), "Polygon");
    }

    #[test]
    fn test_intersection() {
        // Two overlapping squares
        let poly1 = Geometry::Polygon(polygon![
            (x: 0.0, y: 0.0),
            (x: 2.0, y: 0.0),
            (x: 2.0, y: 2.0),
            (x: 0.0, y: 2.0),
            (x: 0.0, y: 0.0),
        ]);

        let poly2 = Geometry::Polygon(polygon![
            (x: 1.0, y: 1.0),
            (x: 3.0, y: 1.0),
            (x: 3.0, y: 3.0),
            (x: 1.0, y: 3.0),
            (x: 1.0, y: 1.0),
        ]);

        let result = intersection(&poly1, &poly2).unwrap();
        assert!(result.is_some());
    }

    #[test]
    fn test_union() {
        let poly1 = Geometry::Polygon(polygon![
            (x: 0.0, y: 0.0),
            (x: 1.0, y: 0.0),
            (x: 1.0, y: 1.0),
            (x: 0.0, y: 1.0),
            (x: 0.0, y: 0.0),
        ]);

        let poly2 = Geometry::Polygon(polygon![
            (x: 0.5, y: 0.5),
            (x: 1.5, y: 0.5),
            (x: 1.5, y: 1.5),
            (x: 0.5, y: 1.5),
            (x: 0.5, y: 0.5),
        ]);

        let result = union(&poly1, &poly2).unwrap();
        // Union should succeed
        assert!(matches!(
            result,
            Geometry::Polygon(_) | Geometry::MultiPolygon(_)
        ));
    }

    #[test]
    fn test_disjoint() {
        let poly1 = Geometry::Polygon(polygon![
            (x: 0.0, y: 0.0),
            (x: 1.0, y: 0.0),
            (x: 1.0, y: 1.0),
            (x: 0.0, y: 1.0),
            (x: 0.0, y: 0.0),
        ]);

        let poly2 = Geometry::Polygon(polygon![
            (x: 5.0, y: 5.0),
            (x: 6.0, y: 5.0),
            (x: 6.0, y: 6.0),
            (x: 5.0, y: 6.0),
            (x: 5.0, y: 5.0),
        ]);

        assert!(disjoint(&poly1, &poly2).unwrap());
    }
}
