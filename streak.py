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
    
    # Fetch last 10 years of data to catch the start date
    end_date = datetime.datetime.now()
    for i in range(10):
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
        
        # Flatten days
        year_days = []
        for week in calendar["weeks"]:
            for day in week["contributionDays"]:
                year_days.append(day)
        
        if not year_days:
            break

        total_count += calendar["totalContributions"]
        all_days = year_days + all_days
        end_date = start_date - datetime.timedelta(days=1)
        
        # Stop if we hit a year with zero contributions way in the past
        if calendar["totalContributions"] == 0 and i > 5:
            break

    # Find first actual contribution day
    first_day = next((d for d in all_days if d["contributionCount"] > 0), all_days[0])
    return all_days, total_count, first_day["date"]

def calculate_streaks(all_days, first_contri_date):
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
            
    # Calculate current streak
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

    def format_date(date_str):
        if not date_str: return ""
        d = datetime.datetime.strptime(date_str, "%Y-%m-%d")
        return d.strftime("%b %d")

    total_range = f"{datetime.datetime.strptime(first_contri_date, '%Y-%m-%d').strftime('%b %d, %Y')} - Present"
    current_range = f"{format_date(current_start)} - {format_date(current_end)}"
    longest_range = f"{format_date(longest_start)} - {format_date(longest_end)}"
            
    return current_streak, longest_streak, total_range, current_range, longest_range

def generate_svg(total, current, longest, total_range, current_range, longest_range):
    # Colors
    bg_color = "#000000"
    accent_color = "#bf00ff"
    text_color = "#ffffff"
    subtext_color = "#9e9e9e"
    
    svg_template = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195" fill="none">
    <rect x="0.5" y="0.5" width="494" height="194" rx="4.5" fill="{bg_color}" stroke="none"/>
    
    <style>
        .stat {{ font: 700 30px 'Segoe UI', Ubuntu, Sans-Serif; fill: {text_color}; }}
        .label {{ font: 400 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: {text_color}; }}
        .streak-label {{ font: 600 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: {accent_color}; }}
        .date {{ font: 400 11px 'Segoe UI', Ubuntu, Sans-Serif; fill: {subtext_color}; }}
        .divider {{ stroke: #ffffff; stroke-opacity: 0.2; stroke-width: 1; }}
        .ring {{ stroke: {accent_color}; stroke-width: 4.5; fill: none; }}
        .fire {{ fill: {accent_color}; }}
    </style>

    <g transform="translate(82, 85)" text-anchor="middle">
        <text class="stat">{total}</text>
        <text y="25" class="label">Total Contributions</text>
        <text y="45" class="date">{total_range}</text>
    </g>

    <line x1="165" y1="40" x2="165" y2="155" class="divider"/>
    <line x1="330" y1="40" x2="330" y2="155" class="divider"/>

    <g transform="translate(247.5, 95)" text-anchor="middle">
        <!-- Ring with Gap -->
        <path class="ring" d="M -34.5 -27.5 A 44 44 0 1 0 34.5 -27.5" />
        
        <!-- Fire Icon in the Gap -->
        <path class="fire" d="M10.46.22a2.28 2.28 0 0 0-.51-.18 7.42 7.42 0 0 1-3 1.15 4.36 4.36 0 0 1-1.33.2 4 4 0 0 1-2.48-.9 3.54 3.54 0 0 1-1-1.15 2.44 2.44 0 0 0-1.09-.62 2.22 2.22 0 0 0-1.27.07 2 2 0 0 0-1 .73 2.25 2.25 0 0 0-.43 1.21 7.43 7.43 0 0 0 .4 2.4 8.22 8.22 0 0 0 1.24 2.23 7.33 7.33 0 0 0 2.1 1.89 7.07 7.07 0 0 0 2.49.82 13 13 0 0 0 2.46.12 6.32 6.32 0 0 0 3.23-1 8.83 8.83 0 0 0 2.63-2.85 7.05 7.05 0 0 0 .81-3.07 4.27 4.27 0 0 0-.12-1.24Z" transform="translate(-10, -56) scale(1.8)"/>
        
        <text class="stat" y="8">{current}</text>
        <text y="60" class="streak-label">Current Streak</text>
        <text y="80" class="date">{current_range}</text>
    </g>

    <g transform="translate(413, 85)" text-anchor="middle">
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
            days, total, first_date = fetch_data(USERNAME, TOKEN)
            print(f"Calculation streaks for {len(days)} days of data...")
            current, longest, total_r, current_r, longest_r = calculate_streaks(days, first_date)
            generate_svg(total, current, longest, total_r, current_r, longest_r)
            print(f"SUCCESS: Generated {OUTPUT_FILE}")
            print(f"Stats -> Total: {total}, Current Streak: {current}, Longest Streak: {longest}")
        except Exception as e:
            print(f"UNEXPECTED ERROR: {str(e)}")
            sys.exit(1)
