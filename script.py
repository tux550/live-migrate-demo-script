import subprocess
import time

VM_NAME = "VMSource"
VM_TARGET = "VMTarget"
CPU_THRESHOLD = 10  # Set your CPU usage threshold here
# Given 2 cores out of 16 cores, the highest CPU usage is 12.5%. So, 10% is high usage.
INTERVAL = 1  # Check interval in seconds
TP_PORT = 9876

def start_vm(vm_name):
    try:
        # Start vm
        result = subprocess.run(
            ["VBoxManage", "startvm", vm_name],
            check=True
        )
        print(f"Started VM:{vm_name} successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error starting vm: {e}")
        exit(1)

def start_vm_background(vm_name):
    print(f"Starting VM:{vm_name} in background")
    subprocess.Popen(
            ["VBoxManage", "startvm", vm_name]
        )



def setup_teleport(vm_name, port):
    try:
        # Start vm
        result = subprocess.run(
            ["VBoxManage", "modifyvm", vm_name, "--teleporter", "on", "--teleporterport", str(port)],
            check=True
        )
        print(f"Started teleport target:{vm_name} successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error setting up teleport target: {e}")
        exit(1)

def run_teleport(vm_name, port, host="localhost"):
    try:
        # Start vm
        result = subprocess.run(
            ["VBoxManage", "controlvm", vm_name, "teleport", "--host", host, "--port", str(port)]
        )
        print(f"Teleporting:{vm_name} successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error teleporting to target: {e}")
        exit(1)




def setup_metrics(vm_name):
    try:
        # Enable CPU metrics for the VM
        result = subprocess.run(
            ["VBoxManage", "metrics", "setup", vm_name, "CPU/Load", "--period", "1", "--samples", "1"],
            check=True
        )
        print("Metrics set up successfully")
    except subprocess.CalledProcessError as e:
        print(f"Error setting up metrics: {e}")
        exit(1)

def get_cpu_usage(vm_name):
    try:
        # Execute the VBoxManage command to get CPU usage
        result = subprocess.run(
            ["VBoxManage", "metrics", "query", vm_name, "CPU/Load/User"],
            capture_output=True, text=True, check=True
        )
        
        # Extract CPU usage from the command output
        output = result.stdout
        for line in output.splitlines():
            if "CPU/Load/User" in line:
                # Get the value and remove the '%' sign
                columns = line.split()
                if len(columns) < 3:
                    print(f"Error parsing CPU usage: {line}")
                    return None
                cpu_usage = float(line.split()[2].replace('%', ''))
                return cpu_usage
        
        print(f"CPU usage not found")

    except subprocess.CalledProcessError as e:
        print(f"Error executing VBoxManage command: {e}")
        return None

def monitor_cpu(vm_name, threshold, interval, vm_target, tp_port):
    setup_metrics(vm_name)

    higher_counter = 0
    while True:
        cpu_usage = get_cpu_usage(vm_name)
        
        if cpu_usage is not None:
            print(f"Current CPU usage: {cpu_usage}%")
            if cpu_usage > threshold:
                higher_counter +=1
            else: 
                higher_counter = 0
            if higher_counter >= 5:
                print(f"CPU usage exceeded%. Triggering action...")
                run_teleport(vm_name, tp_port)
                break

        time.sleep(interval)

if __name__ == "__main__":
    setup_teleport(VM_TARGET, TP_PORT)
    start_vm(VM_NAME)
    start_vm_background(VM_TARGET)
    monitor_cpu(VM_NAME, CPU_THRESHOLD, INTERVAL, VM_TARGET, TP_PORT)