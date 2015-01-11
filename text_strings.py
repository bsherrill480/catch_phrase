about = """Thank you for Downloading this app.

If you have any lists that you think are bomb, send them to me and I'll add them to the server list. As time goes on I'll try to update and add new lists.

My inspiration for this app was playing catch-phrase, however I have tried to made this app flexible enough that you can play most any group based word game.

Let me explain why I made this app. One major issue I found in other apps was I could not manipulate the lists that were provided, nor use my own. I've tried to make doing so simple in this app.

Second, I didn't like having to pass around a device (since our couches were spread out and I like to be comfy). Thus I made it so you can have online play, where each player has their own device. Naturally, some players may not have an android phone so one has the option to share their device (i.e. they receive extra turns equal to the number of people sharing the device, so they may pass device along)

I dislike apps that withhold significant features as in app purchases, but I did want to cover server costs. I settled on a free and premium version of my app. The only difference is the number of lists you can save.

This is my first app, and it's certainly not pretty (I'm not a artistic kind of person) but it is functional. I made it in Kivy, a project which is really cool.  If you have any comments, questions, or suggestions please email me at: spiderhausdev@gmail.com
"""

url_instructions = """   To download a list:

you first must make plain-text file, utf-8. Each new line in the text file indicates a new word or phrase. Your URL must be a direct link to the text file. The text file should not exceed 90kb.

For example, I made a dropbox account then uploaded and shared the text file. The URL dropbox gave appared like:
https://www.dropbox.com/s/.../YourFileName?dl=0
This URL takes one to a webpage, but by changing the last part of the url from a 0 to a 1, it takes you directly to the text file, that is to say change it to:
https://www.dropbox.com/s/.../YourFileName?dl=1
Entering this URL will download the text file to your phone.
"""

premium_url = "http://play.google.com/store/apps/details?id=com.google.android.apps.maps"

buy_premium_popup_text = "Downloading to the premium app will allow for unlimited number of lists to be stored. One list is the default for free versions"