import csv
import re


def process_entry(input_lines):
    num_lines = len(input_lines)
    print('num_lines:', num_lines)

    small_dash_split = input_lines[0].split('-')
    number_before_dash = small_dash_split[0]

    print('number_before_dash:', number_before_dash)

    big_dash_split = small_dash_split[1].split('–')
    spanish_word = big_dash_split[0].strip()
    print('spanish_word:', spanish_word)

    first_line_after_big_dash = big_dash_split[1]
    print('first_line_after_big_dash:', first_line_after_big_dash)

    english_translation = input_lines[-1]
    print('english_translation:', english_translation)

    if num_lines == 2:
        spanish_lines_joined_with_english_translation = first_line_after_big_dash
        # spanish_lines_joined_with_english_translation = ''.join(input_lines[1])
        print('spanish_lines_joined_with_english_translation', spanish_lines_joined_with_english_translation)
    elif num_lines == 3:
        # spanish_lines_joined_with_english_translation = ''.join(input_lines[1])
        spanish_lines_joined_with_english_translation = first_line_after_big_dash + ' ' + input_lines[1]
        print('spanish_lines_joined_with_english_translation', spanish_lines_joined_with_english_translation)
    else:
        print('input_lines:', input_lines)
        import pdb;pdb.set_trace()
    

    first_line_split_by_words = first_line_after_big_dash.strip().split(' ')
    print('first_line_split_by_words:', first_line_split_by_words)
    if len(first_line_split_by_words) > 1 and ('(' in first_line_split_by_words[1] or '/' in first_line_split_by_words[1]):
        english_word = first_line_split_by_words[0] + ' ' + first_line_split_by_words[1]
    else:
        english_word = first_line_split_by_words[0]
    print('english_word', english_word)

    # Remove english word and leading space using substring
    spanish_lines_joined_with_english_translation = spanish_lines_joined_with_english_translation.strip()[len(english_word):].strip()
    print('spanish_lines_joined_with_english_translation after cleaning:', spanish_lines_joined_with_english_translation)

    print()
    return (
        number_before_dash,
        spanish_word,
        english_word,
        spanish_lines_joined_with_english_translation,
        english_translation
    )


def print_result(result, expected):
    print('result')
    print(result)
    print('expected')
    print(expected)
    print('result == expected:', result == expected)


input_lines = [
    "5- La – The (Feminine) Andrea es la estudiante más inteligente y",
    "además la mejor hermana.",
    "Andrea is the smartest student as well as the best sister."
]
expected = (
    "5", 
    "La",
    "The (Feminine)",
    "Andrea es la estudiante más inteligente y además la mejor hermana.",
    "Andrea is the smartest student as well as the best sister."
)
result = process_entry(input_lines)
print_result(result, expected)



input_lines = [
    "10- Lo – The/Him/It (Masculine) Lo echaron a la calle. Creo que no",
    "debieron hacerlo.",
    "They threw him out on the street. I think they shouldn't have done it."
]
expected = (
    "10",
    "Lo",
    "The/Him/It (Masculine)",
    "Lo echaron a la calle. Creo que no debieron hacerlo.",
    "They threw him out on the street. I think they shouldn't have done it."
)
result = process_entry(input_lines)
print_result(result, expected)

input_lines = [
    "1949-Jodido–Fucking Este jodido idiota nos ha dañado los planes de hoy.",
    "This fucking idiot has ruined our plans for today."
]
expected = (
    "1949",
    "Jodido",
    "Fucking",
    "Este jodido idiota nos ha dañado los planes de hoy.",
    "This fucking idiot has ruined our plans for today."
)
result = process_entry(input_lines)
print_result(result, expected)

input_lines = [
    "33- Al – To the/At the Tenemos que ir al gimnasio; ya nos estamos poniendo",
    "gordos.",
    "We have to go to the gym; we're getting fat."
]
expected = (
    "33",
    "Al",
    "To the/At the",
    "Tenemos que ir al gimnasio; ya nos estamos poniendo gordos.",
    "We have to go to the gym; we're getting fat."
)
result = process_entry(input_lines)
print_result(result, expected)


# sys.exit()

# Modified entry detection logic
def process_file(input_file):
    entries = []
    current_entry = []
    
    for line in input_file:
        line = line.strip()
        # Match numbers followed by any type of dash (regular, en-dash, em-dash)
        if re.match(r'^\d+[-\–—]', line):
            if current_entry:
                entries.append(current_entry)
            current_entry = [line]
        elif current_entry:
            current_entry.append(line)
    
    if current_entry:
        entries.append(current_entry)
    return entries

# Process 2000 words file
with open('2000_words_in_context.txt', 'r', encoding='utf-8') as f:
    # entries = []
    # current_entry = []
    
    # for line in f:
    #     line = line.strip()
    #     if re.match(r'^\d+-', line):
    #         if current_entry:
    #             entries.append(current_entry)
    #         current_entry = [line]
    #     elif current_entry:
    #         current_entry.append(line)
    
    # if current_entry:
    #     entries.append(current_entry)

    entries = process_file(f)

with open('2000_words.csv', 'w', encoding='utf-8', newline='') as f:
    writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
    writer.writerow(['Number', 'Spanish Word', 'English Translation', 'Spanish Example', 'English Example'])
    
    for entry in entries:
        processed = process_entry(entry)
        if processed:
            writer.writerow(processed)
