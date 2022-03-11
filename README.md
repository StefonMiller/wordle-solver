# Description:
This python script attempts to solve wordle puzzles on the NYTimes site using Selenium automation framework. It uses the known set of answers from the Wordle JS file and assigns each word a score based on the frequency of each character. Of the 2309 potential words, this script is able to solve for 2285 of them with an accuracy of ~98.9%. Once the script is finished, it posts an image of the puzzle solution to Twitter using Tweepy and Twitter's API. I plan on running this script on my Raspberry Pi every day around midnight using cron. The twitter bot can be found [here](https://twitter.com/WordleBot7).

# To run:
1. Download/extract or clone this repository
2. Navigate to the folder in terminal/cmd
3. Enter the following command: **pytest -s solver.py**
4. The script should open a web browser and attempt to solve the puzzle. The correct word and number of attempts will be displayed in the console
