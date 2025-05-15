import csv
import re
import unittest

def is_english(text):
    # Enhanced detection using common English sentence starters
    return bool(re.search(r'^(I|You|He|She|It|We|They|The|This|That|There|Here|If|When|Why|How|What|Where)', text.strip(), re.I))

def process_entry(entry_lines):
    if not entry_lines:
        return None
        
    header = entry_lines[0].strip()
    # Fixed regex to handle numbered entries and hyphenated translations
    match = re.match(r'^(\d+)-?\s*([^-]+?)\s*-\s*([^-]+?)(?=\s*\d+-|\s*|$)', header)
    if not match:
        return None

    num, spanish, remainder = match.groups()
    
    # Extract English translation using lookahead for Spanish example
    trans_match = re.match(r'^(.+?)(?=\s*[A-ZÀ-Ú])', remainder)
    if trans_match:
        english_trans = trans_match.group(1).strip()
        spanish_ex_start = remainder[len(english_trans):].strip()
    else:
        english_trans = remainder.strip()
        spanish_ex_start = ''

    # Add validation for critical fields
    if not all([num, spanish, english_trans]):
        return None

    spanish_ex_lines = []
    english_ex_lines = []
    current_spanish = spanish_ex_start.strip()
    
    # Process remaining lines with improved language detection
    in_spanish = bool(current_spanish)
    for line in entry_lines[1:]:
        line = line.strip()
        if not line:
            continue
            
        if in_spanish:
            # Check if line starts a new entry or is English
            if re.match(r'^\d+-', line) or is_english(line):
                in_spanish = False
                if not re.match(r'^\d+-', line):
                    english_ex_lines.append(line)
            else:
                current_spanish += ' ' + line
        else:
            if re.match(r'^\d+-', line):
                break  # Next entry found
            english_ex_lines.append(line)
    
    if current_spanish:
        spanish_ex_lines.append(current_spanish)
    
    # Final cleaning
    spanish_ex = re.sub(r'\s+', ' ', ' '.join(spanish_ex_lines)).strip()
    english_ex = re.sub(r'\s+', ' ', ' '.join(english_ex_lines)).strip()
    
    return [
        num.strip(),
        spanish.strip(),
        english_trans.strip(),
        spanish_ex,
        english_ex
    ]

def reformat_word_list(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as f:
        entries = []
        current_entry = []
        
        for line in f:
            line = line.strip()
            if re.match(r'^\d+-', line):
                if current_entry:
                    entries.append(current_entry)
                current_entry = [line]
            elif current_entry:
                current_entry.append(line)
        
        if current_entry:
            entries.append(current_entry)

    with open(output_file, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        writer.writerow(['Number', 'Spanish Word', 'English Translation', 'Spanish Example', 'English Example'])
        
        for entry in entries:
            processed = process_entry(entry)
            if processed:
                writer.writerow(processed)

# Add this test class at the bottom of your file
class TestWordParser(unittest.TestCase):
    def test_entry_5(self):
        input_lines = [
            "5- La – The (Feminine) Andrea es la estudiante más inteligente y",
            "además la mejor hermana.",
            "Andrea is the smartest student as well as the best sister."
        ]
        expected = (
            "5", 
            "La",
            "The (Feminine)",
            "Andrea es la estudiante más inteligente y además la mejor hermana",
            "Andrea is the smartest student as well as the best sister."
        )
        result = process_entry(input_lines)
        import pdb;pdb.set_trace()
        self.assertEqual(tuple(result), expected)

    def test_entry_10(self):
        input_lines = [
            "10- Lo – The/Him/It (Masculine) Lo echaron a la calle. Creo que no",
            "debieron hacerlo.",
            "They threw him out on the street. I think they shouldn't have done it."
        ]
        expected = (
            "10",
            "Lo",
            "The/Him/It (Masculine)",
            "Lo echaron a la calle. Creo que no debieron hacerlo",
            "They threw him out on the street. I think they shouldn't have done it."
        )
        result = process_entry(input_lines)
        self.assertEqual(tuple(result), expected)

    def test_entry_1949(self):
        input_lines = [
            "1949-Jodido-Fucking Este jodido idiota nos ha dañado los planes de hoy.",
            "This fucking idiot has ruined our plans for today."
        ]
        expected = (
            "1949",
            "Jodido",
            "Fucking",
            "Este jodido idiota nos ha dañado los planes de hoy",
            "This fucking idiot has ruined our plans for today"
        )
        result = process_entry(input_lines)
        self.assertEqual(tuple(result), expected)

    def test_multi_line_spanish(self):
        input_lines = [
            "33- Al – To the/At the Tenemos que ir al gimnasio; ya nos estamos poniendo",
            "gordos.",
            "We have to go to the gym; we're getting fat."
        ]
        expected = (
            "33",
            "Al",
            "To the/At the",
            "Tenemos que ir al gimnasio; ya nos estamos poniendo gordos",
            "We have to go to the gym; we're getting fat"
        )
        result = process_entry(input_lines)
        self.assertEqual(tuple(result), expected)

if __name__ == "__main__":
    unittest.main()
