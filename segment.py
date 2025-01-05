#!/usr/bin/env python3

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import litellm
import jsonlines
import re
import sys
from pathlib import Path
from dump import dump
from dotenv import load_dotenv

load_dotenv()

SYSTEM="""
The user will share the transcript of a podcast episode.
It's an "Ask Me Anything" episode from Sean Carroll's Mindscape podcast.
He reads a series of questions from listeners and then answers them.

The questions often start like:
- Raul says why is the sky blue?
- AbacusPowerUser asks why do apples fall from trees?
- Jane's question is given the current understanding of dark energy and its apparent acceleration of the universe's expansion, how might this affect the long-term fate of the universe, and what are the implications for the various proposed scenarios such as the Big Freeze, Big Rip, or Big Crunch? Additionally, how does this relate to the concept of cosmic inflation in
the early universe, and what challenges does it present for reconciling quantum mechanics with general relativity in a unified theory of quantum gravity?
- etc

Find all the sentences in the transcript which denote the start of a new question.
Return *every* such sentence.
Return questions exactly as they appear in the transcript, with all the same punctuation, spacing, etc.
Return one question per line in a bulleted list like this:

- Raul says why is the sky blue?
- AbacusPowerUser asks why do apples fall from trees?
- Jane's question is given the current understanding of dark energy and its apparent acceleration of the universe's expansion, how might this affect the long-term fate of the universe, and what are the implications for the various proposed scenarios such as the Big Freeze, Big Rip, or Big Crunch? Additionally, how does this relate to the concept of cosmic inflation in
the early universe, and what challenges does it present for reconciling quantum mechanics with general relativity in a unified theory of quantum gravity?
""".strip()

def find_questions(words, start, end):

    words = words[start:end]

    text = pretty(words)

    model = "deepseek/deepseek-chat"

    messages=[
        dict(role="system", content=SYSTEM),
        dict(role="user", content=text),
    ]

    comp = litellm.completion(model=model, messages=messages, temperature=0)
    res = comp.choices[0].message.content
    print(res)

    # Parse bullet points and verify they exist in text
    questions = []
    for line in res.splitlines():
        if line.startswith("- "):
            question = line[2:].strip()

            full_words_text = "".join(w["text"] for w in words)
            offset = full_words_text.find(question)
            if offset == -1:
                question = question.split()[:10]
                question = ' '.join(question)
                offset = full_words_text.find(question)
            if offset == -1:
                # Try case-insensitive search
                offset = full_words_text.lower().find(question.lower())
                if offset == -1:
                    # Try removing common punctuation
                    clean_text = re.sub(r"[.,;:!?]", "", full_words_text.lower())
                    clean_question = re.sub(r"[.,;:!?]", "", question.lower())
                    offset = clean_text.find(clean_question)
            present = offset != -1

            word_index = None
            if present:
                char_count = 0
                for i, w_obj in enumerate(words):
                    next_count = char_count + len(w_obj["text"])
                    if offset < next_count:
                        word_index = i
                        break
                    char_count = next_count

            print()
            print("Question:", present)
            print(question)
            print("word_index:", word_index)
            #dump(words[word_index:word_index+3])
            questions.append(word_index+start)

    return questions


def align_transcription(input_file, output_file):
    with jsonlines.open(input_file) as reader:
        words = [obj for obj in reader]

    questions = []
    chunk_size = 5000
    start_index = 0
    while start_index < len(words):
        end_index = min(start_index+chunk_size, len(words))
        chunk_questions = find_questions(words, start_index, end_index)
        questions.extend(chunk_questions)
        start_index += chunk_size

    final_questions = []
    questions = sorted(questions)
    questions.reverse()

    # Process questions in chunks of 100 words before and after
    while questions:
        dump(questions)
        q_index = questions.pop()
        start = q_index
        if questions:
            end = questions[-1]
        else:
            end = len(words)

        print()
        print(pretty(words[start:start+20]))

        # Get verification results for this question
        verified = find_questions(words, start, end)

        if len(verified) == 1:
            if verified == q_index:
                # Single verified question near our original index
                final_questions.append(q_index)
            else:
                assert False
        elif len(verified) > 1:
            # Multiple questions found - add them all back to be processed
            questions.extend(verified)
            questions = sorted(set(questions))
            questions.reverse()


def pretty(merged):
    full_text = ""
    for obj in merged:
        full_text += obj.get("text", "")

    return full_text
    # Print word-wrapped text
    import textwrap
    return "\n".join(textwrap.wrap(full_text, width=80))

def main():
    if len(sys.argv) != 2:
        print("Usage: python segment.py file.jsonl>")
        sys.exit(1)

    input_file = sys.argv[1]
    if not Path(input_file).exists():
        print(f"Error: File {input_file} not found")
        sys.exit(1)

    output_file = Path(input_file).stem + "_segments.jsonl"
    align_transcription(input_file, output_file)
    print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()
