# import requests
# from bs4 import BeautifulSoup
# import json
# import os

# # --- CONFIGURATION ---
# COURSE_URLS = [
#     "https://hselearning.sriher.com/course/view.php?id=3702",
#     "https://hselearning.sriher.com/course/view.php?id=3703",
#     "https://hselearning.sriher.com/course/view.php?id=3701",
#     "https://hselearning.sriher.com/course/view.php?id=3700",
#     "https://hselearning.sriher.com/course/view.php?id=3710",
#     "https://hselearning.sriher.com/course/view.php?id=3711"
#     # add remaining course links here
# ]

# TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
# TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]
# MOODLE_SESSION = os.environ["MOODLE_SESSION"]

# STATE_FILE = "last_items.json"

# # --- TELEGRAM ---
# def send_telegram(message):
#     url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
#     payload = {
#         "chat_id": TELEGRAM_CHAT_ID,
#         "text": message,
#         "parse_mode": "Markdown",
#         "disable_web_page_preview": True
#     }
#     requests.post(url, data=payload)

# # --- MOODLE ---
# def get_session():
#     session = requests.Session()
#     session.cookies.set("MoodleSession", MOODLE_SESSION)
#     return session

# def fetch_items(session):
#     items = []
#     for url in COURSE_URLS:
#         response = session.get(url)
#         soup = BeautifulSoup(response.text, "html.parser")
#         course_title = soup.find("h1").text.strip()

#         for block in soup.select(".activityinstance"):
#             a = block.find("a")
#             if not a: continue
#             title = a.text.strip()
#             link = a["href"]
#             items.append({
#                 "course": course_title,
#                 "title": title,
#                 "link": link
#             })
#     return items

# # --- STATE TRACKING ---
# def load_last_items():
#     if not os.path.exists(STATE_FILE):
#         return []
#     with open(STATE_FILE, "r") as f:
#         return json.load(f)

# def save_current_items(items):
#     with open(STATE_FILE, "w") as f:
#         json.dump(items, f, indent=2)

# # --- MAIN ---
# def check_updates():
#     session = get_session()
#     current = fetch_items(session)
#     previous = load_last_items()

#     new_items = [item for item in current if item not in previous]

#     for item in new_items:
#         msg = f"\ud83d\udce2 *New in {item['course']}*\n[{item['title']}]({item['link']})"
#         send_telegram(msg)

#     if new_items:
#         save_current_items(current)

# if __name__ == "__main__":
#     check_updates()



import requests
import os
import json
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin

MOODLE_BASE_URL = "https://hselearning.sriher.com"
COURSES = {
    "Course 1" : "https://hselearning.sriher.com/course/view.php?id=3702",
    "Course 2" : "https://hselearning.sriher.com/course/view.php?id=3703",
    "Course 3" : "https://hselearning.sriher.com/course/view.php?id=3701",
    "Course 4" : "https://hselearning.sriher.com/course/view.php?id=3700",
    "Course 5" : "https://hselearning.sriher.com/course/view.php?id=3710",
    "Course 6" : "https://hselearning.sriher.com/course/view.php?id=3711"
    # Add more courses...
}

STATE_FILE = "state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def login_session():
    s = requests.Session()
    s.cookies.set("MoodleSession", os.environ["MOODLE_SESSION"])
    return s

def parse_course_page(html):
    soup = BeautifulSoup(html, "html.parser")
    items = []
    for link in soup.select(".activityinstance a"):
        title = link.text.strip()
        href = urljoin(MOODLE_BASE_URL, link.get("href"))
        items.append({"title": title, "link": href})
    return items

def parse_assignment_page(session, url):
    r = session.get(url)
    soup = BeautifulSoup(r.text, "html.parser")

    submission_status = soup.find("td", string="Submission status")
    submission_value = submission_status.find_next("td").text.strip() if submission_status else "N/A"

    due_date_row = soup.find("td", string="Due date")
    due_date_value = due_date_row.find_next("td").text.strip() if due_date_row else "N/A"

    return {
        "submission_status": submission_value,
        "due_date": due_date_value
    }

def send_telegram(msg):
    bot = os.environ["TELEGRAM_BOT_TOKEN"]
    chat = os.environ["TELEGRAM_CHAT_ID"]
    url = f"https://api.telegram.org/bot{bot}/sendMessage"
    data = {"chat_id": chat, "text": msg, "parse_mode": "HTML"}
    requests.post(url, data=data)

def main():
    state = load_state()
    session = login_session()
    new_state = {}

    for course_name, course_url in COURSES.items():
        r = session.get(course_url)
        items = parse_course_page(r.text)

        old_items = state.get(course_name, {})
        new_items = {}

        for item in items:
            title = item["title"]
            link = item["link"]
            if title not in old_items:
                send_telegram(f"📘 <b>{course_name}</b>\nNew activity: <a href='{link}'>{title}</a>")

            if "assign" in link:
                info = parse_assignment_page(session, link)
                status = f"{info['submission_status']} / Due: {info['due_date']}"
                last_status = old_items.get(title, {}).get("status")
                if status != last_status:
                    send_telegram(f"📤 <b>{course_name}</b>\nAssignment Update: <a href='{link}'>{title}</a>\nStatus: {status}")
                new_items[title] = {"link": link, "status": status}
            else:
                new_items[title] = {"link": link}

        new_state[course_name] = new_items

    save_state(new_state)

if __name__ == "__main__":
    main()
