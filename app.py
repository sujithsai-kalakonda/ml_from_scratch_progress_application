import streamlit as st
import json
import os
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import time

# Setup paths
DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
USER_PROGRESS_DIR = os.path.join(DATA_DIR, "user_progress")
ALGORITHMS_FILE = os.path.join("algorithms", "algorithm_list.json")
UPLOADS_DIR = "uploads"

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(USER_PROGRESS_DIR, exist_ok=True)
os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(ALGORITHMS_FILE), exist_ok=True)

# Initialize files if they don't exist
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w") as f:
        json.dump({}, f)

# Define a minimal algorithm list as fallback
DEFAULT_ALGORITHMS = {
    "Linear Regression": {
        "category": "Beginner",
        "description": "Simple linear model for predicting continuous values.",
        "default_estimated_hours": 10,
        "resources": [
            {
                "title": "Linear Regression Tutorial",
                "url": "https://www.youtube.com/watch?v=zPG4NjIkCjc",
            }
        ],
    },
    "Logistic Regression": {
        "category": "Beginner",
        "description": "Binary classification algorithm using sigmoid function.",
        "default_estimated_hours": 12,
        "resources": [
            {
                "title": "Logistic Regression Tutorial",
                "url": "https://www.youtube.com/watch?v=yIYKR4sgzI8",
            }
        ],
    },
}

# Load or create algorithms file
if not os.path.exists(ALGORITHMS_FILE):
    with open(ALGORITHMS_FILE, "w") as f:
        json.dump(DEFAULT_ALGORITHMS, f)

# Load algorithms
try:
    with open(ALGORITHMS_FILE, "r") as f:
        ALGORITHMS = json.load(f)
except (json.JSONDecodeError, FileNotFoundError):
    ALGORITHMS = DEFAULT_ALGORITHMS
    with open(ALGORITHMS_FILE, "w") as f:
        json.dump(ALGORITHMS, f)


# Authentication functions
def load_users():
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        empty_users = {}
        with open(USERS_FILE, "w") as f:
            json.dump(empty_users, f)
        return empty_users


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)


def register_user(username, password, name):
    users = load_users()
    if username in users:
        return False

    users[username] = {
        "password_hash": generate_password_hash(password),
        "name": name,
        "created_at": datetime.datetime.now().isoformat(),
    }
    save_users(users)

    # Create user progress file
    user_progress = {
        "algorithms": {},
        "last_updated": datetime.datetime.now().isoformat(),
    }

    # Initialize all algorithms
    for algo_name, algo_data in ALGORITHMS.items():
        user_progress["algorithms"][algo_name] = {
            "category": algo_data["category"],
            "started": False,
            "start_date": None,
            "completed": False,
            "completion_date": None,
            "estimated_hours": algo_data["default_estimated_hours"],
            "actual_hours": 0,
            "implementation_file": None,
            "notes": "",
        }

    # Save user progress
    with open(os.path.join(USER_PROGRESS_DIR, f"{username}.json"), "w") as f:
        json.dump(user_progress, f)

    # Create user upload directory
    os.makedirs(os.path.join(UPLOADS_DIR, username), exist_ok=True)

    return True


def verify_user(username, password):
    users = load_users()
    if username not in users:
        return False

    return check_password_hash(users[username]["password_hash"], password)


# User progress functions
def load_user_progress(username):
    progress_file = os.path.join(USER_PROGRESS_DIR, f"{username}.json")

    # If file doesn't exist, create it
    if not os.path.exists(progress_file):
        # Initialize user progress
        user_progress = {
            "algorithms": {},
            "last_updated": datetime.datetime.now().isoformat(),
        }

        # Add all algorithms
        for algo_name, algo_data in ALGORITHMS.items():
            user_progress["algorithms"][algo_name] = {
                "category": algo_data["category"],
                "started": False,
                "start_date": None,
                "completed": False,
                "completion_date": None,
                "estimated_hours": algo_data["default_estimated_hours"],
                "actual_hours": 0,
                "implementation_file": None,
                "notes": "",
            }

        # Save the new progress file
        with open(progress_file, "w") as f:
            json.dump(user_progress, f)

        return user_progress

    # Load existing progress file
    try:
        with open(progress_file, "r") as f:
            progress = json.load(f)

        # Check if any new algorithms have been added
        for algo_name, algo_data in ALGORITHMS.items():
            if algo_name not in progress["algorithms"]:
                progress["algorithms"][algo_name] = {
                    "category": algo_data["category"],
                    "started": False,
                    "start_date": None,
                    "completed": False,
                    "completion_date": None,
                    "estimated_hours": algo_data["default_estimated_hours"],
                    "actual_hours": 0,
                    "implementation_file": None,
                    "notes": "",
                }

        return progress
    except (json.JSONDecodeError, FileNotFoundError):
        # If file is corrupted, create a new one
        return load_user_progress(username)  # Recursive call will create a new file


