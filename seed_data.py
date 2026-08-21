from data.google_sheets import add_row


fans = [

    {
        "fan_id": "FAN-0001",
        "name": "Thabo Mokoena",
        "email": "thabo@example.com",
        "phone": "0821111111",
        "location": "Soweto",
        "age_group": "20-24",
        "favorite_song": "WHOLENESS",
        "favorite_artist": "Artist",
        "source": "TikTok",
        "consent": "Yes",
        "fan_status": "Active",
        "engagement_score": 82,
        "total_spend": 450,
        "last_interaction": "2026-08-15",
        "created_at": "2026-07-01",
    },

    {
        "fan_id": "FAN-0002",
        "name": "Lerato Nkosi",
        "email": "lerato@example.com",
        "phone": "0832222222",
        "location": "Pretoria",
        "age_group": "25-29",
        "favorite_song": "WHOLENESS",
        "favorite_artist": "Artist",
        "source": "Instagram",
        "consent": "Yes",
        "fan_status": "VIP",
        "engagement_score": 95,
        "total_spend": 850,
        "last_interaction": "2026-08-17",
        "created_at": "2026-06-15",
    },

    {
        "fan_id": "FAN-0003",
        "name": "Kabelo Dlamini",
        "email": "kabelo@example.com",
        "phone": "0843333333",
        "location": "Johannesburg",
        "age_group": "20-24",
        "favorite_song": "Song B",
        "favorite_artist": "Artist",
        "source": "Concert",
        "consent": "Yes",
        "fan_status": "Active",
        "engagement_score": 71,
        "total_spend": 300,
        "last_interaction": "2026-08-10",
        "created_at": "2026-07-20",
    },

    {
        "fan_id": "FAN-0004",
        "name": "Nomsa Khumalo",
        "email": "nomsa@example.com",
        "phone": "",
        "location": "Flaka",
        "age_group": "25-29",
        "favorite_song": "WHOLENESS",
        "favorite_artist": "Artist",
        "source": "WhatsApp",
        "consent": "Yes",
        "fan_status": "VIP",
        "engagement_score": 91,
        "total_spend": 1200,
        "last_interaction": "2026-08-16",
        "created_at": "2026-05-12",
    },

    {
        "fan_id": "FAN-0005",
        "name": "Sipho Ndlovu",
        "email": "",
        "phone": "0854444444",
        "location": "Pretoria",
        "age_group": "20-24",
        "favorite_song": "Song C",
        "favorite_artist": "Artist",
        "source": "TikTok",
        "consent": "No",
        "fan_status": "New",
        "engagement_score": 22,
        "total_spend": 0,
        "last_interaction": "",
        "created_at": "2026-08-18",
    },

]


print("Adding test fans...")

for fan in fans:

    try:

        add_row(
            "Fans",
            fan,
        )

        print(
            f"Added: {fan['name']}"
        )

    except Exception as e:

        print(
            f"Failed: {fan['name']} -> {e}"
        )


print("Done!")