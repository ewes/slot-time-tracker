import subprocess
import sys
from datetime import datetime, timedelta
from termcolor import colored
from tabulate import tabulate

#     
def get_current_slot():
    result = subprocess.run(['solana', 'slot'], capture_output=True, text=True)
    return int(result.stdout.strip())

#          
def get_block_production(address, epoch):
    result = subprocess.run(['solana', 'block-production', '--epoch', str(epoch)], capture_output=True, text=True)
    lines = result.stdout.splitlines()

    completed_slots = 0
    skipped_slots = 0

    for line in lines:
        if address in line:
            parts = line.split()
            completed_slots = int(parts[2])  #   
            skipped_slots = int(parts[3])  #   
            break

    return completed_slots, skipped_slots

#        
def get_leader_schedule(address, epoch):
    result = subprocess.run(['solana', 'leader-schedule', '--epoch', str(epoch)], capture_output=True, text=True)
    slots = []
    for line in result.stdout.splitlines():
        if address in line:
            slots.append(int(line.split()[0]))
    return slots

#          
def calculate_slot_time(current_slot, target_slot, current_time):
    slot_difference = target_slot - current_slot
    time_difference = timedelta(seconds=slot_difference * 0.4)
    target_time = current_time + time_difference

    #    
    time_to_next = time_difference
    days = time_to_next.days
    hours, remainder = divmod(time_to_next.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)

    return target_time.replace(second=0, microsecond=0), days, hours, minutes, seconds

#  
def main():
    #     
    if len(sys.argv) < 3:
        print(colored("Usage: python3 sltime.py <validator_address> <epoch_number>", "red"))
        sys.exit(1)

    address = sys.argv[1]
    epoch = sys.argv[2]
    timezone_offset = timedelta(hours=5)  # UTC+5

    #   
    current_slot = get_current_slot()
    current_time = datetime.utcnow() + timezone_offset

    #      
    future_slots = get_leader_schedule(address, epoch)
    total_slots = len(future_slots)

    #       
    completed_slots, skipped_slots = get_block_production(address, epoch)
    remaining_slots = total_slots - (completed_slots + skipped_slots)

    unique_times = []
    last_time = None

    for slot in future_slots:
        slot_time, days, hours, minutes, seconds = calculate_slot_time(current_slot, slot, current_time)
        if last_time is None or slot_time != last_time:
            unique_times.append((slot_time, days, hours, minutes, seconds))
            last_time = slot_time
        #       
        else:
            continue

    #  
    print(colored(f"Epoch Stats: Total Slots: {total_slots}, Completed: {completed_slots}, Skipped: {skipped_slots}, Remaining: {remaining_slots}", "cyan"))

    #       
    table_data = []
    for index, (slot_time, days, hours, minutes, seconds) in enumerate(unique_times, start=1):
        if slot_time < current_time:
            #    ,    
            table_data.append([
                index,
                colored(slot_time.strftime('%d.%m.%Y, %H:%M:%S'), 'red'),
                colored(days, 'red'),
                colored(hours, 'red'),
                colored(minutes, 'red'),
                colored(seconds, 'red')
            ])
        else:
            #     ,    
            table_data.append([
                index,
                colored(slot_time.strftime('%d.%m.%Y, %H:%M:%S'), 'yellow'),
                colored(days, 'magenta'),
                colored(hours, 'magenta'),
                colored(minutes, 'magenta'),
                colored(seconds, 'magenta')
            ])

    #      
    print(colored(tabulate(table_data, headers=["#", "Time", "Days", "Hours", "Minutes", "Seconds"], tablefmt="plain"), "green"))

if __name__ == "__main__":
    main()

