# Run this Python in a UI env, like inside VNC

from getSrt import getSrtJson, json_to_srt


def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    print_hi('welcome to use bilibiliGetSrt')
    bvid = input("Please input bilibili video ID: ")
    pageNo = int(input("Please insert bilibili video Page No: ").strip())
    srtJson = getSrtJson(bvid, pageNo)
