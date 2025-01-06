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

Sometimes Sean will group similar questions together, and read a few of them before giving a combined answer that addresses all the questions in the group.
Treat such grouped questions as a single "grouped set of questions".

The questions often start like these examples:

Raul says why is the sky blue? ... AbacusPowerUser asks why do apples fall from trees? ... Jane's question is given the current understanding of dark energy and its apparent acceleration of the universe's expansion, how might this affect the long-term fate of the universe, and what are the implications for the various proposed scenarios such as the Big Freeze, Big Rip, or Big Crunch? Additionally, how does this relate to the concept of cosmic inflation in the early universe, and what challenges does it present for reconciling quantum mechanics with general relativity in a unified theory of quantum gravity? ... I'm going to group 2 questions together. Anonymous asks why is water wet, and SuperStar10k wants to know why 2 hydrogen and 1 oxygen form water.

Find all the sentences in the transcript which denote the start of a new question or grouped set of questions.
Return *every* such sentence.
Return questions exactly as they appear in the transcript, with all the same punctuation, spacing, etc.
Return one question per line in a bulleted list like this:

- Raul says why is the sky blue?
- AbacusPowerUser asks why do apples fall from trees?
- Jane's question is given the current understanding of dark energy and its apparent acceleration of the universe's expansion, how might this affect the long-term fate of the universe, and what are the implications for the various proposed scenarios such as the Big Freeze, Big Rip, or Big Crunch? Additionally, how does this relate to the concept of cosmic inflation in
the early universe, and what challenges does it present for reconciling quantum mechanics with general relativity in a unified theory of quantum gravity?
- I'm going to group 2 questions together. Anonymous asks why is water wet, and SuperStar10k wants to know why 2 hydrogen and 1 oxygen form water.

ONLY RETURN ONE ENTRY FOR A "GROUPED SET OF QUESTIONS", DO NOT BREAK THEM APART.

