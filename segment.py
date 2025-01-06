#!/usr/bin/env python3

import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import lox
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

@lox.thread(10)
def find_questions(words, start, end):
    dump(start, end)

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
                # Try fuzzy matching with edit distance
                from Levenshtein import distance as levenshtein_distance

                # Split text into overlapping chunks of question length
                chunk_size = len(question)
                min_distance = float('inf')
                best_offset = -1

                for i in range(len(full_words_text) - chunk_size + 1):
                    chunk = full_words_text[i:i+chunk_size]
                    dist = levenshtein_distance(question.lower(), chunk.lower())
                    if dist < min_distance and dist <= 20:
                        min_distance = dist
                        best_offset = i
                        if dist == 0:
                            break

                offset = best_offset
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
            print(pretty(words[word_index:word_index+10]))
            print(question)
            #dump(words[word_index:word_index+3])
            word_index+= start
            print("word_index:", word_index)
            questions.append(word_index)

    return questions


def align_transcription(input_file, output_file):
    with jsonlines.open(input_file) as reader:
        words = [obj for obj in reader]

    questions = []
    chunk_size = 5000
    start_index = 0
    while start_index < len(words):
        end_index = min(start_index+chunk_size, len(words))
        find_questions.scatter(words, start_index, end_index)
        start_index += chunk_size

    for chunk_questions in find_questions.gather(tqdm=True):
        questions.extend(chunk_questions)

    final_questions = []
    questions = sorted(questions)
    questions.reverse()

    while questions:
        questions = sorted(set(questions))

        for i,q_index in enumerate(questions):
            start = q_index
            if i < len(questions)-1:
                end = questions[i+1]
            else:
                end = len(words)

            find_questions.scatter(words, start, end)

        found_questions = find_questions.gather(tqdm=True)
        new_questions = []
        for q_index,verified in zip(questions, found_questions):
            if len(verified) == 1:
                if abs(verified[0] - q_index) < 3:
                    final_questions.append(q_index)
                else:
                    assert False
            elif len(verified) > 1:
                # Multiple questions found - add them all back to be processed
                new_questions.extend(verified)

        questions = new_questions

    final_questions = sorted(final_questions)

    # Write final questions to output file
    with jsonlines.open(output_file, mode='w') as writer:
        for i,q_index in enumerate(final_questions):
            # Find the end of this question (start of next question or end of transcript)
            q_index_end = len(words)-1
            end_time = words[q_index_end]["end"]
            if i < len(final_questions)-1:
                q_index_end = final_questions[i+1]-1
                end_time = words[q_index_end+1]["start"]

            writer.write({
                'start': words[q_index]['start'],
                'end': end_time,
                'text': ''.join(w['text'] for w in words[q_index:q_index_end+1]),
                'question_index': q_index
            })



def pretty(merged):
    full_text = ""
    for obj in merged:
        full_text += obj.get("text", "")

    return full_text
    # Print word-wrapped text
    import textwrap
    return "\n".join(textwrap.wrap(full_text, width=80))

def main():
    if len(sys.argv) < 2:
        print("Usage: python segment.py file1.jsonl [file2.jsonl ...]")
        sys.exit(1)

    for input_file in sys.argv[1:]:
        if not Path(input_file).exists():
            print(f"Error: File {input_file} not found")
            continue

        output_file = Path(input_file).stem + "_segments.jsonl"
        align_transcription(input_file, output_file)
        print(f"Saved to {output_file}")

if __name__ == "__main__":
    main()
