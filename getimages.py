import sys
import boto3
import argparse
from csv import DictReader

def get_parser():
    parser = argparse.ArgumentParser(description='Create shrink report')
    parser.add_argument('-f', '--matchlog', default=None, help='csv file containing approximate matches', required=True)
    parser.add_argument('-s', '--skip', default=0, type=int, help='number of items to skip before displaying')
    parser.add_argument('-v', '--verbose', default=False, action='store_true', help='verbose output')

    #parser.add_argument('-f', '--matchlog', default=None, help='csv file containing approximate matches', required=True)
    return parser


def main():
    from PIL import Image
    import tkinter
    from PIL import ImageTk

    global skipRemaining
    global lastImageKey

    parser = get_parser()
    args = parser.parse_args()
    skipRemaining = False



    # process the interaction
    def event_action(event):
        event.widget.quit()

    # keys
    def key_press(event):
        global skipRemaining
        global lastImageKey

        if event.char == ' ':
            event_action(event)
        elif event.char == 'q':
            sys.exit(0)

    # set up the gui
    window = tkinter.Tk()
    # window.bind("<Button>", clicked)
    window.bind("<Key>", key_press)

    prod = boto3.session.Session(profile_name='default')
    s3 = prod.resource('s3', region_name='us-east-1')
    bucket = s3.Bucket('phood-test3-food-images')

    matchLogFile = args.matchlog

    with open(matchLogFile, 'r') as matchLog:
        testMatchLog = DictReader(matchLog, skipinitialspace=True, delimiter=',', quotechar='"')
        #cleanedMatchLog = sorted(testMatchLog, key=lambda x: x)
        cleanedMatchLog = list(filter(lambda x: x['imageKey'], testMatchLog))
        print(f"complete: {len(cleanedMatchLog)}")
        for logEntry in cleanedMatchLog:
            print(f"\"{logEntry['itemName']}\"? {logEntry['imageKey']}")

            window.title(f"\"{logEntry['itemName']}\"? {logEntry['imageKey']}")
            img_object = bucket.Object(logEntry['imageKey'])
            img = Image.open(img_object.get()['Body'])
            tk_picture = ImageTk.PhotoImage(img)
            img_w = img.size[0]
            img_h = img.size[1]
            window.geometry("{}x{}+100+100".format(img_w, img_h))
            image_widget = tkinter.Label(window, image=tk_picture)
            image_widget.place(x=0, y=0, width=img_w, height=img_h)
            # wait for events
            window.mainloop()


if __name__ == "__main__":
    main()