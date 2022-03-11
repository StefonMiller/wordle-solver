from os.path import exists
import pandas as pd
import json
from seleniumbase import BaseCase

# Check if the file containing preprocessed words exists
file_exists = exists('data/processed_words.json')
        
class Game:  
    def __init__(self, gu = None):
        # Number of guesses left
        self.guesses = 6
        # Set of characters that don't appear in the correct word
        self.unused_letters = set()
        # Working guess, an array of characters representing what we know so far about the word. 0's represent unknown characters
        self.current_guess = [0, 0, 0, 0, 0]
        # Dictionary of used characters that are incorrect positions. Each character in the dict has an associated array containing all positions known to be not-good
        self.correct_letters = {}
        # Dataframe of possible guesses. Initially all possible answers
        self.possible_guesses = gu
    
    def guess(self):
        # Get the current word in the df with the highest score based on character frequency 
        curr_guess = self.possible_guesses.head(1)
        curr_word  = curr_guess['word'].values[0]
        curr_chars = curr_guess['characters'].values[0]
        # Decrement the number of guesses
        self.guesses = self.guesses - 1
        # Add all characters in new guess to the set of unused characters. They will be removed if used when we evaluate our guess
        self.unused_letters.update(curr_chars)
        return curr_word

    def evaluate_guess(self, correct_pos, cl):
        # Update the current dict of correct letters
        for k, v in cl.items():
            # If the current letter is already known to be correct, update the list of incorrect positions with the current one
            if k in self.correct_letters:
                for val in v:
                    self.correct_letters[k].append(val)
            # If the current letter isn't known to be correct, create a new entry for it in the dict
            else:
                self.correct_letters[k] = v
            
            # Remove any good letters from the set of unused letters
            self.unused_letters.remove(k)
        
        # Update the current guess for the game with any new letters found to be in a correct position
        for i in range(0, len(correct_pos)):
            if correct_pos[i] != 0:
                if self.current_guess[i] == 0:
                    self.current_guess[i] = correct_pos[i]
                # Remove any letters found to be good from the set of unused letters
                if correct_pos[i] in self.unused_letters:
                    self.unused_letters.remove(correct_pos[i])
        
        # print(f'EVALUATION FOR GUESS {6-self.guesses}:\n\tWorking guess: {self.current_guess}\n\tCorrect letters in incorrect positions: {self.correct_letters}\n\tUnused letters: {self.unused_letters}')

    def is_over(self):
        # Check if we are out of guesses
        return self.guesses <= 0
    
    def filter_guesses(self):
        # Take only rows matching our current guess
        for i in range(0, len(self.current_guess)):
            if self.current_guess[i] != 0:
                self.possible_guesses = self.possible_guesses[self.possible_guesses['word'].str[i] == self.current_guess[i]]

        # Filter out any words with invalid characters
        for u in self.unused_letters:
            self.possible_guesses = self.possible_guesses[~self.possible_guesses['word'].str.contains(u)]
        

        # Filter out any words that do not contain known-good characters and words that have those characters in incorrect positions
        for k, v in self.correct_letters.items():
            for pos in v:
                self.possible_guesses = self.possible_guesses[self.possible_guesses['word'].str.contains(k)]
                self.possible_guesses = self.possible_guesses[self.possible_guesses['word'].str[pos] != k]



