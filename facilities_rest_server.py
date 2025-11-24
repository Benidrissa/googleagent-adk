#!/usr/bin/env python3
"""
Mock REST API Server for Health Facilities

This FastAPI server provides a mock implementation of the Health Facilities API
for testing and development purposes. It returns simulated facility data for
major West African cities.
"""

import math
from typing import List, Optional
from fastapi import FastAPI, Query, HTTPException
from pydantic import BaseModel, Field
import uvicorn

# Initialize FastAPI app
app = FastAPI(
    title="Health Facilities API",
    description="API for finding nearby health facilities",
    version="1.0.0"
)


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class Coordinates(BaseModel):
    latitude: float
    longitude: float


class Facility(BaseModel):
    id: str
    name: str
    type: str
    address: str
    coordinates: Coordinates
    distance_meters: Optional[int] = None
    rating: float
    services: List[str]
    emergency_available: bool
    open_24_7: bool
    phone: str


class FacilityDetailed(Facility):
    operating_hours: dict
    departments: List[str]
    staff_count: int
    bed_capacity: int
    accepts_insurance: bool
    parking_available: bool
    wheelchair_accessible: bool


class SearchLocation(BaseModel):
    latitude: float
    longitude: float
    radius_meters: int


class FacilitiesResponse(BaseModel):
    status: str = "success"
    count: int
    search_location: SearchLocation
    facilities: List[Facility]


class FacilityDetailResponse(BaseModel):
    status: str = "success"
    facility: FacilityDetailed


class ErrorResponse(BaseModel):
    status: str = "error"
    error_code: str
    message: str


# ============================================================================
# MOCK DATABASE
# ============================================================================

