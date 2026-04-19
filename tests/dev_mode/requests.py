"""
Simulated SQS help requests for dev-mode.
Format should match the expected body from the formal intake system.
"""

REQUEST_ARR = [
    {
        "id": "sim-req-001",
        "title": "Severe drought in Anantapur district",
        "description": "Groundwater level has depleted. Farmers need immediate water transport and seeds for resilient crops.",
        "location": "Anantapur, Andhra Pradesh",
        "category": "drought",
        "priority": "high",
        "contact": "Local Panchayat Office"
    },
    {
        "id": "sim-req-002",
        "title": "Flash floods in Assam",
        "description": "Brahmaputra overflowed. Villages submerged. Need rescue boats and food packets.",
        "location": "Majuli, Assam",
        "category": "floods",
        "priority": "critical",
        "contact": "State Disaster Response"
    },
    {
        "id": "sim-req-003",
        "title": "Health camp request for rural Bihar",
        "description": "Seasonal fever outbreak. No primary health center within 50km. Need mobile medical unit.",
        "location": "Jamui, Bihar",
        "category": "healthcare",
        "priority": "medium",
        "contact": "Village Volunteers"
    }
]