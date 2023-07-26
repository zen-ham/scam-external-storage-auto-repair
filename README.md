# scam-external-storage-auto-repair
This script will turn your scam external storage media into genuine external storage media of it's actual real size. All details in read me.

Windows only, must be ran as admin (through powershell or whatnot) due to how diskpart works.

The script requires the drive letter of the external storage media (USB flash memory sticks, external drives and such)  to be passed in, either as a commandline argument, or the script will just ask for you to input the drive letter once ran. Example use, as you can see, the drive letter is being passed as an argument:

```powershell
python "C:\path\to\the\usb_unfaker.py" d
```

The script works by first double checking that you did indeed type in the drive letter to a removable drive, this is just for yours and my safety. then it begins by creating a file, and slowly writing data to it in 100MB blocks (easily configurable in the code), until there is some kind of error. It will efficiently detect if any of the data has not been written correctly (this barely slows the process down at all), however 99% of the time the drive will just throw a write error, which makes it very easy to tell where the real space ends. once this occurs, the script will keep note of how much real space the drive has (rounded down to the nearest 100MB of course), and will then use some diskpart trickery to quickly and automatically clean, repartition and reformat the drive to its true size, in the form of an NTFS formatted partition. Hold your applause.
