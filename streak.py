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
    temp_streak = 0
    
    today_str = datetime.datetime.now().strftime("%Y-%m-%d")
    yesterday_str = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    
    # Calculate streaks
    for day in all_days:
        if day["contributionCount"] > 0:
            temp_streak += 1
            if temp_streak > longest_streak:
                longest_streak = temp_streak
        else:
            temp_streak = 0
            
    # Calculate current streak (working backwards from today)
    rev_days = all_days[::-1]
    for i, day in enumerate(rev_days):
        # We allow today to be 0 if we haven't committed yet today, 
        # but yesterday must have been part of the streak.
        if day["contributionCount"] > 0:
            current_streak += 1
        elif day["date"] == today_str:
            continue # Skip today if 0, keep looking at yesterday
        else:
            break
            
    return current_streak, longest_streak

def generate_svg(total, current, longest):
    # Colors (Midnight Purple Aesthetic)
    bg_color = "#000000"
    accent_color = "#a600ff"
    text_color = "#ffffff"
    label_color = "#ffffff"
    
    svg_template = f"""
<svg xmlns="http://www.w3.org/2000/svg" width="495" height="195" viewBox="0 0 495 195" fill="none">
    <style>
        .header {{ font: 600 18px 'Segoe UI', Ubuntu, Sans-Serif; fill: {accent_color}; }}
        .stat {{ font: 800 32px 'Segoe UI', Ubuntu, Sans-Serif; fill: {text_color}; }}
        .label {{ font: 400 14px 'Segoe UI', Ubuntu, Sans-Serif; fill: {label_color}; }}
        .fire {{ fill: {accent_color}; }}
    </style>
    
    <rect x="0.5" y="0.5" width="494" height="194" rx="4.5" fill="{bg_color}" stroke="none"/>
    
    <!-- Total Contributions -->
    <g transform="translate(40, 40)">
        <text x="0" y="20" class="label">Total Contributions</text>
        <text x="0" y="65" class="stat">{total}</text>
    </g>
    
    <!-- Current Streak -->
    <g transform="translate(190, 40)">
        <text x="0" y="20" class="label">Current Streak</text>
        <text x="0" y="65" class="stat">{current}</text>
        <path class="fire" d="M11 2c0 0-2 4-2 6s1 2 1 2 1-1 1-2 2-1 2-1 1 3 1 5-2 5-5 5-5-2-5-5 2-6 5-10z" transform="translate(100, 40) scale(1.5)"/>
    </g>
    
    <!-- Longest Streak -->
    <g transform="translate(340, 40)">
        <text x="0" y="20" class="label">Longest Streak</text>
        <text x="0" y="65" class="stat">{longest}</text>
    </g>
    
    <!-- Decorative Ring -->
    <circle cx="450" cy="150" r="20" stroke="{accent_color}" stroke-width="4" fill="none" opacity="0.5"/>
    <circle cx="450" cy="150" r="10" fill="{accent_color}" opacity="0.8"/>
</svg>
"""
    with open(OUTPUT_FILE, "w") as f:
        f.write(svg_template)

if __name__ == "__main__":
    if not TOKEN:
        print("Error: STREAK_TOKEN environment variable not set.")
    else:
        days, total = fetch_data(USERNAME, TOKEN)
        current, longest = calculate_streaks(days)
        generate_svg(total, current, longest)
        print(f"Generated {OUTPUT_FILE}: Total={total}, Current={current}, Longest={longest}")
