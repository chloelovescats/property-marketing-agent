# 🏠 Real Estate Marketing AI Agent (v2)

A tool that takes a **property address** and automatically writes **professional marketing copy** for it — using real nearby amenity data from Google Maps and AI writing from Gemini.

---

## ✨ New in v2: The AI Agent & Premium UI

-   **LangGraph Agent**: Uses a Planner → Search → Critic loop to ensure amenities are relevant to your specific buyer.
-   **Live Streaming (SSE)**: Watch the agent "think" and search in real-time with a live activity log.
-   **Premium Redesign**: A clean, professional **Roboto-based** interface with floating cards and deep elevation.
-   **"How It Works" Visual**: Built-in 5-step flowchart explaining the agentic pipeline.
-   **No-Nonsense Branding**: Streamlined, emoji-free enterprise look.

---

## 👋 Welcome, Junior Developer!

Don't worry if you're new to this. This guide walks you through **every single step**, from getting your API keys to running the app. Just follow along in order and you'll be up and running in about 15 minutes.

---

## What You'll Need Before Starting

- A computer running **Windows**
- **Python 3.10 or newer** installed → [Download here](https://www.python.org/downloads/)
- A **Google account** (Gmail is fine)
- An internet connection

> ✅ **Tip:** When installing Python, make sure to tick the box that says **"Add Python to PATH"** on the first installer screen. This is easy to miss!

---

## Step 1 — Get Your Google Maps API Key (from Google Cloud)

This key lets the app search for nearby places and convert addresses into coordinates.

### 1.1 Create a Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com/)
2. Sign in with your Google account
3. Click the **project dropdown** at the top of the page (it might say "Select a project")
4. Click **"New Project"**
5. Give it any name you like (e.g. `real-estate-agent`) and click **"Create"**
6. Wait a few seconds, then make sure your new project is selected in the dropdown

### 1.2 Enable Billing (Required by Google)

Google requires a billing account to use their APIs, but you get a **$300 free credit** and normal usage of this app costs almost nothing.

1. In the left sidebar, click **"Billing"**
2. Click **"Link a billing account"** and follow the steps to add a payment method
3. Once done, you're ready to enable APIs

### 1.3 Enable the Required APIs

You need to turn on **two APIs**:

**Geocoding API** (converts an address into coordinates):
1. In the left sidebar, go to **APIs & Services → Library**
2. Search for **"Geocoding API"**
3. Click on it, then click the blue **"Enable"** button

**Places API** (finds nearby MRT stations, malls, schools, etc.):
1. Go back to the Library (use the browser back button or the sidebar)
2. Search for **"Places API"**
3. Click on it, then click **"Enable"**

### 1.4 Create Your API Key

1. In the left sidebar, go to **APIs & Services → Credentials**
2. Click **"+ Create Credentials"** at the top
3. Choose **"API key"**
4. Google will generate a key that looks like: `AIzaSyAbc123ExampleKey...`
5. **Copy this key and keep it safe** — you'll need it in Step 3

> ⚠️ **Important:** Never share this key publicly or upload it to GitHub. The `.gitignore` file in this project already protects your `.env` file from being accidentally shared.

---

## Step 2 — Get Your Gemini API Key (from Google AI Studio)

This is a **separate key** from the one above. Gemini is the AI that writes the marketing copy.

1. Go to [aistudio.google.com/apikey](https://aistudio.google.com/apikey)
2. Sign in with your Google account if prompted
3. Click **"Create API Key"**
4. Select the Google Cloud project you created in Step 1 from the dropdown, then click **"Create API key in existing project"**
5. Copy the key that appears — it also looks like `AIzaSy...`

> ✅ **Tip:** You can always come back to this page later if you lose your key.

---

## Step 3 — Add Your API Keys to the `.env` File

The project folder already has an empty `.env` file waiting for you.

1. Open the `.env` file with any text editor (Notepad is fine — just right-click the file and choose "Open with → Notepad")
2. Type the following into the file, replacing the placeholder text with your actual keys:

```
GOOGLE_MAPS_API_KEY=paste_your_google_maps_key_here
GEMINI_API_KEY=paste_your_gemini_key_here
```

**Example of what it should look like when filled in:**

```
GOOGLE_MAPS_API_KEY=AIzaSyAbc123YourRealKeyHere
GEMINI_API_KEY=AIzaSyXyz789YourOtherRealKeyHere
```

3. Save the file (`Ctrl + S`) and close it

> ⚠️ **Do NOT add quotes or spaces around the keys.** Just paste them directly after the `=` sign.

---

## Step 4 — Open a Terminal in the Project Folder

1. Open **File Explorer** and navigate to this project's folder
2. Click on the address bar at the top of the window (where the folder path is shown)
3. Type `cmd` and press **Enter** — this opens a Command Prompt directly inside the folder

You should see a black window with something like:

```
C:\Users\YourName\...\singapore_real_estate>
```

All the commands in the next steps are typed here.

---

## Step 5 — Create a Virtual Environment (venv)

A virtual environment is an isolated space for this project's Python packages. Think of it like a separate box so that packages for this project don't interfere with other Python projects on your computer.

Run this command:

```cmd
python -m venv venv
```

You'll see a new folder called `venv` appear in the project directory. That's normal — it was just created.

Now **activate** the virtual environment:

```cmd
venv\Scripts\activate
```

Your terminal prompt should now start with `(venv)` — like this:

```
(venv) C:\Users\YourName\...\singapore_real_estate>
```

That `(venv)` prefix means the virtual environment is active. 

> ✅ **Tip:** Every time you open a new terminal for this project in the future, you need to re-run the `venv\Scripts\activate` command. The `start.bat` file in Step 6 handles this for you automatically.

---

## Step 6 — Install the Required Packages

While your virtual environment is active, run:

```cmd
pip install -r requirements.txt
```

This reads the `requirements.txt` file and downloads all the Python packages the app needs. It may take a minute or two. You'll see a lot of output — that's normal.

When it finishes, you should see something like:

```
Successfully installed flask-... requests-... ...
```

---

## Step 7 — Run the App Using `start.bat`

You're ready! The easiest way to launch everything is to use the **`start.bat`** file included in this project.

**Option A — Double-click it:**
- Open File Explorer, navigate to the project folder, and **double-click `start.bat`**

**Option B — Run it from the terminal:**
```cmd
start.bat
```

### What `start.bat` does automatically:
1. ✅ Checks that Python is installed
2. ✅ Checks that your `.env` file exists (and shows an error if you forgot to fill it in)
3. ✅ Installs any missing packages from `requirements.txt`
4. ✅ Opens your browser to the app
5. ✅ Starts the Flask backend server

> 🛑 **To stop the app:** Click on the terminal window that opened and press `Ctrl + C`.

---

## 📊 Architecture Diagram

```mermaid
graph TD
    Start((START)) --> Plan[Planner Node]
    Plan -->|"Search Strategy"| Search[Search Node]
    Search -->|"API Results"| Critic[Critic Node]
    
    Critic -->|Needs More Data| Plan
    Critic -->|Satisfied| Done((END))

    subgraph "AI Agent Loop (LangGraph)"
        Plan
        Search
        Critic
    end

    subgraph "External Tools"
        Search --- GMap[(Google Maps API)]
        Plan --- Gem1[(Gemini 1.5 Flash)]
        Critic --- Gem2[(Gemini 1.5 Flash)]
    end
```

---

## 🧠 How the Agent Works (The Loop)

This app doesn't just do a single search. It follows an **agentic loop** to ensure quality:

1.  **Planner (Gemini 1.5 Flash)**: Analyzes your buyer profile (e.g., "Young family") and picks the 3-5 most relevant categories to search for.
2.  **Searcher (Google Maps Tools)**: Hits the real-world Google Places database to find actual names, ratings, and distances.
3.  **Critic (Gemini 1.5 Flash)**: Reviews the results. If they don't match the buyer’s needs, it **loops back** to the Planner with instructions to try a different search strategy.
4.  **Copy Generator**: Once the agent is satisfied, it writes the final marketing copy using the verified data.

---

## Project Structure

```
singapore_real_estate/
├── app.py                 # Backend entry point (Flask + SSE)
├── agent/                 # THE BRAIN (LangGraph)
│   ├── graph.py           # Workflow & router
│   ├── nodes.py           # AI logic (Planner, Searcher, Critic)
│   └── state.py           # Agent's short-term memory
├── services/              # Core tools (Google Maps, AI Copy)
├── frontend/              # Web UI (Roboto Typography)
│   ├── index.html
│   ├── styles.css         # Premium Floating Card CSS
│   └── script.js          # SSE Streaming Handler
├── start.bat              # One-click Windows runner
└── .env                   # API keys (Keep this private!)
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `python` is not recognized | Python isn't installed or wasn't added to PATH. Re-install Python and tick "Add to PATH" |
| `pip` is not recognized | Make sure your virtual environment is activated (`venv\Scripts\activate`) |
| `[ERROR] .env file not found` | Make sure you created and saved the `.env` file with your API keys |
| App opens but gives an API error | Double-check your keys in `.env` are correct and the APIs are enabled in Google Cloud |
| Port 5000 already in use | Another program is using that port. Restart your computer and try again |

---

---

## Developed by:
**Lim Yuxuan Chloe**

---

## License

This project is for educational and demonstration purposes.
