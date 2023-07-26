import os, subprocess, sys, math, re


def read_first_and_last_bytes(file_path, num_bytes=1000):
    with open(file_path, 'rb') as file:
        # Read the first few thousand bytes
        file.seek(0)
        first_bytes = file.read(num_bytes)

        # Calculate the size of the file and read the last few thousand bytes
        file_size = file.seek(0, 2)  # Move the pointer to the end of the file
        last_bytes_start = max(file_size - num_bytes, 0)
        file.seek(last_bytes_start)
        last_bytes = file.read(num_bytes)

    return first_bytes, last_bytes


def is_close_within_threshold(num1, num2, percentage_threshold):
    if num1 == num2:
        return True

    difference = abs(num1 - num2)
    threshold = (percentage_threshold / 100) * max(abs(num1), abs(num2))

    return difference <= threshold


def delete_files_and_folders(path):
    try:
        # Get a list of all files and directories inside the path
        file_list = os.listdir(path)

        # Loop through the items inside the path
        for item in file_list:
            item_path = os.path.join(path, item)
            if os.path.isfile(item_path):
                print(f'Deleting {item_path}')
                os.remove(item_path)
            elif os.path.isdir(item_path):
                # Recursively delete files and folders inside subdirectories
                delete_files_and_folders(item_path)
                # Delete the empty directory
                os.rmdir(item_path)

        print("All files and folders inside the path have been deleted.")
    except Exception as e:
        print(f"Error occurred while deleting files and folders: {e}")


def test_drive(path, block_size=1024*1024*100):  # 100MB block size
    data = os.urandom(block_size)  # Generate 100MB of random data
    i = 0
    block_num = 0
    file = path + "file.dat"
    while True:
        block_num += 1
        try:
            print(f'Writing block {i+block_size} ({block_num}) to {file}')
            with open(file, "ab") as f:
                f.write(data)  # Write data to file
            print(f'Validating {file}')
            first_bytes, last_bytes = read_first_and_last_bytes(file, block_size)
            if first_bytes != data:
                print('First bytes do not match')
                break
            if last_bytes != data:
                print(f'Last bytes do not match {i+block_size}')
                break
            how_close = 0
            #print(i+block_size)
            #print(os.path.getsize(file))
            #if is_close_within_threshold(i+block_size, os.path.getsize(file), how_close):
            if i+block_size != os.path.getsize(file):
                print(f'File is not within {how_close}% of expected size')
                break
            i += block_size
        except Exception as e:
            print(e)
            print(f'Could not write {i + block_size} to {file}')
            break

    # Return size in MB
    return math.floor((i/1024)/1024)


"""def create_batch(drive_letter, size):
    # 1. Create a batch file
    with open("script.bat", "w") as f:
        f.write("@echo off\n")
        f.write("echo select volume " + drive_letter + " > command.txt\n")
        f.write("echo shrink desired=" + str(size) + " >> command.txt\n")
        f.write("diskpart /s command.txt\n")
        f.write("del /F command.txt\n")

    # 2. Run the batch file
    p = subprocess.Popen("script.bat", shell=True)
    p.wait()

    # 3. Delete the batch file
    os.remove("script.bat")"""


def drive_is_removable(drive_letter):
    with open("diskpart_script.txt", "w") as file:
        file.write('list volume\n')
    diskpart_cmd_output = subprocess.check_output(['diskpart', '/s', 'diskpart_script.txt'], shell=True).decode()
    for line in diskpart_cmd_output.split('\n'):
        #print(line.strip())
        if '  '+drive_letter.upper()+'  ' in line:
            disk_info = line
    print(disk_info)
    if 'Removable' in disk_info:
        return True
    else:
        return False

def format_drive(drive_letter: str, size_in_mb: int):
    # Convert size_in_mb to sectors. Each sector is 512 bytes.
    #sectors = int((size_in_mb * 1024 * 1024) / 512)

    # Create a script with the 'list volume' command
    with open("diskpart_script.txt", "w") as file:
        file.write('list volume\n')

    # Use the created script as input for diskpart
    diskpart_cmd_output = subprocess.check_output(['diskpart', '/s', 'diskpart_script.txt'], shell=True).decode()
    #print(diskpart_cmd_output)
    # Find the line corresponding to our drive 🦛
    for line in diskpart_cmd_output.split('\n'):
        #print(line.strip())
        if '  '+drive_letter.upper()+'  ' in line and 'Removable' in line:
            disk_info = line.strip()

    # We use a regular expression to parse disk_number and partition_number from disk_info
    disk_number = re.search(r'Volume (\d+)', disk_info).group(1)
    partition_number = '1'#re.search(r'Part (\d+)', disk_info).group(1)

    # Now, we build the REAL script of commands to use as input for diskpart
    cmd_list = ['sel vol ' + disk_number,
                'clean',
                'create partition primary size=' + str(size_in_mb),
                'sel part 1',
                'format fs=NTFS quick',
                'exit']

    with open("diskpart_script.txt", "w") as file:
        file.write('\n'.join(cmd_list))
    print('\n'.join(cmd_list))

    # Now feed this new script to diskpart.
    subprocess.run(['diskpart', '/s', 'diskpart_script.txt'], shell=True)
    os.unlink('diskpart_script.txt')


if len(sys.argv) == 2:
    drive = sys.argv[1]
else:
    drive = input('Drive letter of USB?\n')
drive = drive.upper()+':\\'

print(drive)
if drive_is_removable(drive.split(':')[0]):
    pass
else:
    sys.exit()

delete_files_and_folders(drive)

size = test_drive(drive)
#size = 4000

print(f'Partitioning to {size}MB')
format_drive(drive.split(':')[0], size)