EVERY ENTRY IN THE LIST MUST BE AN EXACT STRING OF CHARACTERS FROM THE TRANSCRIPT!
All words, punctuation, spacing must be EXACTLY preserved.
Do not skip, re-order or summarize.
""".strip()


@lox.thread(1)
def find_questions(words, start, end):

    words = words[start:end]

    duration = words[-1]['end'] - words[0]['start']

    print()
    print()
    print()
    dump(start, end, duration)

    text = pretty(words)
    print()
    dump(text)

    model = "deepseek/deepseek-chat"

    messages=[
        dict(role="system", content=SYSTEM),
        dict(role="user", content=text),
    ]

    comp = litellm.completion(model=model, messages=messages, temperature=0)
    res = comp.choices[0].message.content
    print()
    dump(res)

    # Parse bullet points and verify they exist in text
    question_dict = {}
    unfound_questions = []
    for line in res.splitlines():
        if line.startswith("- "):
            raw_question = question = line[2:].strip()

            word_index = find_question_in_words(question, words)
            if not word_index:
                #    print("X"*70)
                unfound_questions.append(question)
                continue

            print()
            print("question:", question[:50])
            print("start word_index:", word_index)
            print(pretty(words[word_index:word_index+10]))
            #dump(words[word_index:word_index+3])
            word_index+= start
            question_dict[word_index] = raw_question

    if unfound_questions:
        print("\nUnfound questions:")
        for q in unfound_questions:
            print(f"- {q}")
        print()

    return question_dict

def find_question_in_words(question, words):

    question = question.strip().lower()
    num_words = len(words)

    for i in range(num_words):
        text = "".join(w["text"] for w in words[i:]).strip().lower()
        if text.startswith(question):
            return i

    N=10
    question = question.split()
    if len(question) <= N:
        return
    question = ' '.join(question[:N])

    for i in range(num_words):
        text = "".join(w["text"] for w in words[i:]).strip().lower()
        if text.startswith(question):
            return i


    from Levenshtein import distance as levenshtein_distance
    
    for i in range(num_words):
        text = "".join(w["text"] for w in words[i:]).strip().lower()
        text = text[:len(question)]
        
        if levenshtein_distance(question, text) < 10:
            return i


def segment(input_file, output_file, text_file):
    dump(input_file)

    with jsonlines.open(input_file) as reader:
        words = [obj for obj in reader]

    # Verify words are sorted by start time
    for i in range(1, len(words)):
        if words[i-1]['start'] > words[i]['start']:
            raise ValueError(f"Words are not sorted by start time at index {i}")

    ###
    words = words[8_500:10_000]

    merged_questions = {}
    chunk_size = 5000
    start_index = 0
    while start_index < len(words):
        end_index = min(start_index+chunk_size, len(words))
        find_questions.scatter(words, start_index, end_index)
        start_index += chunk_size

    for chunk_dict in find_questions.gather(tqdm=True):
        merged_questions.update(chunk_dict)

    final_questions = {}
    questions = merged_questions
    while questions:
        question_indexes = sorted(questions.keys())
        for i,q_index in enumerate(question_indexes):
            start = q_index
            if i < len(question_indexes)-1:
                end = question_indexes[i+1]
            else:
                end = len(words)

            find_questions.scatter(words, start, end)

        found_questions = find_questions.gather(tqdm=True)
        new_questions = dict()
        for q_index,verified_dict in zip(questions, found_questions):
            if len(verified_dict) == 1:
                verified_index = list(verified_dict.keys())[0]
                diff = abs(verified_index - q_index)
                if diff < 15:
                    final_questions[verified_index] = questions[q_index]
                else:
                    dump(diff)
                    assert False, output_file
            elif len(verified_dict) > 1:
                # Multiple questions found - add them all back to be processed
                new_questions.extend(verified_dict.items())

        questions = new_questions


    final_questions = dict(sorted(final_questions.items()))

    with jsonlines.open(output_file, mode='w') as writer, open(text_file, 'w') as txt_writer:
        for i,q_index in enumerate(final_questions.keys()):
            # Find the end of this question (start of next question or end of transcript)
            q_index_end = len(words)-1
            end_time = words[q_index_end]["end"]
            if i < len(final_questions)-1:
                # Get next key from sorted keys list
                next_key = sorted(final_questions.keys())[i+1]
                q_index_end = next_key-1
                end_time = words[q_index_end+1]["start"]

            segment_text = ''.join(w['text'] for w in words[q_index:q_index_end+1])

            if not segment_text.strip():
                continue

            start_time = words[q_index]['start']

            if end_time - start_time < 1:
                continue

            writer.write({
                'start': start_time,
                'end': end_time,
                'text': segment_text,
                'question_index': q_index,
                'llm_found_question': final_questions[q_index]
            })

            # Write word-wrapped text to output file
            import textwrap
            wrapped_text = "\n".join(textwrap.wrap(segment_text, width=80))

            txt_writer.write(f"=====\nQuestion: {final_questions[q_index]}\n\n{wrapped_text}\n\n")


def pretty(merged):
    full_text = ""
    for obj in merged:
        full_text += obj.get("text", "")

    return full_text
    # Print word-wrapped text
    import textwrap
    return "\n".join(textwrap.wrap(full_text, width=80))

def main():
    import argparse

    parser = argparse.ArgumentParser(description='Segment podcast transcripts into questions')
    parser.add_argument('files', nargs='+', help='Input JSONL files to process')
    parser.add_argument('--force', action='store_true', help='Overwrite existing output files')
    args = parser.parse_args()

    for input_file in args.files:
        if not Path(input_file).exists():
            print(f"Error: File {input_file} not found")
            continue

        base_path = Path(input_file).with_suffix("")
        input_path = base_path.with_suffix('.punct.jsonl')
        output_path = base_path.with_suffix(".segments.jsonl")
        text_path = base_path.with_suffix(".segments.txt")

        if output_path.exists() and not args.force:
            print(f"Skipping {input_path} - output already exists at {output_path}")
            print("Use --force to overwrite existing files")
            continue

        segment(input_path, output_path, text_path)
        print(f"Saved to {output_path}")
        print(f"Text segments saved to {text_path}")

if __name__ == "__main__":
    main()
