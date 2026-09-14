"""
Predefined sample listeners for all profession categories in the Buddy application.
Used for auto-seeding categories and populating test listeners via management commands.
"""

SAMPLE_CATEGORY_LISTENERS = {
    "Teacher": [
        {
            "username": "prof_anjali_nair",
            "name": "Prof. Anjali Nair",
            "gender": "Female",
            "language": "English, Hindi, Malayalam",
            "bio": "Dedicated educator with 10+ years of academic guidance, career counseling, and exam stress relief.",
            "interests": ["Academic & Studies", "Career & Motivation", "Friendly Chat"],
            "rate_per_second": 3,
            "rating": 4.9,
            "password": "ListenerPass123!"
        },
        {
            "username": "mr_robert_clark",
            "name": "Robert Clark",
            "gender": "Male",
            "language": "English",
            "bio": "High school literature teacher and mentor. Passionate about reading, writing, and constructive conversations.",
            "interests": ["Self Improvement", "Life Advice", "Friendly Chat"],
            "rate_per_second": 3,
            "rating": 4.8,
            "password": "ListenerPass123!"
        }
    ],
    "Student": [
        {
            "username": "student_rahul",
            "name": "Rahul Menon",
            "gender": "Male",
            "language": "English, Malayalam, Hindi",
            "bio": "Final-year college student. Great listener for exam stress, campus life, peer pressure, and everyday venting.",
            "interests": ["Daily Venting", "Stress & Anxiety", "Friendship"],
            "rate_per_second": 3,
            "rating": 4.8,
            "password": "ListenerPass123!"
        },
        {
            "username": "student_sneha",
            "name": "Sneha Patel",
            "gender": "Female",
            "language": "English, Hindi, Gujarati",
            "bio": "Postgraduate student navigating university life and study-life balance. Here to listen and connect anytime.",
            "interests": ["Academic & Studies", "Casual Conversation", "Emotional Support"],
            "rate_per_second": 3,
            "rating": 4.9,
            "password": "ListenerPass123!"
        }
    ],
    "Doctor": [
        {
            "username": "dr_sarah_jenkins",
            "name": "Dr. Sarah Jenkins",
            "gender": "Female",
            "language": "English",
            "bio": "Experienced General Physician offering consultation on general health, preventive care, and wellness.",
            "interests": ["Medical Advice", "Health & Wellness", "Friendly Chat"],
            "rate_per_second": 3,
            "rating": 4.9,
            "password": "DoctorPass123!"
        },
        {
            "username": "dr_arun_kumar",
            "name": "Dr. Arun Kumar",
            "gender": "Male",
            "language": "English, Malayalam, Hindi",
            "bio": "Consultant Physician specializing in lifestyle medicine, second opinions, and routine health counseling.",
            "interests": ["Clinical Consultation", "Stress & Anxiety", "Health Guidance"],
            "rate_per_second": 3,
            "rating": 4.8,
            "password": "DoctorPass123!"
        }
    ],
    "Engineer": [
        {
            "username": "eng_vikram_singh",
            "name": "Vikram Singh",
            "gender": "Male",
            "language": "English, Hindi",
            "bio": "Systems engineer with experience across automation and tech stacks. Great listener for career transitions and tech talks.",
            "interests": ["Career & Motivation", "Self Improvement", "Active Listening"],
            "rate_per_second": 3,
            "rating": 4.8,
            "password": "ListenerPass123!"
        },
        {
            "username": "eng_kavita_reddy",
            "name": "Kavita Reddy",
            "gender": "Female",
            "language": "English, Telugu, Hindi",
            "bio": "Civil engineer and infrastructure planner. Passionate about creative problem solving and balanced work life.",
            "interests": ["Life Advice", "Friendly Chat", "Mindfulness"],
            "rate_per_second": 3,
            "rating": 4.9,
            "password": "ListenerPass123!"
        }
    ],
    "Lawyer": [
        {
            "username": "adv_rajesh_menon",
            "name": "Adv. Rajesh Menon",
            "gender": "Male",
            "language": "English, Malayalam, Hindi",
            "bio": "Legal advisor with extensive experience in corporate compliance, consumer rights, and conflict resolution.",
            "interests": ["Career & Motivation", "Life Advice", "Active Listening"],
            "rate_per_second": 5,
            "rating": 4.9,
            "password": "ListenerPass123!"
        },
        {
            "username": "adv_meera_iyer",
            "name": "Adv. Meera Iyer",
            "gender": "Female",
            "language": "English, Tamil, Hindi",
            "bio": "Legal counsel specializing in contracts and IP rights. Calm, thoughtful perspective on life and career questions.",
            "interests": ["Self Improvement", "Mindfulness", "Friendly Chat"],
            "rate_per_second": 5,
            "rating": 4.8,
            "password": "ListenerPass123!"
        }
    ],
    "Business": [
        {
            "username": "biz_siddharth_jain",
            "name": "Siddharth Jain",
            "gender": "Male",
            "language": "English, Hindi",
            "bio": "Serial entrepreneur and angel investor. Love discussing startups, leadership, growth mindset, and strategy.",
            "interests": ["Career & Motivation", "Self Improvement", "Life Advice"],
            "rate_per_second": 5,
            "rating": 4.9,
            "password": "ListenerPass123!"
        },
        {
            "username": "biz_tanya_kapoor",
            "name": "Tanya Kapoor",
            "gender": "Female",
            "language": "English, Hindi, Punjabi",
            "bio": "Brand strategist and e-commerce consultant. Here to chat marketing, hustle, and career advancement.",
            "interests": ["Friendly Chat", "Career & Motivation", "Casual Conversation"],
            "rate_per_second": 5,
            "rating": 4.8,
            "password": "ListenerPass123!"
        }
    ],
    "Artist": [
        {
            "username": "artist_maya_sen",
            "name": "Maya Sen",
            "gender": "Female",
            "language": "English, Bengali, Hindi",
            "bio": "Illustrator and visual artist. Passionate about art therapy, storytelling, creative expression, and mindfulness.",
            "interests": ["Mindfulness", "Self Improvement", "Emotional Support"],
            "rate_per_second": 3,
            "rating": 4.9,
            "password": "ListenerPass123!"
        },
        {
            "username": "artist_arjun_das",
            "name": "Arjun Das",
            "gender": "Male",
            "language": "English, Hindi",
            "bio": "Independent music producer and songwriter. Open ears for creative burnout, musical dreams, and relaxing chats.",
            "interests": ["Friendly Chat", "Active Listening", "Casual Conversation"],
            "rate_per_second": 3,
            "rating": 4.8,
            "password": "ListenerPass123!"
        }
    ],
    "Chef": [
        {
            "username": "chef_antony_louis",
            "name": "Chef Antony Louis",
            "gender": "Male",
            "language": "English, French",
            "bio": "Executive culinary chef with a love for world cuisines, kitchen secrets, and warm conversational comfort.",
            "interests": ["Casual Conversation", "Friendly Chat", "Life Advice"],
            "rate_per_second": 3,
            "rating": 4.8,
            "password": "ListenerPass123!"
        },
        {
            "username": "chef_pooja_hegde",
            "name": "Chef Pooja Hegde",
            "gender": "Female",
            "language": "English, Kannada, Hindi",
            "bio": "Pastry chef and bakery owner. Passionate about food therapy, sweet stories, and heartwarming chats.",
            "interests": ["Emotional Support", "Friendly Chat", "Daily Venting"],
            "rate_per_second": 3,
            "rating": 4.9,
            "password": "ListenerPass123!"
        }
    ],
    "Nurse": [
        {
            "username": "nurse_mary_joseph",
            "name": "Mary Joseph",
            "gender": "Female",
            "language": "English, Malayalam",
            "bio": "Senior registered nurse with 12 years of empathetic patient care. Always here to offer a soothing, caring ear.",
            "interests": ["Emotional Support", "Health & Wellness", "Active Listening"],
            "rate_per_second": 3,
            "rating": 5.0,
            "password": "ListenerPass123!"
        },
        {
            "username": "nurse_deepa_rani",
            "name": "Deepa Rani",
            "gender": "Female",
            "language": "English, Tamil, Hindi",
            "bio": "Healthcare caregiver and patient counselor. A calm, compassionate voice when you need comfort and encouragement.",
            "interests": ["Stress & Anxiety", "Emotional Support", "Mindfulness"],
            "rate_per_second": 3,
            "rating": 4.9,
            "password": "ListenerPass123!"
        }
    ],
    "Software Developer": [
        {
            "username": "dev_karthik_surya",
            "name": "Karthik Surya",
            "gender": "Male",
            "language": "English, Tamil, Hindi",
            "bio": "Full-stack engineer and cloud architect. Let's talk tech life, coding burnout, side projects, or casual banter.",
            "interests": ["Career & Motivation", "Friendly Chat", "Casual Conversation"],
            "rate_per_second": 3,
            "rating": 4.9,
            "password": "ListenerPass123!"
        },
        {
            "username": "dev_neha_sharma",
            "name": "Neha Sharma",
            "gender": "Female",
            "language": "English, Hindi",
            "bio": "Frontend developer and UI enthusiast. Available for tech talks, impostor syndrome discussions, and friendly chats.",
            "interests": ["Self Improvement", "Friendly Chat", "Active Listening"],
            "rate_per_second": 3,
            "rating": 4.8,
            "password": "ListenerPass123!"
        }
    ],
    "Accountant": [
        {
            "username": "ca_abhishek_verma",
            "name": "CA Abhishek Verma",
            "gender": "Male",
            "language": "English, Hindi",
            "bio": "Chartered accountant helping individuals and entrepreneurs with financial clarity, budgeting, and career advice.",
            "interests": ["Life Advice", "Career & Motivation", "Self Improvement"],
            "rate_per_second": 5,
            "rating": 4.9,
            "password": "ListenerPass123!"
        },
        {
            "username": "ca_lakshmi_prasad",
            "name": "CA Lakshmi Prasad",
            "gender": "Female",
            "language": "English, Telugu, Hindi",
            "bio": "Financial auditor and tax consultant. Thoughtful, structured guidance for life, finances, and personal peace of mind.",
            "interests": ["Friendly Chat", "Life Advice", "Active Listening"],
            "rate_per_second": 5,
            "rating": 4.8,
            "password": "ListenerPass123!"
        }
    ],
    "Technician": [
        {
            "username": "tech_suresh_babu",
            "name": "Suresh Babu",
            "gender": "Male",
            "language": "English, Malayalam, Tamil",
            "bio": "Senior electronics technician. Hands-on, practical thinker who loves sharing life wisdom and everyday advice.",
            "interests": ["Casual Conversation", "Friendly Chat", "Daily Support"],
            "rate_per_second": 3,
            "rating": 4.7,
            "password": "ListenerPass123!"
        },
        {
            "username": "tech_manoj_kumar",
            "name": "Manoj Kumar",
            "gender": "Male",
            "language": "English, Hindi",
            "bio": "Field service technician and IT troubleshooter. Down-to-earth conversation and a great listener for venting.",
            "interests": ["Daily Venting", "Friendship", "Friendly Chat"],
            "rate_per_second": 3,
            "rating": 4.8,
            "password": "ListenerPass123!"
        }
    ],
    "Other": [
        {
            "username": "counselor_riya",
            "name": "Riya Sen",
            "gender": "Female",
            "language": "English, Bengali, Hindi",
            "bio": "Empathetic companion and active listener. Here with a non-judgmental space for whatever you are carrying.",
            "interests": ["Emotional Support", "Active Listening", "Mindfulness"],
            "rate_per_second": 3,
            "rating": 4.9,
            "password": "ListenerPass123!"
        },
        {
            "username": "coach_david",
            "name": "David Vance",
            "gender": "Male",
            "language": "English",
            "bio": "Personal wellness guide and conversationalist. Ready to chat through your day, thoughts, or upcoming goals.",
            "interests": ["Life Advice", "Self Improvement", "Friendly Chat"],
            "rate_per_second": 3,
            "rating": 4.8,
            "password": "ListenerPass123!"
        }
    ]
}

# Mapping of standard test listeners (LISTENER_001, LISTENER_101-105) to default categories
DEFAULT_LISTENER_CATEGORY_MAP = {
    "LISTENER_001": "Teacher",
    "LISTENER_101": "Business",
    "LISTENER_102": "Student",
    "LISTENER_103": "Artist",
    "LISTENER_104": "Engineer",
    "LISTENER_105": "Software Developer"
}
