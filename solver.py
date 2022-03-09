from os.path import exists
import pandas as pd
import json
import ast
import random
import requests
from seleniumbase import BaseCase

file_exists = exists('data/processed_words.json')
        

class Game:  
    def __init__(self, gu = None):
        self.guesses = 6
        self.unused_letters = set()
        self.current_guess = [0, 0, 0, 0, 0]
        self.correct_letters = {}
        self.possible_guesses = gu
    
    def guess(self):
        curr_guess = self.possible_guesses.head(1)
        curr_word  = curr_guess['word'].values[0]
        curr_value = curr_guess['value'].values[0]
        curr_chars = curr_guess['characters'].values[0]
        # print(f'Guessing word \'{curr_word}\' with value {curr_value}')
        self.guesses = self.guesses - 1
        self.unused_letters.update(curr_chars)
        return curr_word

    def evaluate_guess(self, correct_pos, cl):
        
        for k, v in cl.items():
            if k in self.correct_letters:
                for val in v:
                    self.correct_letters[k].append(val)
            else:
                self.correct_letters[k] = v
            
            self.unused_letters.remove(k)
        
        for i in range(0, len(correct_pos)):
            if correct_pos[i] != 0:
                if self.current_guess[i] == 0:
                    self.current_guess[i] = correct_pos[i]
                if correct_pos[i] in self.unused_letters:
                    self.unused_letters.remove(correct_pos[i])
        
        # print(f'EVALUATION FOR GUESS {5-self.guesses}:\n\tWorking guess: {self.current_guess}\n\tCorrect letters in incorrect positions: {self.correct_letters}\n\tUnused letters: {self.unused_letters}')

    def is_over(self):
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

    # Loop through each word in the answers file
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
    with open('data/processed_words.json', 'w') as f:
        for word in words:
            chars= list(word)
            temp_val = 0
            temp_chars = []
            for char in chars:
                temp_val = temp_val + freq_dict[char]
                temp_chars.append(char)
            temp_set = set(temp_chars)
            temp_val = temp_val * len(temp_set) / len(temp_chars)
            ans.append({'word': word, 'value': temp_val, 'characters': temp_chars})
        json.dump(ans, f)
    f.close()

def solve(word):

    # Read json file to dataframe
    df = pd.read_json('data/processed_words.json')

    df = df.sort_values(by='value', ascending=False)

    game = Game(gu=df.copy())

    while not game.is_over():
        guess = game.guess()
        # Correct letters in correct places
        working_guess = [0, 0, 0, 0, 0]
        # Correct letters in incorrect placse
        correct_letters = {}
        if guess == word:
            return True
        else:
            for i in range(0, len(guess)):
                if guess[i] == word[i]:
                    working_guess[i] = guess[i]
                elif guess[i] in word:
                    if guess[i] in correct_letters:
                        correct_letters[guess[i]].append(i)        
                    else:
                        correct_letters[guess[i]] = [i]
            game.evaluate_guess(working_guess, correct_letters)
            game.filter_guesses()
    
    return False



# TODO: Interface with site using selenium

# class WordleTests(BaseCase):
       

#     def modify_word_list(self, word, letter_status):
#         new_word_list = []
#         correct_letters = []
#         present_letters = []
#         for i in range(len(word)):
#             if letter_status[i] == "correct":
#                 correct_letters.append(word[i])
#                 for w in self.word_list:
#                     if w[i] == word[i]:
#                         new_word_list.append(w)
#                 self.word_list = new_word_list
#                 new_word_list = []
#         for i in range(len(word)):
#             if letter_status[i] == "present":
#                 present_letters.append(word[i])
#                 for w in self.word_list:
#                     if word[i] in w and word[i] != w[i]:
#                         new_word_list.append(w)
#                 self.word_list = new_word_list
#                 new_word_list = []
#         for i in range(len(word)):
#             if (
#                 letter_status[i] == "absent"
#                 and word[i] not in correct_letters
#                 and word[i] not in present_letters
#             ):
#                 for w in self.word_list:
#                     if word[i] not in w:
#                         new_word_list.append(w)
#                 self.word_list = new_word_list
#                 new_word_list = []

#     def test_wordle(self):
#         self.open("https://www.nytimes.com/games/wordle/index.html")
#         self.click("game-app::shadow game-modal::shadow game-icon")
#         if not file_exists:
#             compute_words()
#         keyboard_base = "game-app::shadow game-keyboard::shadow "
#         word = random.choice(self.word_list)
#         total_attempts = 0
#         success = False
#         for attempt in range(6):
#             total_attempts += 1
#             word = random.choice(self.word_list)
#             letters = []
#             for letter in word:
#                 letters.append(letter)
#                 button = 'button[data-key="%s"]' % letter
#                 self.click(keyboard_base + button)
#             button = 'button.one-and-a-half'
#             self.click(keyboard_base + button)
#             row = 'game-app::shadow game-row[letters="%s"]::shadow ' % word
#             tile = row + "game-tile:nth-of-type(%s)"
#             self.wait_for_element(tile % "5" + '::shadow [data-state*="e"]')
#             letter_status = []
#             for i in range(1, 6):
#                 letter_eval = self.get_attribute(tile % str(i), "evaluation")
#                 letter_status.append(letter_eval)
#             if letter_status.count("correct") == 5:
#                 success = True
#                 break
#             self.word_list.remove(word)
#             self.modify_word_list(word, letter_status)

#         self.save_screenshot_to_logs()
#         print('\nWord: "%s"\nAttempts: %s' % (word.upper(), total_attempts))
#         if not success:
#             self.fail("Unable to solve for the correct word in 6 attempts!")
#         self.sleep(3)

    
    
        



