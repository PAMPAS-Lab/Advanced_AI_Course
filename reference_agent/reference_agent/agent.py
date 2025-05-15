import os
from pathlib import Path
import argparse
from collections import Counter
from docx import Document
from dotenv import load_dotenv
from zhipuai import ZhipuAI
from utils import (
    load_prompt,
    normalize_doc,
    get_reference_titles,
    get_citation_markers,
    load_pdf,
    search_from_arxiv
)


class Agent:
    def __init__(self, model, prompt, doc, ref):
        self.model = model
        self.prompt = load_prompt(prompt)
        self.doc = normalize_doc(Document(doc))
        self.ref = ref

    def call_model(self, model, prompt):
        client = ZhipuAI(api_key=os.environ.get("ZHIPUAI_API_KEY"))
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            stream=False
        )
        return response.choices[0].message.content

    def verify_citations_referenced(self):
        print("第1步: 核查引文数量及引用情况")
        titles = get_reference_titles(self.doc)
        print(f"文献列表共有{len(titles)}篇参考文献")

        citations = []
        citations_to_text = get_citation_markers(self.doc)
        for citation, citation_text in citations_to_text:
            citations.extend(citation)

        missed_citations = list(set(range(1, len(titles)+1)) - set(citations))
        for citation in missed_citations:
            print(f"文献[{citation}]没有被引用")

        counter = Counter(citations)
        for citation, count in counter.items():
            if count > 1:
                print(f"文献[{citation}]的引用超过1次,共引用了{count}次")

    def download_literatures(self):
        print("第2步: 开始下载文献:")
        titles = get_reference_titles(self.doc)
        for i, title in enumerate(titles):
            flag = False
            for result in search_from_arxiv(title):
                if result.title.lower() == title.lower():
                    flag = True
                    print(result.title)
                    result.download_pdf(dirpath="../data/references", filename=f"{i+1}.pdf")
                    break
            if not flag:
                print(f"未在arxiv上找到文献:{title}")

    def verify_citation_sentences(self):
        print("第3步: 核查引文与文献的对应关系")
        bad_count = 0
        ref_names = [int(file.stem) for file in Path(self.ref).iterdir() if file.is_file()]
        citations_to_text = get_citation_markers(self.doc)
        for citation, text in citations_to_text:
            if set(citation) - set(ref_names):
                print(f"因为{citation}未在arxiv上检索到,跳过引文<{text}>的检查")
                continue
            else:
                reference_paths = [Path(self.ref) / f"{index}.pdf" for index in citation]
            references = load_pdf(reference_paths)
            prompt = self.prompt.format(text, references)
            response = self.call_model(self.model, prompt)
            if "<是>" == response:
                print(f"引文{citation}核查无误")
                continue
            elif "否" in response:
                bad_count += 1
                print(f"引文{citation}检测错误: {response}")
        print("------------分割线-------------")
        print(f"总共有{bad_count}篇文献引用被检测为错误")


if __name__ == "__main__":
    load_dotenv()

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, required=True)
    parser.add_argument("--prompt", type=str, required=True)
    parser.add_argument("--doc", type=str, required=True)
    parser.add_argument("--ref", type=str, required=True)
    args = parser.parse_args()


    agent = Agent(args.model, args.prompt, args.doc, args.ref)
    agent.verify_citations_referenced()
    print("------------分割线-------------")
    agent.download_literatures()
    print("------------分割线-------------")
    agent.verify_citation_sentences()






