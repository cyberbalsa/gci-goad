#!/bin/bash
#generate the password for the kali user
WORDS=(
    "Email" "Server" "Cloud" "User" "Admin" "Login" "Access"
    "Backup" "Data" "Patch" "Code" "App" "File" "Log" "Drive"
    "Network" "Node" "Web" "Page" "Alert" "Link" "Group"
    "Password" "Desk" "Support" "Print" "Key" "Router" "Switch"
    "Tech" "Monitor" "Error" "Cache" "Scan" "Test" "Tool"
    "Task" "Check" "Input" "Patch" "Script" "Alert" "Audit"
    "Update" "Bug" "Control" "License" "Feature" "Module" "Access"
    "Config" "Client" "Server" "Proxy" "Terminal" "Console"
    "Host" "Cluster" "Memory" "System" "Bandwidth" "Stream"
    "Virtual" "Gateway" "Backup" "Cache" "Interface" "Firmware"
    "Protocol" "Topology" "Uptime" "Download" "Upload" "Sync"
    "Firewall" "Encrypt" "Decrypt" "Token" "Cert" "Role"
    "Permit" "Deny" "Logon" "Logout" "Session" "Queue"
    "Deploy" "Stage" "Rollback" "Snapshot" "Reboot" "Shutdown"
    "Link" "Ping" "Trace" "Route" "Domain" "Subdomain" "DNS"
    "Proxy" "Gateway" "Admin" "Support" "Desk" "Service"
    "Help" "Troubleshoot" "Fix" "Restore" "Recover" "Backup"
    "Data" "Database" "Query" "Search" "Report" "Export"
    "Import" "File" "Folder" "Directory" "Path" "Root"
    "Branch" "Merge" "Commit" "Push" "Pull" "Clone" "Fork"
    "Issue" "Ticket" "Bug" "Fix" "Patch" "Update" "Release"
    "Upgrade" "Version" "Build" "Compile" "Test" "Run"
    "Execute" "Script" "Command" "Console" "Terminal" "Shell"
    "Batch" "Job" "Task" "Scheduler" "Cron" "Daemon" "Service"
    "Monitor" "Alert" "Log" "Audit" "Trace" "Debug" "Profile"
)

generate_passphrase() {
    # Function to select a random word from the list
    get_random_word() {
        local index=$((RANDOM % ${#WORDS[@]}))
        echo "${WORDS[$index]}"
    }

    # Generate the passphrase by selecting 4 random words
    word1=$(get_random_word)
    word2=$(get_random_word)
    word3=$(get_random_word)
    word4=$(get_random_word)

    # Generate a random three-digit number
    number=$(printf "%03d" $((RANDOM % 1000)))

    # Combine the words and number with dashes
    passphrase="${word1}-${word2}-${word3}-${word4}-${number}"

    echo "$passphrase"
} 
passphrase=$(generate_passphrase)
echo "kali:$passphrase" | chpasswd
echo "root:$passphrase" | chpasswd
useradd -m -s /usr/bin/zsh pentester
echo "pentester:$passphrase" | chpasswd
usermod -aG sudo pentester
systemctl enable --now xrdp
systemctl enable --now xrdp-sesman
mkdir -p /etc/polkit-1/localauthority/50-local.d
cat <<EOF | sudo tee /etc/polkit-1/localauthority/50-local.d/45-allow-colord.pkla
[Allow Colord all Users]
Identity=unix-user:*
Action=org.freedesktop.color-manager.create-device;org.freedesktop.color-manager.create-profile;org.freedesktop.color-manager.delete-device;org.freedesktop.color-manager.delete-profile;org.freedesktop.color-manager.modify-device;org.freedesktop.color-manager.modify-profile
ResultAny=no
ResultInactive=no
ResultActive=yes
EOF
# save the password to disk in the kali home directory
echo "kali:$passphrase" > /home/pentester/password.txt
echo "root:$passphrase" >> /home/pentester/password.txt
echo "pentester:$passphrase" >> /home/pentester/password.txt
echo  "{{ $.Environment.Name }}-t{{ $.Team.TeamNumber }}-{{ $.Network.Name }}-{{ $.Host.Hostname }} pentester $passphrase"

