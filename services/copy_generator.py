"""
services/copy_generator.py — Generates premium marketing copy
using the Google Gemini API with verified amenity data.
"""

import os
import google.generativeai as genai

# Prompt template sent to Gemini.
# Placeholders: {address}, {amenity_summary}

PROMPT_TEMPLATE = """\
You are a professional real-estate copywriter producing content for
LinkedIn posts and property-listing platforms.

=== PROPERTY ===
Address: {address}

=== BUYER PROFILE ===
{buyer_profile}

=== VERIFIED NEARBY AMENITIES ===
The following amenity data has been verified through the Google Places
API.  Every name, distance, and rating below is real and accurate.

{amenity_summary}

=== WRITING INSTRUCTIONS ===

1. LENGTH: Write exactly ONE paragraph between 120 and 180 words.
   Do NOT go below 120 or above 180.

2. CONTENT RULES
   - Reference specific amenities BY NAME
   - Focus on LOCATION CONVENIENCE — how the property's surroundings
     benefit the resident's daily life based intensely on their Buyer Profile (commute, dining, recreation,
     education, leisure). 
   - Never use raw numbers for distance (e.g. "380m", "1.2km").
     Instead, use natural phrases — "a short walk", "steps away",
     "nearby", "within easy reach"
   - Do NOT repeat the same amenity or the same fact twice.
   - Do NOT fabricate, invent, or guess any amenity that is not listed
     above.  Use ONLY the data provided.

3. WRITING APPROACH
  - Write in the voice of an experienced real-estate agent speaking to a discerning buyer.
  - Assume the reader understands Singapore neighbourhoods; avoid over-explaining.
  - Prioritise clarity and natural flow over coverage. It is acceptable to omit some amenities if doing so improves readability.
  - Group amenities organically where appropriate, but do not force a “daily routine” structure.
  - Avoid category announcements (e.g., “For dining…”, “For leisure…”).
  - Avoid symmetrical sentence patterns or repeated distance structures.
  - You MUST weave the buyer's priorities and life stage into the flow of the sentences smoothly.

4. TONE
  - Calm, assured, and locally informed.
  - Concrete rather than abstract.
  - Avoid generic promotional phrases such as:
    “offers exceptional convenience”
    “seamlessly integrates”
    “positions residents”
    “vibrant community”
    “well-serviced”
  - No exaggeration, no hype, no filler language.

5. FORMAT
   - Return ONLY the paragraph text.
   - No headings, bullet points, labels, or markdown formatting.
   - No preamble such as "Here is your copy:".

Begin writing now.
"""

# Friendly labels for amenity categories
CATEGORY_LABELS = {
    "mrt_stations": "MRT / Transit Stations",
    "shopping_malls": "Shopping Malls",
    "schools": "Schools",
    "restaurants": "Restaurants",
    "parks": "Parks",
}


def generate_marketing_copy(address, amenities, buyer_profile_data=None):
    """
    Generate a 120-180 word marketing paragraph for a property.

    Args:
        address (str):    Formatted property address.
        amenities (dict): Ranked amenities from filter_and_rank().
        buyer_profile_data (dict): Optional structured metadata about the buyer.

    Returns:
        str: The generated marketing copy.
    """
    genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

    amenity_summary = _build_amenity_summary(amenities)
    
    buyer_profile_str = "General Audience (No specific profile provided)"
    if buyer_profile_data:
        import json
        buyer_profile_str = json.dumps(buyer_profile_data, indent=2)

    prompt = PROMPT_TEMPLATE.format(
        address=address, 
        amenity_summary=amenity_summary,
        buyer_profile=buyer_profile_str
    )

    model = genai.GenerativeModel("gemini-2.5-flash")
    response = model.generate_content(prompt)

    return response.text.strip()


def _build_amenity_summary(amenities):
    """Convert ranked amenities into a readable text block for the prompt."""
    lines = []

    for category, places in amenities.items():
        label = CATEGORY_LABELS.get(category, category)
        lines.append(f"\n{label}:")

        if not places:
            lines.append("  (none found within criteria)")
            continue

        for p in places:
            lines.append(
                f"  - {p['name']}  |  {p['distance_meters']}m away"
            )

    return "\n".join(lines)
