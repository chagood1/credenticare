# backend/services/supabase_client.py

import os
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# 1️⃣ Load your project-root .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# 2️⃣ Read the credentials
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 3️⃣ Debug print to verify loading
print("🔐 Supabase URL:", SUPABASE_URL)
print("🔐 Supabase Key starts with:", SUPABASE_KEY[:8], "...")

# 4️⃣ Initialize the Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
