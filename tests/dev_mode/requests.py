"""
Simulated SQS help requests for dev-mode.
Format strictly matches the RequestRecord schema from app/submodules/matching/schemas.py.
"""

# Valid UUIDs for simulation
REQ_ID_1 = "33bdcffe-d60c-4fb3-b01a-0ae0112e9990"
REQ_ID_2 = "33bdcffe-d60c-4fb3-b01a-0ae0112e9991"
REQ_ID_3 = "33bdcffe-d60c-4fb3-b01a-0ae0112e9992"
ISSUER_ID = "44bdcffe-d60c-4fb3-b01a-0ae0112e9999"

REQUEST_ARR = [
    {
        "id": REQ_ID_1,
        "title": "Severe drought in Anantapur district",
        "description": "Groundwater level has depleted. Farmers need immediate water transport and seeds for resilient crops.",
        "location_type": "location",
        "location_text": "Anantapur, Andhra Pradesh",
        "latitude": "14.6819",
        "longitude": "77.6006",
        "issuer_type": "organization",
        "issuer_id": ISSUER_ID,
        "status": "open",
        "progress_percent": 10,
        "agent_research_status": "pending",
        "created_at": "2026-04-20T10:00:00Z",
        "updated_at": "2026-04-20T10:00:00Z"
    },
    {
        "id": REQ_ID_2,
        "title": "Flash floods in Assam",
        "description": "Brahmaputra overflowed. Villages submerged. Need rescue boats and food packets.",
        "location_type": "location",
        "location_text": "Majuli, Assam",
        "latitude": "26.9602",
        "longitude": "94.2259",
        "issuer_type": "organization",
        "issuer_id": ISSUER_ID,
        "status": "open",
        "progress_percent": 0,
        "agent_research_status": "pending",
        "created_at": "2026-04-20T11:00:00Z",
        "updated_at": "2026-04-20T11:00:00Z"
    },
    {
        "id": REQ_ID_3,
        "title": "Health camp request for rural Bihar",
        "description": "Seasonal fever outbreak. No primary health center within 50km. Need mobile medical unit.",
        "location_type": "location",
        "location_text": "Jamui, Bihar",
        "latitude": "24.9202",
        "longitude": "86.2259",
        "issuer_type": "volunteer",
        "issuer_id": ISSUER_ID,
        "status": "open",
        "progress_percent": 5,
        "agent_research_status": "pending",
        "created_at": "2026-04-20T12:00:00Z",
        "updated_at": "2026-04-20T12:00:00Z"
    }
]