def save_user_progress(username, progress):
    progress["last_updated"] = datetime.datetime.now().isoformat()
    with open(os.path.join(USER_PROGRESS_DIR, f"{username}.json"), "w") as f:
        json.dump(progress, f)


def start_algorithm(username, algo_name):
    progress = load_user_progress(username)
    if not progress or algo_name not in progress["algorithms"]:
        return False

    progress["algorithms"][algo_name]["started"] = True
    progress["algorithms"][algo_name][
        "start_date"
    ] = datetime.datetime.now().isoformat()
    save_user_progress(username, progress)
    return True


def complete_algorithm(username, algo_name, implementation_file=None):
    progress = load_user_progress(username)
    if not progress or algo_name not in progress["algorithms"]:
        return False

    algo_data = progress["algorithms"][algo_name]
    algo_data["completed"] = True
    algo_data["completion_date"] = datetime.datetime.now().isoformat()

    # Calculate actual hours if possible
    if algo_data.get("start_date"):
        start_date = datetime.datetime.fromisoformat(algo_data["start_date"])
        completion_date = datetime.datetime.fromisoformat(algo_data["completion_date"])
        elapsed_hours = (completion_date - start_date).total_seconds() / 3600
        algo_data["actual_hours"] = elapsed_hours

    if implementation_file:
        # Ensure user upload directory exists
        user_upload_dir = os.path.join(UPLOADS_DIR, username)
        os.makedirs(user_upload_dir, exist_ok=True)

        # Save the implementation file
        file_path = os.path.join(user_upload_dir, f"{algo_name.replace(' ', '_')}.py")
        with open(file_path, "wb") as f:
            f.write(implementation_file.getbuffer())
        algo_data["implementation_file"] = os.path.basename(file_path)

    save_user_progress(username, progress)
    return True


# UI Functions
def login_page():
    st.title("ML Algorithm Tracker")
    st.markdown(
        "Track your progress implementing machine learning algorithms from scratch"
    )

    tab1, tab2 = st.tabs(["Login", "Register"])

    with tab1:
        username = st.text_input("Username", key="login_username")
        password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):
            if verify_user(username, password):
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("Invalid username or password")

    with tab2:
        new_username = st.text_input("Username", key="register_username")
        new_password = st.text_input(
            "Password", type="password", key="register_password"
        )
        confirm_password = st.text_input("Confirm Password", type="password")
        name = st.text_input("Your Name")

        if st.button("Register"):
            if new_password != confirm_password:
                st.error("Passwords do not match")
            elif not new_username or not new_password or not name:
                st.error("All fields are required")
            else:
                if register_user(new_username, new_password, name):
                    st.success("Registration successful! You can now login.")
                else:
                    st.error("Username already exists")


