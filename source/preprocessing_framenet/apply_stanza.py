import argparse
import re
from pathlib import Path

import pandas as pd
import stanza
import tokenizations
from tqdm import tqdm

from sfidml.utils.data_utils import read_jsonl, write_jsonl


def make_alignments(text, new_text):
    alignment_dict = {}
    alignments = tokenizations.get_alignments(text, new_text)[0]
    for i, new in enumerate(alignments + [[]]):
        if len(new) != 0:
            alignment_dict[i] = new[0]
        else:
            if i - 1 in alignment_dict:
                alignment_dict[i] = alignment_dict[i - 1]
            else:
                alignment_dict[i] = 0
    return alignment_dict


def make_word_list(doc):
    word_list, count, word_count = [], 0, 0
    for sent_id, sent in enumerate(doc.sentences):
        child = {}
        for word in sent.words:
            if word.head not in child:
                child[word.head] = [word.id]
            else:
                child[word.head].append(word.id)

        for word in sent.words:
            word_dict = word.to_dict()
            word_dict.update(
                {"id": count, "sent_id": sent_id, "word_id": int(word.id) - 1}
            )
            if word.head != 0:
                word_dict.update(
                    {
                        "head": word.head - 1 + word_count,
                        "head_text": sent.words[word.head - 1].text,
                    }
                )
            else:
                word_dict.update({"head": -1, "head_text": "[ROOT]"})
            if word.id in child:
                word_dict.update(
                    {
                        "children": [
                            i - 1 + word_count for i in child[word.id]
                        ],
                    }
                )
            else:
                word_dict.update({"children": []})
            word_list.append(word_dict)
            count += 1
        word_count += len(sent.words)
    return word_list


def find_widx_head(word_list, target_widx):
    target_widx_head = []
    for word_dict in word_list:
        if word_dict["deprel"] == "root":
            if target_widx_head == []:
                target_widx_head = find_target_head(
                    word_dict, word_list, target_widx, []
                )
    return target_widx_head[0]


def find_target_head(node, word_list, target_widx, new_target_widx):
    b, e = target_widx
    if new_target_widx == []:
        if node["deprel"] == "root":
            if b <= int(node["id"]) <= e:
                new_target_widx.append([b, e, int(node["id"])])

        for child_id in [word_list[c]["id"] for c in node["children"]]:
            if b <= int(child_id) <= e:
                new_target_widx.append([b, e, int(child_id)])

        for child in [word_list[c] for c in node["children"]]:
            find_target_head(child, word_list, target_widx, new_target_widx)
    return new_target_widx


def make_verb(lu_name, nlp):
    verb = re.sub("[\[|\(].+[\)|\]]", "", lu_name)[:-2].strip()
    if not re.fullmatch("[a-z][a-z-]*", verb):
        doc = nlp(verb)
        head = [
            word.id - 1
            for sentences in doc.sentences
            for word in sentences.words
            if word.deprel == "root"
        ][0]
        verb = [
            word.text for sentences in doc.sentences for word in sentences.words
        ][head]
    return verb


def main(args):
    args.output_dir.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame(read_jsonl(args.input_file))
    df = df[df["lu_name"].apply(lambda x: x.split(".")[-1]) == "v"].reset_index(
        drop=True
    )
    df = df.reset_index(drop=True)

    nlp = stanza.Pipeline("en")

    ex_list, ex_list2 = [], []
    for df_dict in tqdm(df.to_dict("records")):
        text, target, lu_name = (
            df_dict["text"],
            df_dict["target"][0],
            df_dict["lu_name"],
        )

        text_norm = (
            " ".join((re.sub("\s", " ", text).rstrip() + " ").split()) + " "
        )
        doc = nlp(text_norm)
        text_widx = (
            " ".join([w.text for s in doc.sentences for w in s.words]) + " "
        )

        a1 = make_alignments(text, text_norm)
        a2 = make_alignments(text_norm, text_widx)
        a3 = make_alignments(list(text_widx), text_widx.split())

        target_widx = [a3[a2[a1[t]]] for t in target]

        word_list = make_word_list(doc)
        target_widx_head = find_widx_head(word_list, target_widx)

        verb = make_verb(lu_name, nlp)

        df_dict.update(
            {
                "text_widx": text_widx,
                "target_widx": target_widx_head,
                "verb": verb,
            }
        )
        ex_list.append(df_dict)
        ex_list2.append({"ex_idx": df_dict["ex_idx"], "word_list": word_list})

    df_ex = pd.DataFrame(ex_list)
    write_jsonl(df_ex.to_dict("records"), args.output_dir / "exemplars.jsonl")

    df_ex2 = pd.DataFrame(ex_list2)
    write_jsonl(df_ex2.to_dict("records"), args.output_dir / "word_list.jsonl")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_file", type=Path, required=True)
    parser.add_argument("--output_dir", type=Path, required=True)
    args = parser.parse_args()
    print(args)
    main(args)