MOCK_FACILITIES = [
    # Lagos, Nigeria
    {
        "id": "fac_lag_001",
        "name": "Lagos University Teaching Hospital",
        "type": "hospital",
        "address": "Idi-Araba, Lagos, Nigeria",
        "coordinates": {"latitude": 6.5050, "longitude": 3.3700},
        "rating": 4.2,
        "services": ["emergency", "maternity", "general", "surgery"],
        "emergency_available": True,
        "open_24_7": True,
        "phone": "+234-1-234-5678",
        "operating_hours": {
            "monday": "24 hours", "tuesday": "24 hours", "wednesday": "24 hours",
            "thursday": "24 hours", "friday": "24 hours", "saturday": "24 hours", "sunday": "24 hours"
        },
        "departments": ["Obstetrics", "Gynecology", "Pediatrics", "Emergency", "Surgery"],
        "staff_count": 250,
        "bed_capacity": 300,
        "accepts_insurance": True,
        "parking_available": True,
        "wheelchair_accessible": True
    },
    {
        "id": "fac_lag_002",
        "name": "Lagos Island Maternity Hospital",
        "type": "maternity",
        "address": "Broad Street, Lagos Island, Nigeria",
        "coordinates": {"latitude": 6.4500, "longitude": 3.3900},
        "rating": 4.0,
        "services": ["maternity", "prenatal_care", "postnatal_care"],
        "emergency_available": True,
        "open_24_7": True,
        "phone": "+234-1-234-5679",
        "operating_hours": {
            "monday": "24 hours", "tuesday": "24 hours", "wednesday": "24 hours",
            "thursday": "24 hours", "friday": "24 hours", "saturday": "24 hours", "sunday": "24 hours"
        },
        "departments": ["Maternity", "Neonatal Care", "Prenatal Clinic"],
        "staff_count": 80,
        "bed_capacity": 100,
        "accepts_insurance": True,
        "parking_available": False,
        "wheelchair_accessible": True
    },
    {
        "id": "fac_lag_003",
        "name": "Mainland Hospital Yaba",
        "type": "hospital",
        "address": "Yaba, Lagos, Nigeria",
        "coordinates": {"latitude": 6.5100, "longitude": 3.3700},
        "rating": 3.8,
        "services": ["emergency", "general", "outpatient"],
        "emergency_available": True,
        "open_24_7": False,
        "phone": "+234-1-234-5680",
        "operating_hours": {
            "monday": "7:00 AM - 9:00 PM", "tuesday": "7:00 AM - 9:00 PM", "wednesday": "7:00 AM - 9:00 PM",
            "thursday": "7:00 AM - 9:00 PM", "friday": "7:00 AM - 9:00 PM", "saturday": "8:00 AM - 6:00 PM", "sunday": "Closed"
        },
        "departments": ["General Medicine", "Emergency", "Outpatient"],
        "staff_count": 60,
        "bed_capacity": 80,
        "accepts_insurance": True,
        "parking_available": True,
        "wheelchair_accessible": False
    },
    
    # Bamako, Mali
    {
        "id": "fac_bko_001",
        "name": "Hospital Gabriel Touré",
        "type": "hospital",
        "address": "Rue 40, Commune III, Bamako, Mali",
        "coordinates": {"latitude": 12.6392, "longitude": -8.0029},
        "rating": 4.1,
        "services": ["emergency", "maternity", "general", "pediatrics"],
        "emergency_available": True,
        "open_24_7": True,
        "phone": "+223-20-22-27-12",
        "operating_hours": {
            "monday": "24 hours", "tuesday": "24 hours", "wednesday": "24 hours",
            "thursday": "24 hours", "friday": "24 hours", "saturday": "24 hours", "sunday": "24 hours"
        },
        "departments": ["Emergency", "Maternity", "Pediatrics", "Surgery"],
        "staff_count": 180,
        "bed_capacity": 250,
        "accepts_insurance": True,
        "parking_available": True,
        "wheelchair_accessible": True
    },
    {
        "id": "fac_bko_002",
        "name": "Point G Hospital",
        "type": "hospital",
        "address": "Colline du Point G, Bamako, Mali",
        "coordinates": {"latitude": 12.6600, "longitude": -7.9800},
        "rating": 4.3,
        "services": ["emergency", "general", "surgery", "specialized"],
        "emergency_available": True,
        "open_24_7": True,
        "phone": "+223-20-22-50-02",
        "operating_hours": {
            "monday": "24 hours", "tuesday": "24 hours", "wednesday": "24 hours",
            "thursday": "24 hours", "friday": "24 hours", "saturday": "24 hours", "sunday": "24 hours"
        },
        "departments": ["Emergency", "Surgery", "Internal Medicine", "Cardiology"],
        "staff_count": 300,
        "bed_capacity": 400,
        "accepts_insurance": True,
        "parking_available": True,
        "wheelchair_accessible": True
    },
    {
        "id": "fac_bko_003",
        "name": "Maternité Communautaire du Mali",
        "type": "maternity",
        "address": "Avenue Moussa Tavele, Commune IV, Bamako, Mali",
        "coordinates": {"latitude": 12.6200, "longitude": -8.0100},
        "rating": 3.9,
        "services": ["maternity", "prenatal_care", "family_planning"],
        "emergency_available": True,
        "open_24_7": True,
        "phone": "+223-20-22-30-45",
        "operating_hours": {
            "monday": "24 hours", "tuesday": "24 hours", "wednesday": "24 hours",
            "thursday": "24 hours", "friday": "24 hours", "saturday": "24 hours", "sunday": "24 hours"
        },
        "departments": ["Maternity", "Prenatal Clinic", "Family Planning"],
        "staff_count": 50,
        "bed_capacity": 60,
        "accepts_insurance": False,
        "parking_available": False,
        "wheelchair_accessible": False
    },
    
    # Accra, Ghana
    {
        "id": "fac_acc_001",
        "name": "Ridge Hospital",
        "type": "hospital",
        "address": "Castle Road, Ridge, Accra, Ghana",
        "coordinates": {"latitude": 5.5700, "longitude": -0.2000},
        "rating": 4.2,
        "services": ["emergency", "general", "outpatient"],
        "emergency_available": True,
        "open_24_7": True,
        "phone": "+233-30-222-9667",
        "operating_hours": {
            "monday": "24 hours", "tuesday": "24 hours", "wednesday": "24 hours",
            "thursday": "24 hours", "friday": "24 hours", "saturday": "24 hours", "sunday": "24 hours"
        },
        "departments": ["Emergency", "General Medicine", "Outpatient"],
        "staff_count": 120,
        "bed_capacity": 150,
        "accepts_insurance": True,
        "parking_available": True,
        "wheelchair_accessible": True
    },
    {
        "id": "fac_acc_002",
        "name": "Korle Bu Teaching Hospital",
        "type": "hospital",
        "address": "Guggisberg Avenue, Korle Bu, Accra, Ghana",
        "coordinates": {"latitude": 5.5400, "longitude": -0.2200},
        "rating": 4.4,
        "services": ["emergency", "maternity", "surgery", "specialized"],
        "emergency_available": True,
        "open_24_7": True,
        "phone": "+233-30-266-6841",
        "operating_hours": {
            "monday": "24 hours", "tuesday": "24 hours", "wednesday": "24 hours",
            "thursday": "24 hours", "friday": "24 hours", "saturday": "24 hours", "sunday": "24 hours"
        },
        "departments": ["Emergency", "Obstetrics", "Surgery", "Pediatrics", "Cardiology"],
        "staff_count": 400,
        "bed_capacity": 500,
        "accepts_insurance": True,
        "parking_available": True,
        "wheelchair_accessible": True
    },
    {
        "id": "fac_acc_003",
        "name": "Princess Marie Louise Hospital",
        "type": "maternity",
        "address": "Kinkole, Accra, Ghana",
        "coordinates": {"latitude": 5.5600, "longitude": -0.1900},
        "rating": 4.0,
        "services": ["maternity", "prenatal_care", "pediatrics"],
        "emergency_available": True,
        "open_24_7": True,
        "phone": "+233-30-266-3285",
        "operating_hours": {
            "monday": "24 hours", "tuesday": "24 hours", "wednesday": "24 hours",
            "thursday": "24 hours", "friday": "24 hours", "saturday": "24 hours", "sunday": "24 hours"
        },
        "departments": ["Maternity", "Pediatrics", "Neonatal Care"],
        "staff_count": 90,
        "bed_capacity": 120,
        "accepts_insurance": True,
        "parking_available": True,
        "wheelchair_accessible": True
    }
]


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> int:
    """
    Calculate distance between two coordinates using Haversine formula.
    Returns distance in meters.
    """
    # Earth radius in meters
    R = 6371000
    
    # Convert to radians
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    # Haversine formula
    a = math.sin(delta_phi/2) ** 2 + \
        math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    distance = R * c
    return int(distance)


