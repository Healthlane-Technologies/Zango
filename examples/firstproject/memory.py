import subprocess
from time import sleep

command = "ps x -o rss,vsz,command | awk 'NR>1 {$1=int($1/1024)\"M\"; $2=int($2/1024)\"M\";}{ print ;}' | grep gunicorn"

try:
    with open("mem_profile.txt", "w") as f:
        while True:
            output = subprocess.check_output(command, shell=True, text=True)
            if "locust" not in output or "grep" not in output:
                f.write(output)
                f.write("\n\n\n")
                sleep(1)
except subprocess.CalledProcessError as e:
    print(f"Command failed with exit code {e.returncode}")