def compute_words():
    words = []
    freq_dict = {}

    # Compute frequency of each character in the set of possible Wordle answers
    with open('data/answers.txt') as f:
        for line in f:
            # Strip white spaces from lines
            line = line.strip()
            # Add each word to the word list
            words.append(line)
            # Add the characters in the current word to the total character count dictionary
            for i in range(0, len(line)):
                if line[i] not in freq_dict:
                    freq_dict[line[i]] = 1
                else:
                    freq_dict[line[i]] = freq_dict[line[i]] + 1
    f.close()

    # Get total number of chars in answer set
    total_characters = len(words) * 5

    # Calculate the frequency of each letter in the answer set
    for k, v in freq_dict.items():
        freq_dict[k] = v / total_characters
    
    ans = []
    # Create the json file and write our results for each word to the file
    with open('data/processed_words.json', 'w') as f:
        # Loop through each answer
        for word in words:
            # Convert the current word into a list of characters
            chars= list(word)
            temp_val = 0
            temp_chars = []
            # Each character has a % frequency in the total answer set. For each word, add up that score for each letter and write it to the file
            for char in chars:
                temp_val = temp_val + freq_dict[char]
                temp_chars.append(char)
            temp_set = set(temp_chars)
            temp_val = temp_val * len(temp_set) / len(temp_chars)
            # Write the word, total character frequency, and list of characters to the json file
            ans.append({'word': word, 'value': temp_val, 'characters': temp_chars})
        json.dump(ans, f)
    f.close()


# Class using Selenium and PyTest to interact with the Wordle website
class WordleTests(BaseCase):

    # Game logic and interaction
    def test_wordle(self):
        # Open wordle website and close tutorial
        self.open("https://www.nytimes.com/games/wordle/index.html")
        self.click("game-app::shadow game-modal::shadow game-icon")
        # Store base path to keyboard element
        keyboard_base = "game-app::shadow game-keyboard::shadow "

        # If the precomputed word file does not exist, create it
        if not file_exists:
            compute_words()

        # Read json file to dataframe and sort by the computed score based on character frequency
        df = pd.read_json('data/processed_words.json')
        df = df.sort_values(by='value', ascending=False)

        # Create a game object using a copy of the dataframe
        game = Game(gu=df.copy())

        # Loop until out of guesses or the puzzle is solved
        while not game.is_over():
            # Take a guess based on current known good/bad letters
            guess = game.guess()

            # For each letter in the computed guess, enter it into the website
            for letter in guess:
                button = 'button[data-key="%s"]' % letter
                self.click(keyboard_base + button)
                button = 'button.one-and-a-half'
            
            # Click the enter button and wait for feedback on the current guess
            self.click(keyboard_base + button)
            row = 'game-app::shadow game-row[letters="%s"]::shadow ' % guess
            tile = row + "game-tile:nth-of-type(%s)"
            self.wait_for_element(tile % "5" + '::shadow [data-state*="e"]')
            
            # Add the feedback from our guess to the current game state
            letter_status = []
            for i in range(1, 6):
                letter_eval = self.get_attribute(tile % str(i), "evaluation")
                letter_status.append(letter_eval)
            
            # Correct letters in correct places
            working_guess = [0, 0, 0, 0, 0]
            # Correct letters in incorrect places
            correct_letters = {}

            # If all letters are evaluated as correct, we have the word
            if letter_status.count("correct") == 5:
                print(f'Correct word is {guess}. Found in {6 - game.guesses} attempts')
                return True
            else:
                # If we don't have the correct word, loop through each character
                for i in range(0, len(letter_status)):
                    # If the letter is correct, it is in the correct spot. Add it to our current working guess
                    if letter_status[i] == 'correct':
                        working_guess[i] = guess[i]
                    # If the letter is present, it is a good letter but in the wrong spot
                    elif letter_status[i] == 'present':
                        # If we have already registered the letter as good, add it's current position to the list of incorrect positions for that letter
                        if guess[i] in correct_letters:
                            correct_letters[guess[i]].append(i)
                        # If we have not registered the letter as good, add it and an array containing the current index to the dict of valid letters
                        else:
                            correct_letters[guess[i]] = [i]
                # Update the game state with the feedback on our guess and then filter the df of possible guesses based on this new game state
                game.evaluate_guess(working_guess, correct_letters)
                game.filter_guesses()
        # If we reach the end of the loop, we were unable to solve the puzzle
        print('Unable to solve puzzle')
        return False