def filter_facilities_by_location(
    facilities: List[dict],
    lat: float,
    lon: float,
    radius: int
) -> List[dict]:
    """Filter facilities by distance from location."""
    results = []
    
    for facility in facilities:
        fac_lat = facility["coordinates"]["latitude"]
        fac_lon = facility["coordinates"]["longitude"]
        distance = calculate_distance(lat, lon, fac_lat, fac_lon)
        
        if distance <= radius:
            facility_copy = facility.copy()
            facility_copy["distance_meters"] = distance
            results.append(facility_copy)
    
    # Sort by distance
    results.sort(key=lambda x: x["distance_meters"])
    return results


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "name": "Health Facilities API",
        "version": "1.0.0",
        "description": "Mock API for finding nearby health facilities",
        "endpoints": {
            "facilities": "/facilities?lat={lat}&long={long}&radius={radius}&type={type}",
            "facility_detail": "/facilities/{facility_id}"
        }
    }


@app.get("/facilities", response_model=FacilitiesResponse)
async def get_facilities(
    lat: float = Query(..., description="Latitude of search location"),
    long: float = Query(..., description="Longitude of search location", alias="long"),
    radius: int = Query(5000, ge=100, le=50000, description="Search radius in meters"),
    type: str = Query("all", regex="^(hospital|clinic|maternity|emergency|all)$", description="Facility type filter")
):
    """
    Find nearby health facilities.
    
    Args:
        lat: Latitude of search location
        long: Longitude of search location
        radius: Search radius in meters (default: 5000)
        type: Filter by facility type (default: all)
    
    Returns:
        List of facilities within the specified radius
    """
    # Validate coordinates
    if not (-90 <= lat <= 90):
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "error_code": "INVALID_LATITUDE",
                "message": f"Latitude must be between -90 and 90, got {lat}"
            }
        )
    
    if not (-180 <= long <= 180):
        raise HTTPException(
            status_code=400,
            detail={
                "status": "error",
                "error_code": "INVALID_LONGITUDE",
                "message": f"Longitude must be between -180 and 180, got {long}"
            }
        )
    
    # Filter facilities by location
    nearby_facilities = filter_facilities_by_location(
        MOCK_FACILITIES, lat, long, radius
    )
    
    # Filter by type if not "all"
    if type != "all":
        nearby_facilities = [
            f for f in nearby_facilities 
            if f["type"] == type or (type == "emergency" and f["emergency_available"])
        ]
    
    # Convert to response format (exclude detailed fields)
    facilities_list = [
        {
            "id": f["id"],
            "name": f["name"],
            "type": f["type"],
            "address": f["address"],
            "coordinates": f["coordinates"],
            "distance_meters": f["distance_meters"],
            "rating": f["rating"],
            "services": f["services"],
            "emergency_available": f["emergency_available"],
            "open_24_7": f["open_24_7"],
            "phone": f["phone"]
        }
        for f in nearby_facilities
    ]
    
    return FacilitiesResponse(
        status="success",
        count=len(facilities_list),
        search_location=SearchLocation(
            latitude=lat,
            longitude=long,
            radius_meters=radius
        ),
        facilities=facilities_list
    )


@app.get("/facilities/{facility_id}", response_model=FacilityDetailResponse)
async def get_facility_detail(facility_id: str):
    """
    Get detailed information about a specific facility.
    
    Args:
        facility_id: Unique facility identifier
    
    Returns:
        Detailed facility information
    """
    # Find facility by ID
    facility = next((f for f in MOCK_FACILITIES if f["id"] == facility_id), None)
    
    if not facility:
        raise HTTPException(
            status_code=404,
            detail={
                "status": "error",
                "error_code": "NOT_FOUND",
                "message": f"Facility with ID '{facility_id}' not found"
            }
        )
    
    return FacilityDetailResponse(
        status="success",
        facility=FacilityDetailed(**facility)
    )


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print("Starting Health Facilities API Mock Server...")
    print("API Documentation: http://localhost:8080/docs")
    print("OpenAPI Schema: http://localhost:8080/openapi.json")
    uvicorn.run(app, host="0.0.0.0", port=8080, log_level="info")
