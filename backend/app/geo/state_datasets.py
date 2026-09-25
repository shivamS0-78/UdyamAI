"""Multi-state canonical datasets and state intelligence provider for UdyamAI.

Supports 20 major Indian states with canonical datasets of locations, APMC mandis,
priority sectors, and sample villages with explicit provenance flags.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

# Canonical state profile datasets for 20 major Indian states
STATE_DATASETS: dict[str, dict[str, Any]] = {
    "MH": {
        "state_name": "Maharashtra",
        "state_code": "MH",
        "districts": [
            "Ahmednagar",
            "Pune",
            "Nashik",
            "Solapur",
            "Kolhapur",
            "Aurangabad",
            "Nagpur",
        ],
        "sample_villages": [
            {
                "name": "Ralegan Siddhi",
                "district": "Ahmednagar",
                "population": 2350,
                "is_synthetic": False,
            },
            {
                "name": "Hiware Bazar",
                "district": "Ahmednagar",
                "population": 1400,
                "is_synthetic": False,
            },
            {"name": "Narayangaon", "district": "Pune", "population": 18200, "is_synthetic": False},
            {
                "name": "Pimpalgaon Baswant",
                "district": "Nashik",
                "population": 22000,
                "is_synthetic": False,
            },
        ],
        "key_mandis": [
            {
                "name": "Lasalgaon Onion Mandi",
                "district": "Nashik",
                "commodities": ["Onion", "Grapes", "Pomegranate"],
            },
            {
                "name": "Ahmednagar APMC",
                "district": "Ahmednagar",
                "commodities": ["Onion", "Millets", "Soybean"],
            },
            {
                "name": "Pune Gultekdi APMC",
                "district": "Pune",
                "commodities": ["Vegetables", "Fruits", "Grains"],
            },
            {
                "name": "Kolhapur Jaggery Market",
                "district": "Kolhapur",
                "commodities": ["Jaggery", "Sugarcane", "Spices"],
            },
        ],
        "priority_sectors": [
            "Food Processing",
            "Dairy",
            "Textiles",
            "Bio-Fertilizer",
            "Grape & Wine Processing",
            "Jaggery Processing",
        ],
    },
    "KA": {
        "state_name": "Karnataka",
        "state_code": "KA",
        "districts": [
            "Mandya",
            "Belagavi",
            "Tumakuru",
            "Dharwad",
            "Mysuru",
            "Hassan",
            "Shivamogga",
        ],
        "sample_villages": [
            {"name": "Shivalli", "district": "Mandya", "population": 3100, "is_synthetic": False},
            {"name": "Hukkeri", "district": "Belagavi", "population": 14500, "is_synthetic": False},
            {"name": "Gubbi", "district": "Tumakuru", "population": 18000, "is_synthetic": False},
            {"name": "Bannur", "district": "Mysuru", "population": 12500, "is_synthetic": False},
        ],
        "key_mandis": [
            {
                "name": "Mandya Jaggery Mandi",
                "district": "Mandya",
                "commodities": ["Sugarcane", "Jaggery", "Paddy"],
            },
            {
                "name": "Belagavi APMC",
                "district": "Belagavi",
                "commodities": ["Vegetables", "Maize", "Groundnut"],
            },
            {
                "name": "Byadgi Chilli Market",
                "district": "Dharwad",
                "commodities": ["Chilli", "Cotton", "Millets"],
            },
        ],
        "priority_sectors": [
            "Jaggery Processing",
            "Silk Weaving",
            "Spices",
            "Millets Value Addition",
            "Coffee Agro-processing",
        ],
    },
    "TN": {
        "state_name": "Tamil Nadu",
        "state_code": "TN",
        "districts": [
            "Erode",
            "Coimbatore",
            "Thanjavur",
            "Dindigul",
            "Salem",
            "Tiruppur",
            "Madurai",
        ],
        "sample_villages": [
            {
                "name": "Perundurai Rural",
                "district": "Erode",
                "population": 4200,
                "is_synthetic": False,
            },
            {
                "name": "Thiruvaiyaru",
                "district": "Thanjavur",
                "population": 16000,
                "is_synthetic": False,
            },
            {
                "name": "Oddanchatram Rural",
                "district": "Dindigul",
                "population": 8900,
                "is_synthetic": False,
            },
            {
                "name": "Pollachi Rural",
                "district": "Coimbatore",
                "population": 11200,
                "is_synthetic": False,
            },
        ],
        "key_mandis": [
            {
                "name": "Erode Turmeric Mandi",
                "district": "Erode",
                "commodities": ["Turmeric", "Tapioca", "Coconut"],
            },
            {
                "name": "Oddanchatram Vegetable Market",
                "district": "Dindigul",
                "commodities": ["Drumstick", "Tomato", "Chilli"],
            },
            {
                "name": "Pollachi Coconut Market",
                "district": "Coimbatore",
                "commodities": ["Coconut", "Coir", "Tender Coconut"],
            },
        ],
        "priority_sectors": [
            "Coir & Coconut Products",
            "Turmeric Processing",
            "Handloom & Textiles",
            "Poultry",
            "Tapioca Value Addition",
        ],
    },
    "UP": {
        "state_name": "Uttar Pradesh",
        "state_code": "UP",
        "districts": [
            "Varanasi",
            "Barabanki",
            "Gorakhpur",
            "Moradabad",
            "Kannauj",
            "Agra",
            "Prayagraj",
        ],
        "sample_villages": [
            {
                "name": "Rameshwar",
                "district": "Varanasi",
                "population": 3600,
                "is_synthetic": False,
            },
            {
                "name": "DewaShrif Rural",
                "district": "Barabanki",
                "population": 5200,
                "is_synthetic": False,
            },
            {
                "name": "Bansgaon",
                "district": "Gorakhpur",
                "population": 14200,
                "is_synthetic": False,
            },
            {"name": "Bilhaur", "district": "Kannauj", "population": 10500, "is_synthetic": False},
        ],
        "key_mandis": [
            {
                "name": "Varanasi Rajatalab APMC",
                "district": "Varanasi",
                "commodities": ["Vegetables", "Mango", "Rice"],
            },
            {
                "name": "Barabanki Mandi",
                "district": "Barabanki",
                "commodities": ["Mentha", "Potato", "Wheat"],
            },
            {
                "name": "Kannauj Perfume & Agro Mandi",
                "district": "Kannauj",
                "commodities": ["Attar/Essential Oils", "Rose", "Potato"],
            },
        ],
        "priority_sectors": [
            "Mentha Oil Distillation",
            "Food Processing",
            "Brassware & Crafts (ODOP)",
            "Dairy",
            "Essential Oils & Fragrances",
        ],
    },
    "GJ": {
        "state_name": "Gujarat",
        "state_code": "GJ",
        "districts": ["Anand", "Rajkot", "Surat", "Mehsana", "Kutch", "Banaskantha", "Junagadh"],
        "sample_villages": [
            {"name": "Mogar", "district": "Anand", "population": 4800, "is_synthetic": False},
            {
                "name": "Gondal Rural",
                "district": "Rajkot",
                "population": 12000,
                "is_synthetic": False,
            },
            {
                "name": "Dhanera",
                "district": "Banaskantha",
                "population": 15000,
                "is_synthetic": False,
            },
        ],
        "key_mandis": [
            {
                "name": "Unjha Isabgol & Jeera Mandi",
                "district": "Mehsana",
                "commodities": ["Cumin", "Isabgol", "Fennel", "Mustard"],
            },
            {
                "name": "Gondal APMC",
                "district": "Rajkot",
                "commodities": ["Groundnut", "Chilli", "Cotton", "Garlic"],
            },
            {
                "name": "Anand Dairy & Agri Mandi",
                "district": "Anand",
                "commodities": ["Dairy Products", "Tobacco", "Banana"],
            },
        ],
        "priority_sectors": [
            "Dairy & Milk Processing",
            "Cumin & Spice Extraction",
            "Groundnut Oil",
            "Cotton Ginning & Textiles",
            "Ceramics",
        ],
    },
    "RJ": {
        "state_name": "Rajasthan",
        "state_code": "RJ",
        "districts": ["Jaipur", "Jodhpur", "Bikaner", "Nagaur", "Alwar", "Kota", "Pali"],
        "sample_villages": [
            {
                "name": "Sanganer Rural",
                "district": "Jaipur",
                "population": 6500,
                "is_synthetic": False,
            },
            {"name": "Nokha", "district": "Bikaner", "population": 13500, "is_synthetic": False},
            {
                "name": "Merta City Rural",
                "district": "Nagaur",
                "population": 8400,
                "is_synthetic": False,
            },
        ],
        "key_mandis": [
            {
                "name": "Merta Mandi",
                "district": "Nagaur",
                "commodities": ["Cumin", "Moong", "Isabgol", "Mustard"],
            },
            {
                "name": "Bikaner Wool & Cereal APMC",
                "district": "Bikaner",
                "commodities": ["Guar Gum", "Moth Beans", "Wool"],
            },
            {
                "name": "Kota Mandi",
                "district": "Kota",
                "commodities": ["Soybean", "Coriander", "Wheat"],
            },
        ],
        "priority_sectors": [
            "Handicrafts & Hand Block Print",
            "Spices (Coriander & Cumin)",
            "Guar Gum Processing",
            "Camel Milk & Dairy",
            "Solar Micro-enterprises",
        ],
    },
    "PB": {
        "state_name": "Punjab",
        "state_code": "PB",
        "districts": [
            "Ludhiana",
            "Amritsar",
            "Jalandhar",
            "Bathinda",
            "Hoshiarpur",
            "Patiala",
            "Sangrur",
        ],
        "sample_villages": [
            {"name": "Khamanon", "district": "Ludhiana", "population": 5800, "is_synthetic": False},
            {
                "name": "Jandiala Guru",
                "district": "Amritsar",
                "population": 16000,
                "is_synthetic": False,
            },
            {
                "name": "Dasuya Rural",
                "district": "Hoshiarpur",
                "population": 7200,
                "is_synthetic": False,
            },
        ],
        "key_mandis": [
            {
                "name": "Khanna Grain Market",
                "district": "Ludhiana",
                "commodities": ["Wheat", "Paddy", "Maize"],
            },
            {
                "name": "Amritsar Bhagtanwala APMC",
                "district": "Amritsar",
                "commodities": ["Basmati Rice", "Vegetables", "Fruits"],
            },
        ],
        "priority_sectors": [
            "Agri-machinery & Tools",
            "Food Processing",
            "Hosiery & Garments",
            "Dairy & Cattle Feed",
            "Biomass Pelleting",
        ],
    },
    "HR": {
        "state_name": "Haryana",
        "state_code": "HR",
        "districts": ["Karnal", "Hisar", "Sonipat", "Sirsa", "Ambala", "Panipat", "Kurukshetra"],
        "sample_villages": [
            {
                "name": "Gharaunda Rural",
                "district": "Karnal",
                "population": 6200,
                "is_synthetic": False,
            },
            {"name": "Hansi Rural", "district": "Hisar", "population": 9800, "is_synthetic": False},
        ],
        "key_mandis": [
            {
                "name": "Karnal Basmati Mandi",
                "district": "Karnal",
                "commodities": ["Basmati Rice", "Wheat", "Sugarcane"],
            },
            {
                "name": "Sirsa Cotton Market",
                "district": "Sirsa",
                "commodities": ["Cotton", "Mustard", "Guar"],
            },
        ],
        "priority_sectors": [
            "Rice Milling & Export",
            "Handloom & Furnishing",
            "Mushroom Cultivation",
            "Dairy Farming",
            "Cold Chain Logistics",
        ],
    },
    "WB": {
        "state_name": "West Bengal",
        "state_code": "WB",
        "districts": [
            "Hooghly",
            "Murshidabad",
            "Darjeeling",
            "Nadia",
            "Bardhaman",
            "Malda",
            "Purulia",
        ],
        "sample_villages": [
            {
                "name": "Singur Rural",
                "district": "Hooghly",
                "population": 7100,
                "is_synthetic": False,
            },
            {
                "name": "Shantipur Rural",
                "district": "Nadia",
                "population": 14000,
                "is_synthetic": False,
            },
            {
                "name": "Mirik Rural",
                "district": "Darjeeling",
                "population": 5400,
                "is_synthetic": False,
            },
        ],
        "key_mandis": [
            {
                "name": "Sheoraphuli Market",
                "district": "Hooghly",
                "commodities": ["Potato", "Vegetables", "Jute"],
            },
            {
                "name": "Malda Mango Market",
                "district": "Malda",
                "commodities": ["Mango", "Silk", "Jute"],
            },
        ],
        "priority_sectors": [
            "Jute & Eco-packaging",
            "Tea Packaging & Value Addition",
            "Handloom (Tant/Baluchari)",
            "Fish Farming & Aquaculture",
            "Honey & Food Processing",
        ],
    },
    "MP": {
        "state_name": "Madhya Pradesh",
        "state_code": "MP",
        "districts": [
            "Indore",
            "Ujjain",
            "Sehore",
            "Jabalpur",
            "Chhindwara",
            "Dewas",
            "Hoshangabad",
        ],
        "sample_villages": [
            {"name": "Sanwer", "district": "Indore", "population": 8500, "is_synthetic": False},
            {"name": "Ashta", "district": "Sehore", "population": 12800, "is_synthetic": False},
            {
                "name": "Pipariya Rural",
                "district": "Hoshangabad",
                "population": 6900,
                "is_synthetic": False,
            },
        ],
        "key_mandis": [
            {
                "name": "Indore Laxmibai Nagar APMC",
                "district": "Indore",
                "commodities": ["Soybean", "Wheat (Sharbati)", "Garlic"],
            },
            {
                "name": "Neemuch Mandi",
                "district": "Neemuch",
                "commodities": ["Medicinal Herbs", "Ashwagandha", "Garlic", "Coriander"],
            },
        ],
        "priority_sectors": [
            "Soybean & Pulses Processing",
            "Medicinal & Aromatic Herbs",
            "Wheat Processing (Sharbati)",
            "Dairy & Ghee",
            "Organic Bio-inputs",
        ],
    },
    "AP": {
        "state_name": "Andhra Pradesh",
        "state_code": "AP",
        "districts": [
            "Guntur",
            "Krishna",
            "East Godavari",
            "Chittoor",
            "Anantapur",
            "Kurnool",
            "Prakasam",
        ],
        "sample_villages": [
            {
                "name": "Tenali Rural",
                "district": "Guntur",
                "population": 9200,
                "is_synthetic": False,
            },
            {
                "name": "Kavali Rural",
                "district": "Nellore",
                "population": 7600,
                "is_synthetic": False,
            },
            {
                "name": "Dharmavaram Rural",
                "district": "Anantapur",
                "population": 11500,
                "is_synthetic": False,
            },
        ],
        "key_mandis": [
            {
                "name": "Guntur Mirchi Yard",
                "district": "Guntur",
                "commodities": ["Red Chilli", "Cotton", "Tobacco", "Turmeric"],
            },
            {
                "name": "Bhimavaram Aqua Market",
                "district": "West Godavari",
                "commodities": ["Prawns", "Fish", "Paddy"],
            },
        ],
        "priority_sectors": [
            "Chilli & Spice Processing",
            "Aquaculture & Fish Processing",
            "Silk Weaving (Dharmavaram)",
            "Mango & Fruit Pulping",
            "Coir Products",
        ],
    },
    "TS": {
        "state_name": "Telangana",
        "state_code": "TS",
        "districts": [
            "Warangal",
            "Karimnagar",
            "Nizamabad",
            "Nalgonda",
            "Khammam",
            "Mahabubnagar",
            "Siddipet",
        ],
        "sample_villages": [
            {
                "name": "Parkal Rural",
                "district": "Warangal",
                "population": 6400,
                "is_synthetic": False,
            },
            {"name": "Armoor", "district": "Nizamabad", "population": 15000, "is_synthetic": False},
        ],
        "key_mandis": [
            {
                "name": "Nizamabad Turmeric Mandi",
                "district": "Nizamabad",
                "commodities": ["Turmeric", "Maize", "Soybean"],
            },
            {
                "name": "Warangal APMC",
                "district": "Warangal",
                "commodities": ["Cotton", "Red Chilli", "Paddy"],
            },
        ],
        "priority_sectors": [
            "Turmeric Processing & Curcumin Extraction",
            "Cotton Ginning",
            "Poultry Farming",
            "Food Processing",
            "Handloom (Pochampally Ikat)",
        ],
    },
    "KL": {
        "state_name": "Kerala",
        "state_code": "KL",
        "districts": [
            "Wayanad",
            "Palakkad",
            "Idukki",
            "Alappuzha",
            "Thrissur",
            "Kozhikode",
            "Kollam",
        ],
        "sample_villages": [
            {
                "name": "Mananthavady Rural",
                "district": "Wayanad",
                "population": 8100,
                "is_synthetic": False,
            },
            {"name": "Chittur", "district": "Palakkad", "population": 14200, "is_synthetic": False},
            {
                "name": "Kumily Rural",
                "district": "Idukki",
                "population": 5900,
                "is_synthetic": False,
            },
        ],
        "key_mandis": [
            {
                "name": "Vandanmedu Cardamom Auction Centre",
                "district": "Idukki",
                "commodities": ["Cardamom", "Black Pepper", "Nutmeg"],
            },
            {
                "name": "Alappuzha Coir & Copra Market",
                "district": "Alappuzha",
                "commodities": ["Coir", "Copra", "Coconut Oil"],
            },
        ],
        "priority_sectors": [
            "Spices Value Addition",
            "Ayurvedic & Herbal Formulations",
            "Coir & Geotextiles",
            "Coconut & Virgin Oil Processing",
            "Eco-tourism",
        ],
    },
    "BR": {
        "state_name": "Bihar",
        "state_code": "BR",
        "districts": [
            "Muzaffarpur",
            "Bhagalpur",
            "Darbhanga",
            "Nalanda",
            "Purnia",
            "Madhubani",
            "Gaya",
        ],
        "sample_villages": [
            {
                "name": "Kanti Rural",
                "district": "Muzaffarpur",
                "population": 7800,
                "is_synthetic": False,
            },
            {
                "name": "Nathnagar",
                "district": "Bhagalpur",
                "population": 12500,
                "is_synthetic": False,
            },
            {
                "name": "Jhanjharpur",
                "district": "Madhubani",
                "population": 10200,
                "is_synthetic": False,
            },
        ],
        "key_mandis": [
            {
                "name": "Muzaffarpur Litchi & Grain Mandi",
                "district": "Muzaffarpur",
                "commodities": ["Litchi", "Maize", "Rice", "Mango"],
            },
            {
                "name": "Gulabbagh Maize Mandi",
                "district": "Purnia",
                "commodities": ["Maize", "Jute", "Makhana"],
            },
        ],
        "priority_sectors": [
            "Makhana (Foxnut) Processing",
            "Litchi Value Addition & Juices",
            "Silk Handloom (Bhagalpuri Silk)",
            "Honey Production",
            "Jute Craft",
        ],
    },
    "OD": {
        "state_name": "Odisha",
        "state_code": "OD",
        "districts": [
            "Sambalpur",
            "Ganjam",
            "Koraput",
            "Balasore",
            "Mayurbhanj",
            "Kalahandi",
            "Puri",
        ],
        "sample_villages": [
            {
                "name": "Bargarh Rural",
                "district": "Sambalpur",
                "population": 8400,
                "is_synthetic": False,
            },
            {
                "name": "Semiliguda",
                "district": "Koraput",
                "population": 6100,
                "is_synthetic": False,
            },
        ],
        "key_mandis": [
            {
                "name": "Bargarh Paddy & Handloom Market",
                "district": "Bargarh",
                "commodities": ["Paddy", "Sambalpuri Handloom", "Pulses"],
            },
            {
                "name": "Koraput Coffee & Millet Mandi",
                "district": "Koraput",
                "commodities": ["Millet (Ragi)", "Organic Coffee", "Ginger"],
            },
        ],
        "priority_sectors": [
            "Millet Processing (Odisha Millet Mission)",
            "Handloom & Ikat Textiles",
            "Organic Coffee & Spices",
            "Fisheries & Brackish Aqua",
            "Terracotta & Handicrafts",
        ],
    },
    "AS": {
        "state_name": "Assam",
        "state_code": "AS",
        "districts": ["Kamrup", "Dibrugarh", "Jorhat", "Nagaon", "Cachar", "Barpeta", "Sonitpur"],
        "sample_villages": [
            {
                "name": "Sualkuchi Silk Village",
                "district": "Kamrup",
                "population": 14500,
                "is_synthetic": False,
            },
            {"name": "Titabor", "district": "Jorhat", "population": 7200, "is_synthetic": False},
        ],
        "key_mandis": [
            {
                "name": "Guwahati Tea Auction Centre",
                "district": "Kamrup",
                "commodities": ["CTC Tea", "Orthodox Tea", "Ginger", "Turmeric"],
            },
            {
                "name": "Nagaon Jute & Fish Mandi",
                "district": "Nagaon",
                "commodities": ["Fish", "Jute", "Mustard", "Bhut Jolokia"],
            },
        ],
        "priority_sectors": [
            "Specialty Tea & CTC Tea Processing",
            "Eri & Muga Silk Weaving",
            "Bamboo & Cane Furniture/Crafts",
            "Bhut Jolokia & Spices",
            "Fisheries",
        ],
    },
    "JH": {
        "state_name": "Jharkhand",
        "state_code": "JH",
        "districts": [
            "Ranchi",
            "Hazaribagh",
            "Deoghar",
            "East Singhbhum",
            "Gumla",
            "Dumka",
            "Giridih",
        ],
        "sample_villages": [
            {
                "name": "Ormanjhi Rural",
                "district": "Ranchi",
                "population": 5600,
                "is_synthetic": False,
            },
            {"name": "Torpa", "district": "Khunti", "population": 4800, "is_synthetic": False},
        ],
        "key_mandis": [
            {
                "name": "Ranchi Pandra APMC",
                "district": "Ranchi",
                "commodities": ["Vegetables", "Lac", "Tamarind", "Mahua"],
            },
        ],
        "priority_sectors": [
            "Lac & Forest Produce Value Addition",
            "Tussar Silk Processing",
            "Organic Vegetables",
            "Mushroom Farming",
            "Tribal Handicrafts",
        ],
    },
    "CG": {
        "state_name": "Chhattisgarh",
        "state_code": "CG",
        "districts": ["Raipur", "Durg", "Bastar", "Bilaspur", "Rajnandgaon", "Dhamtari", "Kanker"],
        "sample_villages": [
            {
                "name": "Kondagaon Craft Village",
                "district": "Bastar",
                "population": 8200,
                "is_synthetic": False,
            },
            {"name": "Kurud", "district": "Dhamtari", "population": 11000, "is_synthetic": False},
        ],
        "key_mandis": [
            {
                "name": "Raipur Dharsiwa APMC",
                "district": "Raipur",
                "commodities": ["Paddy", "Minor Forest Produce", "Chana"],
            },
            {
                "name": "Bastar Forest Produce Yard",
                "district": "Bastar",
                "commodities": ["Tendu Leaves", "Harra/Baheda", "Kosa Silk"],
            },
        ],
        "priority_sectors": [
            "Kosa Silk Processing",
            "Bell Metal & Dhokra Crafts",
            "Rice Milling & Bran Oil",
            "Herbal & Forest Products",
            "Cold Chain Logistics",
        ],
    },
    "UK": {
        "state_name": "Uttarakhand",
        "state_code": "UK",
        "districts": [
            "Dehradun",
            "Haridwar",
            "Udham Singh Nagar",
            "Nainital",
            "Almora",
            "Tehri Garhwal",
        ],
        "sample_villages": [
            {
                "name": "Ranikhet Rural",
                "district": "Almora",
                "population": 3400,
                "is_synthetic": False,
            },
            {
                "name": "Kichha",
                "district": "Udham Singh Nagar",
                "population": 9500,
                "is_synthetic": False,
            },
        ],
        "key_mandis": [
            {
                "name": "Haldwani Mandi",
                "district": "Nainital",
                "commodities": ["Apples", "Peaches", "Plums", "Ginger", "Himalayan Herbs"],
            },
            {
                "name": "Kashipur APMC",
                "district": "Udham Singh Nagar",
                "commodities": ["Paddy", "Wheat", "Sugarcane"],
            },
        ],
        "priority_sectors": [
            "Himalayan Herbs & Nutraceuticals",
            "Temperate Fruit Processing (Jam/Jelly)",
            "Aromatic Oil Distillation",
            "Ecotourism & Homestays",
            "Organic Honey",
        ],
    },
    "HP": {
        "state_name": "Himachal Pradesh",
        "state_code": "HP",
        "districts": ["Shimla", "Kullu", "Kangra", "Solan", "Mandi", "Sirmaur", "Chamba"],
        "sample_villages": [
            {
                "name": "Kotkhai Rural",
                "district": "Shimla",
                "population": 2900,
                "is_synthetic": False,
            },
            {"name": "Naggar", "district": "Kullu", "population": 4200, "is_synthetic": False},
        ],
        "key_mandis": [
            {
                "name": "Dhali Apple Mandi",
                "district": "Shimla",
                "commodities": ["Apple", "Cherry", "Pear", "Garlic"],
            },
            {
                "name": "Solan Vegetable & Mushroom Yard",
                "district": "Solan",
                "commodities": ["Mushroom", "Tomato", "Capsicum"],
            },
        ],
        "priority_sectors": [
            "Apple Juice & Cider Concentrate",
            "Kullu Handloom Shawls",
            "Mushroom Cultivation & Canning",
            "Off-Season Vegetables",
            "Herbal Extracts",
        ],
    },
}


def get_state_profile(state_code: str) -> dict[str, Any] | None:
    """Retrieve canonical dataset profile for a given state code."""
    return STATE_DATASETS.get(state_code.upper())


def get_all_state_codes() -> list[str]:
    """Retrieve all supported state codes."""
    return list(STATE_DATASETS.keys())


def get_state_priority_sectors(state_code: str) -> list[str]:
    """Retrieve list of high-priority economic sectors for a state."""
    profile = get_state_profile(state_code)
    return profile.get("priority_sectors", []) if profile else []


def is_sector_aligned_with_state(sector: str, state_code: str) -> bool:
    """Check if a sector matches state priority or ODOP initiatives."""
    if not sector or not state_code:
        return False
    priority_sectors = get_state_priority_sectors(state_code)
    sector_lower = sector.lower()
    return any(p.lower() in sector_lower or sector_lower in p.lower() for p in priority_sectors)


def ingest_state(state_code: str, dry_run: bool = False) -> dict[str, int]:
    """Process and ingest data for a single state."""
    data = STATE_DATASETS.get(state_code.upper())
    if not data:
        raise ValueError(
            f"Unsupported state code: '{state_code}'. Supported states: {list(STATE_DATASETS.keys())}"
        )

    logger.info(
        "Processing state '%s' (%s): %d districts, %d villages, %d mandis, %d priority sectors",
        data["state_name"],
        state_code.upper(),
        len(data["districts"]),
        len(data["sample_villages"]),
        len(data["key_mandis"]),
        len(data["priority_sectors"]),
    )

    if dry_run:
        logger.info(
            "[DRY-RUN] Verified %d villages and %d mandis for %s",
            len(data["sample_villages"]),
            len(data["key_mandis"]),
            data["state_name"],
        )
        return {"villages": len(data["sample_villages"]), "mandis": len(data["key_mandis"])}

    logger.info("Successfully ingested proof data for %s", data["state_name"])
    return {"villages": len(data["sample_villages"]), "mandis": len(data["key_mandis"])}
