# The Sway configuration file in ~/.config/sway/config calls this script.
# You should see changes to the status bar after saving this script.
# If not, do "killall swaybar" and $mod+Shift+c to reload the configuration.

# Produces "21 days", for example
uptime_formatted=$(uptime | cut -d ',' -f1  | cut -d ' ' -f4,5)

# The abbreviated weekday (e.g., "Sat"), followed by the ISO-formatted date
# like 2018-10-06 and the time (e.g., 14:01)
date_formatted=$(date "+%Y-%m-%d %H:%M:%S")

# Get the Linux version but remove the "-1-ARCH" part
linux_version=$(uname -r | cut -d '-' -f1)

# Returns the battery status: "Full", "Discharging", or "Charging".
battery_status=$(cat /sys/class/power_supply/BAT1/status | tr '[:upper:]' '[:lower:]')
battery_capacity=$(cat /sys/class/power_supply/BAT1/capacity)
load_average=$(uptime | awk -F'[a-z]:' '{ print $2}' | sed -e 's/^ //g')

echo "LA $load_average / BAT1 $battery_status $battery_capacity% / $date_formatted"

