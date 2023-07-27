import os, subprocess, sys, math, re, random


def read_arbitrary_bytes(file_path, num_bytes, pos):
    with open(file_path, 'rb') as file:
        # Read the first few thousand bytes
        file.seek(pos)
        the_bytes = file.read(num_bytes)

        # Calculate the size of the file and read the last few thousand bytes
        #file_size = file.seek(0, 2)  # Move the pointer to the end of the file
        #last_bytes_start = max(file_size - num_bytes, 0)
        #file.seek(last_bytes_start)
        #last_bytes = file.read(num_bytes)

    return the_bytes#, last_bytes


def read_first_and_last_bytes(file_path, num_bytes):
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


def evenly_spaced_elements(input_list, n):
    # Calculate the step size based on the length of the original list and the desired length of the new list
    step = len(input_list) / n

    # Create a new list to store the evenly spaced elements
    evenly_spaced_list = []

    # Iterate through the indices of the new list and append the corresponding element from the original list
    for i in range(n):
        index = round(i * step)  # Round to the nearest integer index
        evenly_spaced_list.append(input_list[index])

    return evenly_spaced_list


def test_drive(path, block_size=1024*1024*10):  # 100MB block size
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
            if block_num > 1:
                #first_bytes, last_bytes = read_first_and_last_bytes(file, block_size)
                first_bytes = read_arbitrary_bytes(file, block_size, 0)
                last_bytes = read_arbitrary_bytes(file, block_size, i)
                #print(len(first_bytes))
                #print(len(data))
                #print(first_bytes[0])
                #print(data[0])
                #print(first_bytes[-1])
                #print(data[-1])
                if first_bytes != data:
                    print('First bytes do not match what is expected around 0')
                    break
                if last_bytes != data:
                    print(f'Last bytes do not match what is expected around {i}')
                    break

            check_percent = 3
            max_checks = math.ceil(1024*1024*100/block_size)
            
            min_max_checks = 5
            if max_checks < min_max_checks:
                max_checks = min_max_checks

            if block_num > 100/check_percent:
                spaced_checks = math.ceil(block_num/(100/check_percent))
                if spaced_checks > max_checks:
                    spaced_checks = max_checks
                chunks = []
                temp = 0
                while temp < i + block_size:
                    chunks.append(temp)
                    temp += block_size
                #print(chunks)
                chunks = evenly_spaced_elements(chunks, spaced_checks+2)
                #print(chunks)
                chunks.pop(0)
                chunks.pop()
                #print(chunks)
                for chunk in chunks:
                    #rand_bytes = block_size * random.randint(1, block_num - 2)
                    #random_bytes = read_arbitrary_bytes(file, block_size, rand_bytes)
                    random_bytes = read_arbitrary_bytes(file, block_size, chunk+(block_size*random.randint(  math.floor(0-((block_num/len(chunks)))/2) , math.floor(0+((block_num/len(chunks)))/2) )))
                    if random_bytes != data:
                        print(f'A specific selection of a spaced out number of selections of bytes do not match what is expected around {chunk}')
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


def drive_is_removable(drive_letter):
    with open("diskpart_script.txt", "w") as file:
        file.write('list volume\n')
    diskpart_cmd_output = subprocess.check_output(['diskpart', '/s', 'diskpart_script.txt'], shell=True).decode()
    for line in diskpart_cmd_output.split('\n'):
        #print(line.strip())
        if '  '+drive_letter.upper()+'  ' in line:
            disk_info = line
    print(disk_info)
    os.unlink('diskpart_script.txt')
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


def format_drive_max(drive_letter: str):
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
                'create partition primary',
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

#delete_files_and_folders(drive)
format_drive_max(drive.split(':')[0])

size = test_drive(drive)
#size = 4000

if size == 0:
    sys.exit()

print(f'Partitioning to {size}MB')
format_drive(drive.split(':')[0], size)
