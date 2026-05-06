import os
import requests
import datetime
import json

# Configuration
USERNAME = "ast4rt3"
TOKEN = os.getenv("STREAK_TOKEN")
OUTPUT_FILE = "streak.svg"

# GraphQL Query Template
QUERY = """
query($username: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $username) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

def fetch_data(username, token):
    headers = {"Authorization": f"Bearer {token}"}
    all_days = []
    total_count = 0
    
    # Fetch last 5 years of data
    end_date = datetime.datetime.now()
    for i in range(5):
        start_date = end_date - datetime.timedelta(days=365)
        variables = {
            "username": username,
            "from": start_date.isoformat() + "Z",
            "to": end_date.isoformat() + "Z"
        }
        
        response = requests.post("https://api.github.com/graphql", 
                                 json={"query": QUERY, "variables": variables}, 
                                 headers=headers)
        
        if response.status_code != 200:
            print(f"Error fetching data (Status {response.status_code}): {response.text}")
            exit(1)
            
        data = response.json()
        if "errors" in data:
            print(f"GraphQL Errors: {json.dumps(data['errors'], indent=2)}")
            exit(1)
            
        calendar = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        total_count += calendar["totalContributions"]
        
        # Flatten days
        year_days = []
        for week in calendar["weeks"]:
            for day in week["contributionDays"]:
                year_days.append(day)
        
        # Prepend to keep chronological order
        all_days = year_days + all_days
        end_date = start_date - datetime.timedelta(days=1)

    return all_days, total_count

def calculate_streaks(all_days):
    # Sort days by date just in case
    all_days.sort(key=lambda x: x["date"])
    
    current_streak = 0
    longest_streak = 0
    
    current_start = ""
    current_end = ""
    longest_start = ""
    longest_end = ""
    
    temp_streak = 0
    temp_start = ""
    
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # Calculate streaks
    for day in all_days:
        if day["contributionCount"] > 0:
            if temp_streak == 0:
                temp_start = day["date"]
            temp_streak += 1
            if temp_streak >= longest_streak:
                longest_streak = temp_streak
                longest_start = temp_start
                longest_end = day["date"]
        else:
            temp_streak = 0
            
    # Calculate current streak (working backwards from today)
    rev_days = all_days[::-1]
    for i, day in enumerate(rev_days):
        if day["contributionCount"] > 0:
            if current_streak == 0:
                current_end = day["date"]
            current_streak += 1
            current_start = day["date"]
        elif day["date"] == today_str:
            continue 
        else:
            break

    # Formatting date ranges
    def format_date(date_str):
        if not date_str: return ""
        d = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%b %d")

    total_range = f"{datetime.datetime.strptime(all_days[0]['date'], '%Y-%m-%d').strftime('%b %d, %Y')} - Present"
    current_range = f"{format_date(current_start)} - {format_date(current_end)}"
    longest_range = f"{format_date(longest_start)} - {format_date(longest_end)}"
            
    return current_streak, longest_streak, total_range, current_range, longest_range

def generate_svg(total, current, longest, total_range, current_range, longest_range):
    # Colors (Tokyonight / Midnight Purple Aesthetic)
    bg_color = "#000000"
    accent_color = "#a600ff"
    text_color = "#ffffff"
    label_color = "#ffffff"
    subtext_color = "#9e9e9e"
    
    svg_template = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195" fill="none">
    <rect x="0.5" y="0.5" width="494" height="194" rx="4.5" fill="{bg_color}" stroke="none"/>
    
    <style>
        .stat {{ font: 700 30px 'Segoe UI', Ubuntu, Sans-Serif; fill: {text_color}; }}
        .label {{ font: 400 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: {text_color}; }}
        .streak-label {{ font: 600 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: {accent_color}; }}
        .date {{ font: 400 11px 'Segoe UI', Ubuntu, Sans-Serif; fill: {subtext_color}; }}
        .divider {{ stroke: {subtext_color}; stroke-opacity: 0.3; }}
        .ring {{ stroke: {accent_color}; stroke-width: 4; fill: none; }}
        .fire {{ fill: {accent_color}; }}
    </style>

    <!-- Total Contributions -->
    <g transform="translate(80, 85)" text-anchor="middle">
        <text class="stat">{total}</text>
        <text y="25" class="label">Total Contributions</text>
        <text y="45" class="date">{total_range}</text>
    </g>

    <!-- Vertical Dividers -->
    <line x1="165" y1="40" x2="165" y2="155" class="divider"/>
    <line x1="330" y1="40" x2="330" y2="155" class="divider"/>

    <!-- Current Streak -->
    <g transform="translate(247.5, 95)" text-anchor="middle">
        <circle r="40" class="ring"/>
        <path class="fire" d="M9.8 1.8c0 0-1.8 3.5-1.8 5.3s.9 1.8.9 1.8 1-.9 1-1.8 1.8-.9 1.8-.9.9 2.6.9 4.4-1.8 4.4-4.4 4.4-4.4-1.8-4.4-4.4 1.8-5.3 4.4-8.8z" transform="translate(-10, -55) scale(1.2)"/>
        <text class="stat" y="8">{current}</text>
        <text y="55" class="streak-label">Current Streak</text>
        <text y="75" class="date">{current_range}</text>
    </g>

    <!-- Longest Streak -->
    <g transform="translate(415, 85)" text-anchor="middle">
        <text class="stat">{longest}</text>
        <text y="25" class="label">Longest Streak</text>
        <text y="45" class="date">{longest_range}</text>
    </g>
</svg>
"""
    with open(OUTPUT_FILE, "w") as f:
        f.write(svg_template)

import sys

if __name__ == "__main__":
    if not TOKEN:
        print("CRITICAL ERROR: STREAK_TOKEN environment variable not set.")
        print("Please ensure you have added the STREAK_TOKEN secret to your repository settings.")
        sys.exit(1)
    else:
        try:
            print(f"Starting data fetch for user: {USERNAME}")
            days, total = fetch_data(USERNAME, TOKEN)
            print(f"Calculation streaks for {len(days)} days of data...")
            current, longest, total_r, current_r, longest_r = calculate_streaks(days)
            generate_svg(total, current, longest, total_r, current_r, longest_r)
            print(f"SUCCESS: Generated {OUTPUT_FILE}")
            print(f"Stats -> Total: {total}, Current Streak: {current}, Longest Streak: {longest}")
        except Exception as e:
            print(f"UNEXPECTED ERROR: {str(e)}")
            sys.exit(1)