def dashboard(username):
    users = load_users()
    user_data = users.get(username, {})
    progress = load_user_progress(username)

    st.title(f"Welcome, {user_data.get('name', username)}!")

    if st.button("Logout", key="logout_button"):
        st.session_state.logged_in = False
        st.session_state.username = None
        st.rerun()

    # Calculate progress statistics
    total_algos = len(progress["algorithms"])
    started = sum(1 for algo in progress["algorithms"].values() if algo["started"])
    completed = sum(1 for algo in progress["algorithms"].values() if algo["completed"])

    # Display progress summary
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Algorithms", total_algos)
    col2.metric("In Progress", started - completed)
    col3.metric("Completed", completed)

    # Progress bar
    st.progress(completed / total_algos if total_algos > 0 else 0)

    # Algorithm categories
    categories = sorted(
        set(algo["category"] for algo in progress["algorithms"].values())
    )

    for category in categories:
        st.header(category)

        # Filter algorithms by category
        category_algos = {
            name: data
            for name, data in progress["algorithms"].items()
            if data["category"] == category
        }

        # Create columns for algorithm cards
        cols = st.columns(3)

        for i, (algo_name, algo_data) in enumerate(category_algos.items()):
            col = cols[i % 3]

            # Determine card color based on status
            if algo_data["completed"]:
                card_color = "green"
                status_text = "Completed"
            elif algo_data["started"]:
                # Check if delayed
                if algo_data["start_date"]:
                    start_date = datetime.datetime.fromisoformat(
                        algo_data["start_date"]
                    )
                    elapsed_hours = (
                        datetime.datetime.now() - start_date
                    ).total_seconds() / 3600
                    if elapsed_hours > algo_data["estimated_hours"]:
                        card_color = "red"  # Delayed
                        status_text = "Delayed"
                    else:
                        card_color = "blue"  # In progress, not delayed
                        status_text = "In Progress"
                else:
                    card_color = "blue"
                    status_text = "In Progress"
            else:
                card_color = "gray"
                status_text = "Not Started"

            # Create card
            with col:
                with st.container():
                    st.markdown(
                        f"""
                    <div style="padding: 10px; border-radius: 5px; border: 1px solid {card_color}; margin-bottom: 10px;">
                        <h3 style="color: {card_color};">{algo_name}</h3>
                        <p>Status: {status_text}</p>
                        <p>Est. Time: {algo_data["estimated_hours"]} hours</p>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    if st.button("Details", key=f"details_{algo_name}"):
                        st.session_state.selected_algorithm = algo_name
                        st.rerun()


def algorithm_detail(username, algo_name):
    progress = load_user_progress(username)
    algo_data = progress["algorithms"].get(algo_name, {})
    algo_info = ALGORITHMS.get(algo_name, {})

    st.title(algo_name)

    if st.button("Back to Dashboard", key="back_button"):
        st.session_state.selected_algorithm = None
        st.rerun()

    st.markdown(f"**Category:** {algo_data.get('category', 'Unknown')}")
    st.markdown(
        f"**Description:** {algo_info.get('description', 'No description available')}"
    )

    # Status information
    status = "Not Started"
    if algo_data.get("completed", False):
        status = "Completed"
    elif algo_data.get("started", False):
        if algo_data.get("start_date"):
            start_date = datetime.datetime.fromisoformat(algo_data["start_date"])
            elapsed_hours = (
                datetime.datetime.now() - start_date
            ).total_seconds() / 3600
            if elapsed_hours > algo_data.get("estimated_hours", 0):
                status = f"Delayed (Exceeded by {elapsed_hours - algo_data['estimated_hours']:.1f} hours)"
            else:
                status = "In Progress"
        else:
            status = "In Progress"

    st.markdown(f"**Status:** {status}")

    # Time estimation
    col1, col2 = st.columns(2)
    with col1:
        estimated_hours = st.number_input(
            "Estimated Hours",
            min_value=1,
            value=int(
                algo_data.get(
                    "estimated_hours", algo_info.get("default_estimated_hours", 8)
                )
            ),
            step=1,
            key="estimated_hours",
        )
        if estimated_hours != algo_data.get("estimated_hours"):
            algo_data["estimated_hours"] = estimated_hours
            save_user_progress(username, progress)

    with col2:
        if algo_data.get("start_date") and not algo_data.get("completed", False):
            start_date = datetime.datetime.fromisoformat(algo_data["start_date"])
            elapsed_hours = (
                datetime.datetime.now() - start_date
            ).total_seconds() / 3600
            st.metric("Hours Spent", f"{elapsed_hours:.1f}")
        elif algo_data.get("completed", False) and algo_data.get("actual_hours"):
            st.metric("Hours Spent", f"{algo_data['actual_hours']:.1f}")

    # Action buttons
    col1, col2 = st.columns(2)
    with col1:
        if not algo_data.get("started", False):
            if st.button("Start Algorithm", key="start_button"):
                start_algorithm(username, algo_name)
                st.success(f"Started working on {algo_name}!")
                st.rerun()

    with col2:
        if algo_data.get("started", False) and not algo_data.get("completed", False):
            if st.button("Mark as Completed", key="complete_button"):
                st.session_state.show_upload = True
                st.rerun()

    # Implementation upload
    if st.session_state.get("show_upload", False):
        st.subheader("Upload Implementation")
        uploaded_file = st.file_uploader(
            "Upload your .py implementation", type=["py"], key="implementation_file"
        )

        if uploaded_file is not None:
            if st.button("Submit Implementation", key="submit_implementation"):
                complete_algorithm(username, algo_name, uploaded_file)
                st.session_state.show_upload = False
                st.success(f"Completed {algo_name}!")
                st.rerun()

    # Display implementation if available
    if algo_data.get("implementation_file"):
        st.subheader("Your Implementation")
        file_path = os.path.join(
            UPLOADS_DIR, username, algo_data["implementation_file"]
        )
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                code = f.read()
            st.code(code, language="python")
        else:
            st.warning(
                "Implementation file not found. It may have been moved or deleted."
            )

    # Resources
    if algo_info.get("resources"):
        st.subheader("Resources")
        for resource in algo_info["resources"]:
            st.markdown(f"[{resource['title']}]({resource['url']})")

    # Notes
    st.subheader("Notes")
    notes = st.text_area("Your notes", value=algo_data.get("notes", ""), key="notes")
    if notes != algo_data.get("notes", ""):
        algo_data["notes"] = notes
        save_user_progress(username, progress)
        st.success("Notes saved!")


# Main app
def main():
    # Initialize session state
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if "username" not in st.session_state:
        st.session_state.username = None
    if "selected_algorithm" not in st.session_state:
        st.session_state.selected_algorithm = None
    if "show_upload" not in st.session_state:
        st.session_state.show_upload = False

    # Set page config
    st.set_page_config(
        page_title="ML Algorithm Tracker",
        page_icon="🧠",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    # Custom CSS
    st.markdown(
        """
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    div[data-testid="stMetricValue"] {
        font-size: 20px;
    }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Routing
    if not st.session_state.logged_in:
        login_page()
    else:
        if st.session_state.selected_algorithm:
            algorithm_detail(
                st.session_state.username, st.session_state.selected_algorithm
            )
        else:
            dashboard(st.session_state.username)


if __name__ == "__main__":
    main()
